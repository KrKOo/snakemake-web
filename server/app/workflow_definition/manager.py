import json
import os

from flask import current_app as app

from app.wrappers import with_updated_workflow_definitions

from . import WorkflowDefinitionListItem, WorkflowDefinitionMetadata


def get_workflow_definition(dir: str) -> WorkflowDefinitionMetadata:
    with open(os.path.join(dir, "metadata.json")) as json_data:
        metadata = json.load(json_data)
        return WorkflowDefinitionMetadata(dir, **metadata)


def get_workflow_definitions() -> list[WorkflowDefinitionMetadata]:
    workflow_definition_dirs = get_workflow_definition_dirs()
    return [get_workflow_definition(d) for d in workflow_definition_dirs]


@with_updated_workflow_definitions
def get_workflow_definition_by_id(
    workflow_definition_id: str,
) -> WorkflowDefinitionMetadata | None:
    for workflow_definition in get_workflow_definitions():
        if workflow_definition.id == workflow_definition_id:
            return workflow_definition
    
    return None


def get_workflow_definition_dirs() -> list[str]:
    workflow_definition_dirs = [
        os.path.join(app.config["APP_WORKFLOW_DEFINITION_DIR"], d)
        for d in os.listdir(app.config["APP_WORKFLOW_DEFINITION_DIR"])
        if not d.startswith(".")
    ]

    # Filter out non-directories
    workflow_definition_dirs = [d for d in workflow_definition_dirs if os.path.isdir(d)]

    return workflow_definition_dirs


@with_updated_workflow_definitions
def get_workflow_definition_list() -> list[WorkflowDefinitionListItem]:
    res = []

    for workflow_definition in get_workflow_definitions():
        with open(os.path.join(str(workflow_definition.dir), "Snakefile")) as f:
            definition = f.read()

        workflow_res = WorkflowDefinitionListItem(
            id=workflow_definition.id,
            name=workflow_definition.name,
            definition=definition,
        )
        res.append(workflow_res)

    return res
