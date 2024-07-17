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
) -> WorkflowDefinitionMetadata:
    for workflow_definition in get_workflow_definitions():
        if workflow_definition.id == workflow_definition_id:
            return workflow_definition


def get_workflow_definition_dirs() -> list[str]:
    workflow_definition_dirs = [
        os.path.join(app.config["WORKFLOW_DEFINITION_DIR"], d)
        for d in os.listdir(app.config["WORKFLOW_DEFINITION_DIR"])
        if not d.startswith(".")
    ]

    # Filter out non-directories
    workflow_definition_dirs = [d for d in workflow_definition_dirs if os.path.isdir(d)]

    return workflow_definition_dirs


@with_updated_workflow_definitions
def get_workflow_definition_list() -> list[WorkflowDefinitionListItem]:
    res = []

    for workflow_definition in get_workflow_definitions():
        workflow_res: WorkflowDefinitionListItem = {}
        workflow_res["id"] = workflow_definition.id
        workflow_res["name"] = workflow_definition.name

        with open(os.path.join(str(workflow_definition.dir), "Snakefile")) as f:
            workflow_res["definition"] = f.read()

        res.append(workflow_res)

    return res
