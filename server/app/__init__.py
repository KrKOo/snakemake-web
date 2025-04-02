import os

from celery import Celery
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import config
from .routes import api_router


def create_app():
    return entrypoint("app")


def create_celery():
    return entrypoint("celery")


def init_celery_app() -> Celery:
    celery_app = Celery(__name__)
    celery_app.config_from_object(
        dict(
            broker_url=config.celery.broker_url,
            result_backend=config.celery.result_backend,
            task_serializer = "pickle",
            result_serializer = "pickle",
            event_serializer = "json",
            accept_content = ["application/json", "application/x-python-serialize"],
            result_accept_content = ["application/json", "application/x-python-serialize"]
        )
    )
    celery_app.set_default()
    return celery_app


def entrypoint(mode="app"):
    app = FastAPI()

    register_routes(app)

    celery_app = init_celery_app()
    if mode == "celery":
        return celery_app
    if mode == "app":
        return app


def register_routes(app):
    app.include_router(api_router)

    app.mount("/assets", StaticFiles(directory=os.path.join(config.app.web_dir, "assets")), name="static")

    @app.get("/")
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        file_path = os.path.join(config.app.web_dir, "index.html")
        return FileResponse(file_path)