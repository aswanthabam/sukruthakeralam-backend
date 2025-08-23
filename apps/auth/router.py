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
    username: str = Body(...),
    password: str = Body(...),
):
    token = auth_service.authenticate_and_create_jwt(username, password)
    return {"access_token": token}


@router.get("/auth")
async def protected_route(auth_service: AuthDependency):
    return {"message": "This is a protected route"}
