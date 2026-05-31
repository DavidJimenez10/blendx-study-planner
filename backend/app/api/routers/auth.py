from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...schemas.auth import LoginInput, RegisterInput, TokenResponse
from ...services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterInput, svc: AuthServiceDep):
    return svc.register(data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginInput, svc: AuthServiceDep):
    return svc.login(data)
