from fastapi import APIRouter

from ...schemas.auth import LoginInput, RegisterInput, TokenResponse
from ..deps import AuthServiceDep

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterInput, svc: AuthServiceDep):
    return svc.register(data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginInput, svc: AuthServiceDep):
    return svc.login(data)
