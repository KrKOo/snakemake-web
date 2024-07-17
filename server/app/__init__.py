import os
import secrets
import sys
import tomllib
from celery import Celery
from mongoengine import connect as mongo_connect
from flask import Flask, send_from_directory


def create_app():
    return entrypoint("app")


def create_celery():
    return entrypoint("celery")


def init_celery_app(app: Flask) -> Celery:
    celery_app = Celery(app.name)
    celery_app.config_from_object(
        dict(
            broker_url=app.config.get("CELERY_BROKER_URL"),
            result_backend=app.config.get("CELERY_RESULT_BACKEND"),
        )
    )
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def entrypoint(mode="app"):
    app = Flask(__name__)

    if os.environ.get("CONFIG_FILE"):
        app.config.from_envvar("CONFIG_FILE")
    else:
        app.config.from_file("../config.cfg", load=tomllib.load, text=False)
    if os.environ.get("CONFIG_FILE"):
        app.config.from_envvar("CONFIG_FILE")
    else:
        app.config.from_file("../config.cfg", load=tomllib.load, text=False)

    if app.config.get("SECRET_KEY"):
        app.secret_key = app.config["SECRET_KEY"]
    else:
        app.secret_key = secrets.token_urlsafe(16)
    if app.config.get("SECRET_KEY"):
        app.secret_key = app.config["SECRET_KEY"]
    else:
        app.secret_key = secrets.token_urlsafe(16)

    mongo_connect(host=app.config.get("MONGODB_URI"), uuidRepresentation="standard")

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
            web_dir = app.config.get("WEB_DIR")
            if path != "" and os.path.exists(os.path.join(web_dir, path)):
                return send_from_directory(web_dir, path)

            return send_from_directory(web_dir, "index.html")
