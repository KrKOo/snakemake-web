from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

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

api_router = APIRouter(prefix="/api")

@api_router.post("/run")
async def run_workflow(request: Request, username: str = Depends(get_authenticated_user), token: AccessToken = Depends(get_valid_access_token)):
    data = await request.json()

    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

    workflow_definition_id = data.get("id")

    workflow_definition = get_workflow_definition_by_id(workflow_definition_id)
    if not workflow_definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow definition not found")

    if token.is_authorized_for_workflow(workflow_definition):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    input_dir = data.get("input_dir")
    output_dir = data.get("output_dir")

    workflow_config = app_to_workflow_config()
    workflow = Workflow(
        log_dir=config.app.log_dir,
        tes_url=config.snakemake.tes_url,
        token=token
    )

    workflow_id = workflow.run(
        workflow_config=workflow_config,
        workflow_definition_id=workflow_definition_id,
        input_dir=input_dir,
        output_dir=output_dir,
        username=username
    )
    return {"workflow_id": workflow_id}


@api_router.get("/workflow")
async def get_workflows(username: str = Depends(get_authenticated_user)):
    workflows = get_workflows_by_user(username)
    return workflows


@api_router.delete("/workflow/{workflow_id}")
async def cancel_workflow(workflow_id: str, username: str = Depends(get_authenticated_user), token: AccessToken = Depends(get_valid_access_token)):
    if not is_valid_uuid(workflow_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID")

    workflow = Workflow(
        log_dir=config.app.log_dir,
        tes_url=config.snakemake.tes_url,
        token=token,
        id=workflow_id
    )
    
    if not workflow.exists() or not workflow.is_owned_by_user(username):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    workflow.cancel()

    return {"message": "Workflow canceled"}

@api_router.get("/workflow/{workflow_id}")
async def worflow_detail(workflow_id: str, username: str = Depends(get_authenticated_user), token: AccessToken = Depends(get_valid_access_token)):
    if not is_valid_uuid(workflow_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID")

    workflow = Workflow(
        log_dir=config.app.log_dir,
        tes_url=config.snakemake.tes_url,
        token=token,
        id=workflow_id
    )

    if not workflow.exists() or not workflow.is_owned_by_user(username):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    workflow_detail = workflow.get_detail()

    return workflow_detail


@api_router.get("/workflow_definition")
def workflow_definition():
    workflow_definitions = get_workflow_definition_list()

    return workflow_definitions
