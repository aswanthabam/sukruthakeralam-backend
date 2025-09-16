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
    username: str = Body(..., min_length=5, max_length=100, regex=r"^[A-Za-z0-9_.-]+$"),
    password: str = Body(..., min_length=5, max_length=100),
):
    token = auth_service.authenticate_and_create_jwt(username, password)
    return {"access_token": token}


@router.get("/auth")
async def protected_route(auth_service: AuthDependency):
    return {"message": "This is a protected route"}
