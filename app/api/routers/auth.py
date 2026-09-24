"""Register / login / logout / me."""
from fastapi import APIRouter, Depends, Header, Response

from app.api.deps import bearer_token, current_user
from app.api.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest
from app.models.app_user import AppUser
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register(payload: RegisterRequest):
    user = auth_service.register(payload.email, payload.full_name, payload.password, payload.role)
    return user.to_dict()


@router.post("/login")
def login(payload: LoginRequest):
    return auth_service.login(payload.email, payload.password)


@router.get("/me")
def me(user: AppUser = Depends(current_user)):
    return user.to_dict()


@router.post("/change-password", status_code=204)
def change_password(payload: ChangePasswordRequest, user: AppUser = Depends(current_user)):
    auth_service.change_password(user.id, payload.old_password, payload.new_password)
    return Response(status_code=204)


@router.post("/logout", status_code=204)
def logout(authorization: str = Header(None)):
    auth_service.logout(bearer_token(authorization))
    return Response(status_code=204)
