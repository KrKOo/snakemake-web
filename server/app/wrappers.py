from flask import request
from functools import wraps
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
                "message": "User not authenticated",
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
