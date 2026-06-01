from datetime import date
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..clients.openai_client import OpenAIClient
from ..repositories.plan_repository import PlanRepository
from ..repositories.task_repository import TaskRepository
from ..schemas.study_task import StudyTaskCreate, StudyTaskRead
from ..schemas.task_generation import (
    FailedGeneration,
    GenerateTasksRequest,
    GenerateTasksResponse,
    GeneratedTask,
)

_TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "generate_tasks.txt"


class GenerationService:
    def __init__(self, db: Session, openai_client: OpenAIClient) -> None:
        self.db = db
        self.openai_client = openai_client
        self.plan_repo = PlanRepository(db)
        self.task_repo = TaskRepository(db)

    def generate_tasks(self, plan_id: int, request: GenerateTasksRequest) -> GenerateTasksResponse:
        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.target_date is None:
            raise HTTPException(
                status_code=422,
                detail="Plan must have a target_date to generate tasks. Set a target completion date on the plan first.",
            )

        existing_tasks = self.task_repo.get_by_plan_id(plan_id)

        prompt = self._build_prompt(
            plan.goal,
            plan.hours_per_week,
            plan.target_date,
            existing_tasks,
            request.max_tasks,
        )

        generated = self.openai_client.generate_tasks(prompt, list[GeneratedTask])

        valid_tasks, failed_generations = self._validate_and_persist_tasks(generated, plan_id)

        total_hours = sum(t.estimated_hours for t in valid_tasks)
        hours_match, warning = self._compute_hours_match(total_hours, plan.hours_per_week, valid_tasks)

        return GenerateTasksResponse(
            tasks=valid_tasks,
            total_estimated_hours=total_hours,
            hours_match=hours_match,
            warning=warning,
            failed_generations=failed_generations,
        )

    def _validate_and_persist_tasks(
        self, generated: list, plan_id: int
    ) -> tuple[list[StudyTaskRead], list[FailedGeneration]]:
        valid_tasks: list[StudyTaskRead] = []
        failed_generations: list[FailedGeneration] = []

        for task in generated:
            if not task.title.strip():
                failed_generations.append(
                    FailedGeneration(title="", estimated_hours=0.0, reason="Empty title")
                )
                continue
            if task.estimated_hours <= 0:
                failed_generations.append(
                    FailedGeneration(
                        title=task.title,
                        estimated_hours=task.estimated_hours,
                        reason="Estimated hours must be positive",
                    )
                )
                continue

            try:
                created = self.task_repo.create(
                    plan_id,
                    StudyTaskCreate(
                        title=task.title.strip(),
                        estimated_hours=float(task.estimated_hours),
                        subtopic="general",
                    ),
                )
                valid_tasks.append(StudyTaskRead.model_validate(created))
            except (SQLAlchemyError, ValueError) as e:
                failed_generations.append(
                    FailedGeneration(
                        title=task.title,
                        estimated_hours=task.estimated_hours,
                        reason=f"{type(e).__name__}: {e}",
                    )
                )

        return valid_tasks, failed_generations

    def _compute_hours_match(
        self, total_hours: float, hours_per_week: float, valid_tasks: list
    ) -> tuple[bool, str | None]:
        if hours_per_week <= 0:
            warning = None
            if valid_tasks:
                warning = (
                    f"Plan has hours_per_week={hours_per_week}. "
                    f"Generated {len(valid_tasks)} tasks totaling {total_hours:.1f}h."
                )
            return True, warning

        tolerance = hours_per_week * 0.2
        hours_match = abs(total_hours - hours_per_week) <= tolerance

        warning = None
        if not hours_match and valid_tasks:
            if total_hours > hours_per_week:
                warning = (
                    f"Generated tasks total {total_hours:.1f}h, which exceeds "
                    f"your {hours_per_week}h/week commitment by more than 20%"
                )
            else:
                warning = (
                    f"Generated tasks total {total_hours:.1f}h, which is under "
                    f"your {hours_per_week}h/week commitment by more than 20%"
                )

        return hours_match, warning

    def _build_prompt(
        self,
        goal: str,
        hours_per_week: float,
        target_date: date,
        existing_tasks: list,
        max_tasks: int | None,
    ) -> str:
        template = _TEMPLATE_PATH.read_text(encoding="utf-8")

        if existing_tasks:
            tasks_lines = "\n".join(
                f"  - {t.title} ({t.estimated_hours}h)" for t in existing_tasks
            )
        else:
            tasks_lines = "  (no tasks yet)"

        if max_tasks is not None:
            max_tasks_instruction = f"Generate at most {max_tasks} tasks."
        else:
            max_tasks_instruction = "Generate as many tasks as needed to cover the goal scope."

        return template.format(
            goal=goal,
            hours_per_week=hours_per_week,
            target_date=str(target_date),
            existing_tasks=tasks_lines,
            max_tasks_instruction=max_tasks_instruction,
        )
