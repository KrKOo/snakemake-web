from functools import wraps

from flask import current_app as app
from flask import request

from .auth import AccessToken, AuthClient
from .utils import pull_workflow_definitions


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

        auth_client = AuthClient(
            app.config["OIDC_URL"],
            app.config["OIDC_CLIENT_ID"],
            app.config["OIDC_CLIENT_SECRET"],
        )
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
        pull_workflow_definitions(
            app.config["WORKFLOW_DEFINITION_DIR"],
            app.config["WORKFLOW_DEFINITION_REPO"],
            app.config["WORKFLOW_DEFINITION_BRANCH"],
        )
        return f(*args, **kwargs)

    return decorated
