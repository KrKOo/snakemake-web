from flask import Blueprint, current_app, request

from .auth import AccessToken
from .utils import app_to_workflow_config, is_valid_uuid
from .workflow import Workflow
from .workflow_definition.manager import (
    get_workflow_definition_by_id,
    get_workflow_definition_list,
)
from .workflow_handler import get_workflows_by_user
from .wrappers import with_access_token, with_user

api = Blueprint("api", __name__)


@api.route("/run", methods=["POST"])
@with_user
@with_access_token
def run_workflow(token: AccessToken, username: str):
    data = request.json

    if not data:
        return "Invalid request", 400

    workflow_definition_id = data.get("id")

    workflow_definition = get_workflow_definition_by_id(workflow_definition_id)
    if not workflow_definition:
        return "Workflow definition not found", 404

    if token.is_authorized_for_workflow(workflow_definition):
        return "Unauthorized", 401

    input_dir = data.get("input_dir")
    output_dir = data.get("output_dir")

    workflow_config = app_to_workflow_config(current_app)
    workflow = Workflow(
        log_dir=current_app.config["APP_LOG_DIR"],
        tes_url=current_app.config["SNAKEMAKE_TES_URL"],
        token=token
    )

    workflow_id = workflow.run(
        workflow_config=workflow_config,
        workflow_definition_id=workflow_definition_id,
        input_dir=input_dir,
        output_dir=output_dir,
        username=username
    )
    return {"workflow_id": workflow_id}, 200


@api.route("/workflow", methods=["GET"])
@with_user
def workflow(username):
    workflows = get_workflows_by_user(username)
    return workflows, 200


@api.route("/workflow/<workflow_id>", methods=["DELETE"])
@with_user
@with_access_token
def cancel_workflow(token: AccessToken, username: str, workflow_id: str):
    if not is_valid_uuid(workflow_id):
        return "Invalid workflow ID", 400

    workflow = Workflow(
        id=workflow_id,
        log_dir=current_app.config["APP_LOG_DIR"],
        tes_url=current_app.config["SNAKEMAKE_TES_URL"],
        token=token
    )
    
    if not workflow.exists() or not workflow.is_owned_by_user(username):
        return "Workflow not found", 404

    workflow.cancel()

    return "Workflow canceled", 200


@api.route("/workflow/<workflow_id>", methods=["GET"])
@with_user
@with_access_token
def worflow_jobs(token:AccessToken, username: str, workflow_id: str):
    if not is_valid_uuid(workflow_id):
        return "Invalid workflow ID", 400

    workflow = Workflow(
        id=workflow_id,
        log_dir=current_app.config["APP_LOG_DIR"],
        tes_url=current_app.config["SNAKEMAKE_TES_URL"],
        token=token
    )

    if not workflow.exists() or not workflow.is_owned_by_user(username):
        return "Workflow not found", 404

    workflow_detail = workflow.get_detail()

    return workflow_detail, 200


@api.route("/workflow_definition")
def workflow_definition():
    workflow_definitions = get_workflow_definition_list()

    return workflow_definitions, 200
