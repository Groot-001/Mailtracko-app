from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from src.core.config.settings import config
from src.core.lifespan import lifespan
from src.shared.exceptions.exception_handler import add_exceptions_handler
from src.shared.infrastructure.middlewares.registry import register_middlewares
from src.modules.organization.application.listeners import organization_activity_listener  # noqa: F401
from src.modules.organization.application.listeners import organization_listener  # noqa: F401
import src.modules.auth.application.listeners.organization_deleted_listener  # noqa: F401 # noqa: F401

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def create_app() -> FastAPI:
    app = FastAPI(title=config.PROJECT_NAME, lifespan=lifespan)
   
    ASSETS_DIR.mkdir(
    parents=True,
    exist_ok=True,
    )

    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

    Instrumentator().instrument(app).expose(app)

    register_routers(app)
    register_middlewares(app)
    register_exception_handlers(app)

    return app


def register_routers(app: FastAPI):
    from src.shared.routers.registry import register_routers as _register
    _register(app)


def register_exception_handlers(app: FastAPI):
    add_exceptions_handler(app)


if __name__ == "__main__":
    uvicorn.run("src.main:create_app", host="0.0.0.0", port=8000, reload=True, factory=True)
