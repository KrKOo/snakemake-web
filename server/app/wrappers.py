import os
from git import Repo
from flask import request, current_app as app
from functools import wraps
from .auth import AccessToken, AuthClient


auth_client = AuthClient(
    app.config["OIDC_URL"],
    app.config["OIDC_CLIENT_ID"],
    app.config["OIDC_CLIENT_SECRET"],
)


def pull_workflow_definitions():
    workflow_definition_dir = app.config["WORKFLOW_DEFINITION_DIR"]

    if not os.path.exists(workflow_definition_dir):
        os.makedirs(workflow_definition_dir)
        Repo.clone_from(app.config["WORKFLOW_DEFINITION_REPO"], workflow_definition_dir)
    else:
        repo = Repo(workflow_definition_dir)
        repo.remotes.origin.pull()

    branch = app.config.get("WORKFLOW_DEFINITION_BRANCH")
    if branch:
        repo.git.checkout(branch)


def with_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        username = ""
        if "X-Forwarded-Preferred-Username" in request.headers:
            username = request.headers.get("X-Forwarded-Preferred-Username")

        if not username:
            return {
                "message": "User not authenticated",
                "data": None,
                "error": "Unauthorized",
            }, 401

        return f(username, *args, **kwargs)

    return decorated


def with_access_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Forwarded-Access-Token")
        if not token:
            return {
                "message": "No access token",
                "data": None,
                "error": "Unauthorized",
            }, 401

        token = AccessToken(token, auth_client)

        if token.is_expired() or not token.is_valid():
            return {
                "message": "Invalid access token",
                "data": None,
                "error": "Unauthorized",
            }, 401

        return f(token, *args, **kwargs)

    return decorated


def with_updated_workflow_definitions(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        pull_workflow_definitions()
        return f(*args, **kwargs)

    return decorated
