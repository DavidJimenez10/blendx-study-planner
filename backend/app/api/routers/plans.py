from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...schemas.agent import AgentGenerateRequest, BreakdownResponse
from ...schemas.study_plan import StudyPlanCreate, StudyPlanRead, StudyPlanUpdate
from ...schemas.study_task import StudyTaskCreate, StudyTaskRead, StudyTaskUpdate
from ...schemas.task_generation import GenerateTasksRequest, GenerateTasksResponse
from ..deps import (
    AgentServiceDep,
    GenerationServiceDep,
    PlanServiceDep,
    TaskServiceDep,
)

SSEMediaType = "text/event-stream"


class AgentSSEResponse(StreamingResponse):
    media_type = SSEMediaType


router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("", response_model=StudyPlanRead, status_code=201)
def create_plan(data: StudyPlanCreate, svc: PlanServiceDep):
    return svc.create_plan(data)


@router.get("/{plan_id}", response_model=StudyPlanRead)
def get_plan(plan_id: int, svc: PlanServiceDep):
    return svc.get_plan(plan_id)


@router.patch("/{plan_id}", response_model=StudyPlanRead)
def update_plan(
    plan_id: int,
    data: StudyPlanUpdate,
    svc: PlanServiceDep,
):
    return svc.update_plan(plan_id, data)


@router.post("/{plan_id}/tasks", response_model=StudyTaskRead, status_code=201)
def create_task(plan_id: int, data: StudyTaskCreate, svc: TaskServiceDep):
    return svc.create_task(plan_id, data)


@router.get("/{plan_id}/tasks", response_model=list[StudyTaskRead])
def get_tasks(plan_id: int, svc: TaskServiceDep):
    return svc.get_tasks_by_plan(plan_id)


@router.patch("/{plan_id}/tasks/{task_id}", response_model=StudyTaskRead)
def update_task(
    plan_id: int,
    task_id: int,
    data: StudyTaskUpdate,
    svc: TaskServiceDep,
):
    return svc.update_task(plan_id, task_id, data)


@router.post("/{plan_id}/generate-tasks", response_model=GenerateTasksResponse)
def generate_tasks(
    plan_id: int,
    svc: GenerationServiceDep,
    data: GenerateTasksRequest = GenerateTasksRequest(),
):
    return svc.generate_tasks(plan_id, data)


@router.post("/{plan_id}/agent/breakdown", response_model=BreakdownResponse)
def agent_breakdown(plan_id: int, svc: AgentServiceDep):
    return svc.perform_breakdown(plan_id)


@router.post("/{plan_id}/agent/generate", response_class=AgentSSEResponse)
def agent_generate(plan_id: int, data: AgentGenerateRequest, svc: AgentServiceDep):
    for event in svc.execute_planning_graph(plan_id, data):
        yield event
