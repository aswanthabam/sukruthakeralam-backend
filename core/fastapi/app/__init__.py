from contextlib import asynccontextmanager
import traceback
import uuid
from fastapi import Request
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from sqlalchemy.exc import StatementError, IntegrityError

from core.exception.core import AbstractException
from core.fastapi.app.exception_handlers import (
    abstract_exception_handler,
    exception_handler,
    integrity_error_handler,
    request_validation_exception_handler,
    statement_error_handler,
    validation_exception_handler,
)
from core.fastapi.response.response_class import CustomORJSONResponse
from core.fastapi.loaders.router import autoload_routers
from core.fastapi.middlewares.process_time_middleware import ProcessingTimeMiddleware
from apps.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("AVC CORE:: Cooking ...")
    yield
    print("AVC CORE:: Cooked !")


def create_app():
    app = FastAPI(lifespan=lifespan, default_response_class=CustomORJSONResponse)

    router = autoload_routers("apps")

    app.include_router(router=router)

    app.add_middleware(ProcessingTimeMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AbstractException, abstract_exception_handler)
    app.add_exception_handler(401, abstract_exception_handler)
    app.add_exception_handler(
        RequestValidationError, request_validation_exception_handler
    )
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(StatementError, statement_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, exception_handler)

    @app.get("/api/ping", summary="Ping the API", tags=["Health Check"])
    def root():
        return HTMLResponse(
            content="<html><h1>Haa shit! My Code is working.</h1></html>"
        )
