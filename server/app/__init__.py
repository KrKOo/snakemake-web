import os
import secrets
import tomllib
from flask import Flask

app = Flask(__name__)

if os.environ.get("CONFIG_FILE"):
    app.config.from_envvar("CONFIG_FILE")
else:
    app.config.from_file("../config.cfg", load=tomllib.load, text=False)

if app.config.get("SECRET_KEY"):
    app.secret_key = app.config["SECRET_KEY"]
else:
    app.secret_key = secrets.token_urlsafe(16)


from app import routes

if os.environ.get("FLASK_ENV") == "production":
    app.register_blueprint(routes.api, url_prefix="/")
elif os.environ.get("FLASK_ENV") == "development":
    app.register_blueprint(routes.api, url_prefix="/api")
