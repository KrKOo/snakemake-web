import os
import secrets

from celery import Celery
from flask import Flask, send_from_directory
from mongoengine import connect as mongo_connect

from .config import YAMLConfig


def create_app():
    return entrypoint("app")


def create_celery():
    return entrypoint("celery")


def init_celery_app(app: Flask) -> Celery:
    celery_app = Celery(app.name)
    celery_app.config_from_object(
        dict(
            broker_url=app.config["CELERY_BROKER_URL"],
            result_backend=app.config["CELERY_RESULT_BACKEND"],
        )
    )
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def entrypoint(mode="app"):
    app = Flask(__name__)

    if os.environ.get("CONFIG_FILE"):
        config = YAMLConfig(os.environ.get("CONFIG_FILE"))
    else:
        config = YAMLConfig("../config.yaml")

    print(config.to_dict())
    app.config.from_mapping(config.to_dict())

    if app.config.get("APP_SECRET_KEY"):
        app.secret_key = app.config["APP_SECRET_KEY"]
    else:
        app.secret_key = secrets.token_urlsafe(16)

    mongo_connect(host=app.config["MONGO_MONGODB_URI"], uuidRepresentation="standard")

    register_routes(app)

    celery_app = init_celery_app(app)
    if mode == "celery":
        return celery_app
    if mode == "app":
        return app


def register_routes(app):
    with app.app_context():
        from . import routes

        app.register_blueprint(routes.api, url_prefix="/api")

        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve(path):
            web_dir = app.config["APP_WEB_DIR"]
            if path != "" and os.path.exists(os.path.join(web_dir, path)):
                return send_from_directory(web_dir, path)

            return send_from_directory(web_dir, "index.html")
