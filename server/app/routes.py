from flask import Blueprint, request, current_app as app
import requests
from .workflow import Workflow
from .workflow_handler import get_workflows_by_user
from .workflow_definition.manager import get_workflow_definition_list
from .wrappers import with_user, with_access_token
from .utils import is_valid_uuid
from .auth import AccessToken

api = Blueprint("api", __name__)


@api.route("/run", methods=["POST"])
@with_user
@with_access_token
def run_workflow(token: AccessToken, username: str):
    data = request.json
    workflow_definition_id = data.get("id")

    if not token.has_visa("ControlledAccessGrants", workflow_definition_id):
        return "Unauthorized", 401

    input_dir = data.get("input_dir")
    output_dir = data.get("output_dir")

    workflow = Workflow(
        log_dir=app.config["WORKFLOW_LOG_DIR"],
        tes_url=app.config["TES_URL"],
        tes_auth=requests.auth.HTTPBasicAuth(
            username=app.config["TES_BASIC_AUTH_USERNAME"],
            password=app.config["TES_BASIC_AUTH_PASSWORD"],
        ),
    )
    workflow_id = workflow.run(
        workflow_definition_id, input_dir, output_dir, username, token.value
    )
    return {"workflow_id": workflow_id}, 200


@api.route("/workflow", methods=["GET"])
@with_user
def workflow(username):
    workflows = get_workflows_by_user(username)
    return workflows, 200


@api.route("/workflow/<workflow_id>", methods=["DELETE"])
@with_user
def cancel_workflow(username, workflow_id):
    if not is_valid_uuid(workflow_id):
        return "Invalid workflow ID", 400

    workflow = Workflow(
        id=workflow_id,
        log_dir=app.config["WORKFLOW_LOG_DIR"],
        tes_url=app.config["TES_URL"],
        tes_auth=requests.auth.HTTPBasicAuth(
            username=app.config["TES_BASIC_AUTH_USERNAME"],
            password=app.config["TES_BASIC_AUTH_PASSWORD"],
        ),
    )
    if not workflow.exists() or not workflow.is_owned_by_user(username):
        return "Workflow not found", 404

    workflow.cancel()

    return "Workflow canceled", 200


@api.route("/workflow/<workflow_id>", methods=["GET"])
@with_user
def worflow_jobs(username, workflow_id):
    if not is_valid_uuid(workflow_id):
        return "Invalid workflow ID", 400

    workflow = Workflow(
        id=workflow_id,
        log_dir=app.config["WORKFLOW_LOG_DIR"],
        tes_url=app.config["TES_URL"],
        tes_auth=requests.auth.HTTPBasicAuth(
            username=app.config["TES_BASIC_AUTH_USERNAME"],
            password=app.config["TES_BASIC_AUTH_PASSWORD"],
        ),
    )
    if not workflow.exists() or not workflow.is_owned_by_user(username):
        return "Workflow not found", 404

    workflow_detail = workflow.get_detail()

    return workflow_detail, 200


@api.route("/workflow_definition")
def workflow_definition():
    workflow_definitions = get_workflow_definition_list()

    return workflow_definitions, 200
