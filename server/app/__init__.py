import os
import secrets
import tomllib
from flask import Flask, send_from_directory

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

app.register_blueprint(routes.api, url_prefix="/api")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    web_dir = app.config.get("WEB_DIR")
    if path != "" and os.path.exists(os.path.join(web_dir, path)):
        return send_from_directory(web_dir, path)

    return send_from_directory(web_dir, "index.html")
