import json
import operator
from pathlib import Path
from typing import Annotated, TypedDict

from fastapi import HTTPException
from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from ..clients.openai_client import OpenAIClient
from ..repositories.plan_repository import PlanRepository
from ..repositories.task_repository import TaskRepository
from ..schemas.agent import AgentGenerateRequest, BreakdownResponse, Subtopic, TaskDraft
from ..schemas.study_task import StudyTaskCreate

_TEMPLATES = Path(__file__).parent.parent / "templates"
_BREAKDOWN_TEMPLATE = (_TEMPLATES / "breakdown.txt").read_text(encoding="utf-8")
_GENERATE_TEMPLATE = (_TEMPLATES / "generate_agent_tasks.txt").read_text(encoding="utf-8")


class AgentState(TypedDict):
    plan_id: int
    constraints: str
    hours_per_week: float
    pending_subtopics: list[dict]
    current_subtopic: dict | None
    current_tasks_draft: list[dict]
    final_tasks: Annotated[list[dict], operator.add]
    feedback_loop: str | None
    retry_count: int
    warnings: Annotated[list[str], operator.add]


class AgentService:
    def __init__(self, db: Session, openai_client: OpenAIClient) -> None:
        self.db = db
        self.openai_client = openai_client
        self.plan_repo = PlanRepository(db)
        self.task_repo = TaskRepository(db)
        self.graph = self._build_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def perform_breakdown(self, plan_id: int) -> BreakdownResponse:
        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        prompt = _BREAKDOWN_TEMPLATE.format(
            goal=plan.goal,
            constraints=plan.constraints or "None",
            hours_per_week=plan.hours_per_week,
        )

        subtopics = self.openai_client.generate_tasks(prompt, list[Subtopic])
        return BreakdownResponse(subtopics=subtopics)

    def execute_planning_graph(
        self, plan_id: int, request: AgentGenerateRequest
    ):
        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if not request.approved_subtopics:
            raise HTTPException(
                status_code=422,
                detail="At least one approved subtopic is required",
            )

        initial_state: AgentState = {
            "plan_id": plan_id,
            "constraints": plan.constraints or "",
            "hours_per_week": plan.hours_per_week or 0,
            "pending_subtopics": [
                {"name": s.name, "description": s.description, "suggested_hours": s.suggested_hours}
                for s in request.approved_subtopics
            ],
            "current_subtopic": None,
            "current_tasks_draft": [],
            "final_tasks": [],
            "feedback_loop": None,
            "retry_count": 0,
            "warnings": [],
        }

        total_subtopics = len(initial_state["pending_subtopics"])
        graph_stream = self.graph.stream(initial_state, stream_mode="updates", config={"recursion_limit": 200})
        return self._sse_adapter(graph_stream, total_subtopics)

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(AgentState)

        builder.add_node("prepare_next_subtopic", self._prepare_next_subtopic)
        builder.add_node("generate_tasks", self._generate_tasks)
        builder.add_node("validate_constraints", self._validate_constraints)
        builder.add_node("save_to_database_node", self._save_to_database_node)

        builder.set_entry_point("prepare_next_subtopic")
        builder.add_edge("prepare_next_subtopic", "generate_tasks")
        builder.add_edge("generate_tasks", "validate_constraints")

        builder.add_conditional_edges(
            "validate_constraints",
            self._route_validation,
            {
                "generate_tasks": "generate_tasks",
                "prepare_next_subtopic": "prepare_next_subtopic",
                "save_to_database_node": "save_to_database_node",
            },
        )

        builder.add_edge("save_to_database_node", END)

        return builder.compile()

    # ------------------------------------------------------------------
    # Graph nodes
    # ------------------------------------------------------------------

    def _prepare_next_subtopic(self, state: AgentState) -> dict:
        pending = state["pending_subtopics"]
        if not pending:
            return {"current_subtopic": None}

        next_subtopic = pending[0]
        remaining = pending[1:]

        return {
            "current_subtopic": next_subtopic,
            "pending_subtopics": remaining,
            "current_tasks_draft": [],
            "feedback_loop": None,
            "retry_count": 0,
        }

    def _generate_tasks(self, state: AgentState) -> dict:
        subtopic = state["current_subtopic"]
        if not subtopic:
            return {"current_tasks_draft": []}

        feedback = state.get("feedback_loop")
        constraints = state.get("constraints", "")
        hours_per_week = state.get("hours_per_week", 0)

        if feedback:
            feedback_section = (
                f"Previous generation was rejected. Feedback: {feedback}\n"
                f"Please adjust the tasks to address this feedback."
            )
        else:
            feedback_section = ""

        prompt = _GENERATE_TEMPLATE.format(
            subtopic_name=subtopic["name"],
            subtopic_description=subtopic["description"],
            suggested_hours=subtopic["suggested_hours"],
            constraints=constraints or "None",
            hours_per_week=hours_per_week,
            feedback_section=feedback_section,
        )

        tasks = self.openai_client.generate_tasks(prompt, list[TaskDraft])

        return {
            "current_tasks_draft": [
                {
                    "title": t.title.strip(),
                    "estimated_hours": float(t.estimated_hours),
                    "subtopic": subtopic["name"],
                }
                for t in tasks
            ]
        }

    def _validate_constraints(self, state: AgentState) -> dict:
        tasks = state["current_tasks_draft"]
        subtopic = state["current_subtopic"]
        hours_per_week = state["hours_per_week"]
        retry_count = state["retry_count"]
        final_tasks = state["final_tasks"]

        if not tasks:
            return {
                "feedback_loop": None,
                "final_tasks": [],
                "warnings": [
                    f"No tasks generated for '{subtopic['name'] if subtopic else 'unknown'}'"
                ],
            }

        subtopic_name = subtopic["name"]

        subtopic_total = sum(t["estimated_hours"] for t in tasks)
        suggested = subtopic["suggested_hours"]

        subtopic_ok = True
        if suggested > 0:
            tolerance = suggested * 0.2
            subtopic_ok = abs(subtopic_total - suggested) <= tolerance

        existing_global = sum(t["estimated_hours"] for t in final_tasks)
        new_global = existing_global + subtopic_total

        global_ok = True
        if hours_per_week > 0:
            global_ok = new_global <= hours_per_week * 1.2

        if subtopic_ok and global_ok:
            return {
                "feedback_loop": None,
                "final_tasks": tasks,
                "warnings": [],
            }

        if retry_count >= 3:
            return {
                "feedback_loop": None,
                "final_tasks": tasks,
                "warnings": [
                    f"Max retries (3) exceeded for '{subtopic_name}'. Tasks saved as-is."
                ],
            }

        parts = []
        if not subtopic_ok:
            parts.append(
                f"Tasks total {subtopic_total:.1f}h but suggested is {suggested:.1f}h "
                f"(±20%). Adjust estimated hours to fit within {suggested * 0.8:.1f}h–{suggested * 1.2:.1f}h."
            )
        if not global_ok:
            parts.append(
                f"Global total would be {new_global:.1f}h which exceeds "
                f"the plan limit of {hours_per_week:.1f}h/week (+20%). "
                f"Reduce to stay under {hours_per_week * 1.2:.1f}h."
            )

        return {
            "feedback_loop": " ".join(parts),
            "retry_count": retry_count + 1,
            "warnings": [],
        }

    def _save_to_database_node(self, state: AgentState) -> dict:
        tasks = state["final_tasks"]
        plan_id = state["plan_id"]

        for task in tasks:
            self.task_repo.create(
                plan_id,
                StudyTaskCreate(
                    title=task["title"],
                    estimated_hours=task["estimated_hours"],
                    subtopic=task.get("subtopic", "general"),
                ),
            )

        return {}

    # ------------------------------------------------------------------
    # Router
    # ------------------------------------------------------------------

    def _route_validation(self, state: AgentState) -> str:
        if state.get("feedback_loop"):
            return "generate_tasks"
        if state.get("pending_subtopics"):
            return "prepare_next_subtopic"
        return "save_to_database_node"

    # ------------------------------------------------------------------
    # SSE adapter
    # ------------------------------------------------------------------

    def _sse_adapter(self, graph_stream, total_subtopics: int):
        yield self._format_sse("planning_started", {"subtopic_count": total_subtopics})

        subtopic_index = 0

        try:
            for chunk in graph_stream:
                for node_name, state_update in chunk.items():
                    if node_name == "prepare_next_subtopic":
                        subtopic = state_update.get("current_subtopic")
                        if subtopic:
                            subtopic_index += 1
                            yield self._format_sse(
                                "subtopic_started",
                                {
                                    "subtopic": subtopic["name"],
                                    "index": subtopic_index,
                                    "total": total_subtopics,
                                },
                            )
                    elif node_name == "generate_tasks":
                        tasks = state_update.get("current_tasks_draft", [])
                        yield self._format_sse(
                            "tasks_generated",
                            {"task_count": len(tasks), "tasks": tasks},
                        )
                    elif node_name == "validate_constraints":
                        feedback = state_update.get("feedback_loop")
                        if feedback:
                            yield self._format_sse(
                                "validation_retry", {"feedback": feedback}
                            )
                        warnings = state_update.get("warnings", []) or []
                        for w in warnings:
                            yield self._format_sse("warning", {"message": w})
                    elif node_name == "save_to_database_node":
                        yield self._format_sse("tasks_saved", {"saved": True})

            yield self._format_sse("planning_complete", {"status": "completed"})
        except Exception as exc:
            yield self._format_sse("error", {"message": str(exc)})

    @staticmethod
    def _format_sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"
