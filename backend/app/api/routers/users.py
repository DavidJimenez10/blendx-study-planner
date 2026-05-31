from fastapi import APIRouter

from ...schemas.study_plan import StudyPlanRead
from ...schemas.user import UserCreate, UserRead
from ..deps import PlanServiceDep, UserServiceDep

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(svc: UserServiceDep):
    return svc.get_all_users()


@router.post("", response_model=UserRead, status_code=201)
def create_user(data: UserCreate, svc: UserServiceDep):
    return svc.create_user(data)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, svc: UserServiceDep):
    return svc.get_user(user_id)


@router.get("/{user_id}/plans", response_model=list[StudyPlanRead])
def get_user_plans(user_id: int, svc: PlanServiceDep):
    return svc.get_plans_by_user(user_id)
