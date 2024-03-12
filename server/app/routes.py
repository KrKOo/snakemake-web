from flask import Blueprint, request
from .workflow_handler import (
    get_workflow_jobs_info,
    get_workflows,
    run,
    get_workflow_definitions,
)
from .wrappers import with_user, with_access_token
from .utils import is_valid_uuid

api = Blueprint("api", __name__)


@api.route("/run", methods=["POST"])
@with_user
@with_access_token
def run_workflow(token, username):
    workflow_definition_id = request.json.get("id")
    workflow_id = run(workflow_definition_id, username, token)
    return {"workflow_id": workflow_id}, 200


@api.route("/workflow", methods=["GET"])
@with_user
def workflow(username):
    workflows = get_workflows(username)
    return workflows, 200


@api.route("/workflow/<workflow_id>/jobs", methods=["GET"])
@with_user
def worflow_jobs(username, workflow_id):
    if not is_valid_uuid(workflow_id):
        return "Invalid workflow ID", 400

    list_view = request.args.get("view") == "list"

    try:
        jobs_info = get_workflow_jobs_info(username, workflow_id, list_view)
    except FileNotFoundError:
        return "Workflow not found", 404

    return jobs_info, 200


@api.route("/workflow_definition")
def workflow_definition():
    workflow_definitions = get_workflow_definitions()

    return workflow_definitions, 200
