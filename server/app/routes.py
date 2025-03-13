from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from uuid import UUID
from .auth import AccessToken
from .config import config
from .utils import app_to_workflow_config, is_valid_uuid
from .workflow import Workflow
from .workflow_definition.manager import (
    get_workflow_definition_by_id,
    get_workflow_definition_list,
)
from .workflow_handler import get_workflows_by_user
from .api_dependencies import get_authenticated_user, get_valid_access_token
from .schemas import WorkflowId, WorkflowDefinitionListItem, WorkflowDetail, WorkflowListItem, WorkflowRun

api_router = APIRouter(prefix="/api")

@api_router.post("/run", response_model=WorkflowId, responses={400: {"description": "Invalid workflow definition ID"}, 401: {"description": "Unauthorized"}})
async def run_workflow(workflow_run: WorkflowRun, token: AccessToken = Depends(get_valid_access_token)):
    workflow_definition = get_workflow_definition_by_id(workflow_run.workflow_definition_id)
    if not workflow_definition:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow definition not found")

    if token.is_authorized_for_workflow(workflow_definition):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    workflow_config = app_to_workflow_config()
    workflow = Workflow(
        log_dir=config.app.log_dir,
        tes_url=config.snakemake.tes_url,
        token=token
    )

    username = token.userinfo.sub
    workflow_id = workflow.run(
        workflow_config=workflow_config,
        workflow_definition_id=workflow_run.workflow_definition_id,
        input_dir=workflow_run.input_dir,
        output_dir=workflow_run.output_dir,
        username=username
    )
    return WorkflowId(id=workflow_id)


@api_router.get("/workflow", response_model=list[WorkflowListItem])
async def get_workflows(token: AccessToken = Depends(get_valid_access_token)):
    username = token.userinfo.sub
    workflows = get_workflows_by_user(username)
    return workflows


@api_router.delete("/workflow/{workflow_id}", response_model=WorkflowId, responses={400: {"description": "Invalid workflow ID"}, 404: {"description": "Workflow not found"}})
async def cancel_workflow(workflow_id: UUID, token: AccessToken = Depends(get_valid_access_token)):
    if not is_valid_uuid(workflow_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID")

    workflow = Workflow(
        log_dir=config.app.log_dir,
        tes_url=config.snakemake.tes_url,
        token=token,
        id=str(workflow_id)
    )
    
    username = token.userinfo.sub
    if not workflow.exists() or not workflow.is_owned_by_user(username):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    workflow.cancel()

    return WorkflowId(id=workflow_id)

@api_router.get("/workflow/{workflow_id}", response_model=WorkflowDetail, responses={400: {"description": "Invalid workflow ID"}, 404: {"description": "Workflow not found"}})
async def worflow_detail(workflow_id: str, token: AccessToken = Depends(get_valid_access_token)):
    if not is_valid_uuid(workflow_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID")

    workflow = Workflow(
        log_dir=config.app.log_dir,
        tes_url=config.snakemake.tes_url,
        token=token,
        id=workflow_id
    )

    username = token.userinfo.sub
    if not workflow.exists() or not workflow.is_owned_by_user(username):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    workflow_detail = workflow.get_detail()

    return workflow_detail


@api_router.get("/workflow_definition", response_model=list[WorkflowDefinitionListItem])
def workflow_definition():
    workflow_definitions = get_workflow_definition_list()

    return workflow_definitions
