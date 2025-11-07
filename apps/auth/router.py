from fastapi import APIRouter, HTTPException
from fastapi.params import Body

from apps.auth.dependency import AuthDependency
from apps.auth.service import AuthServiceDependency


router = APIRouter(
    prefix="/auth",
)


@router.post("/login")
async def login(
    auth_service: AuthServiceDependency,
    username: str = Body(
        ..., min_length=5, max_length=100, regex=r"^[A-Za-z0-9@_.-]+$"
    ),
    password: str = Body(..., min_length=5, max_length=100),
):
    token = await auth_service.authenticate_and_create_jwt(username, password)
    return {"access_token": token}


@router.post("/logout")
async def logout(auth_service: AuthServiceDependency, auth: AuthDependency):
    await auth_service.invalidate_jwt(auth.token)
    return {"message": "Logged out successfully"}


@router.get("/auth")
async def protected_route(auth_service: AuthDependency):
    return {"message": "This is a protected route"}
