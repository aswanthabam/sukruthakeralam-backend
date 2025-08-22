import traceback
import uuid
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import StatementError, IntegrityError

from core.exception.core import AbstractException


async def abstract_exception_handler(request: Request, exc: AbstractException):
    return ORJSONResponse(exc.to_json(), status_code=exc.status_code)


async def custom_auth_exception_handler(request: Request, exc: Exception):
    return ORJSONResponse(
        {
            "message": "Unauthorized!",
            "error_code": "UNAUTHORIZED",
        },
        status_code=401,
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "type": error.get("type", "unknown"),
                "loc": error.get("loc", []),
                "msg": error.get("msg", "Invalid input"),
                "input": error.get("input", None),
            }
        )
    return ORJSONResponse(
        {
            "message": "Invalid Request, Please check your request",
            "error_code": "REQUEST_VALIDATION_ERROR",
            "errors": errors,
        },
        status_code=422,
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    return ORJSONResponse(
        {
            "message": "Error Processing Request",
            "error_code": "VALIDATION_ERROR",
            "errors": {"msg": f"{e.get('loc')} {e.get('msg')}" for e in exc.errors()},
        },
        status_code=500,
    )


async def statement_error_handler(request: Request, exc: StatementError):
    if isinstance(exc.orig, AbstractException):
        raise exc.orig
    else:
        raise exc


async def integrity_error_handler(request: Request, exc: IntegrityError):
    traceback.print_exc()
    return ORJSONResponse(
        {
            "message": "Integrity Error",
            "error_code": "INTEGRITY_ERROR",
        },
    )


async def exception_handler(request: Request, exc: Exception):
    track_id = str(uuid.uuid4())
    # try:
    #     await notify_error(request, exc, track_id)
    # except Exception as e:
    #     print("Error while sending error notification")
    #     traceback.print_exc()
    return ORJSONResponse(
        {
            "message": "Error Processing Request",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
        status_code=500,
    )
