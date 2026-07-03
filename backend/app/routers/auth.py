"""
API router: auth (see docs/API_Contract.md §1).
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthenticatedUser,
    LoginRequest,
    PasswordChangeRequest,
    PasswordChangeResponse,
    RefreshRequest,
    RefreshResponse,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

auth_service = AuthService()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    access_token, refresh_token, user = auth_service.login(db, payload.email, payload.password)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=AuthenticatedUser(id=user.id, email=user.email, role=user.role),
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    access_token, refresh_token = auth_service.refresh(db, payload.refresh_token)
    return RefreshResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service.logout(db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/password", response_model=PasswordChangeResponse)
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service.change_password(db, current_user, payload)
    return PasswordChangeResponse()
