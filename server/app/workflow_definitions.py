import os
import json

from app import app
from .wrappers import with_updated_workflow_definitions


def get_workflow_metadata(workflow_dir):
    with open(os.path.join(workflow_dir, "metadata.json")) as json_data:
        metadata = json.load(json_data)
        return metadata


@with_updated_workflow_definitions
def get_workflow_definition_dir_by_id(workflow_definition_id):
    for workflow_definition_dir in get_workflow_definition_dirs():
        if (
            get_workflow_metadata(workflow_definition_dir)["id"]
            == workflow_definition_id
        ):
            return workflow_definition_dir


def get_workflow_definition_dirs():
    workflow_definition_dirs = [
        os.path.join(app.config["WORKFLOW_DEFINITION_DIR"], d)
        for d in os.listdir(app.config["WORKFLOW_DEFINITION_DIR"])
        if not d.startswith(".")
    ]

    # Filter out non-directories
    workflow_definition_dirs = [d for d in workflow_definition_dirs if os.path.isdir(d)]

    return workflow_definition_dirs


@with_updated_workflow_definitions
def get_workflow_definitions():
    res = []
    for workflow_definition_dir in get_workflow_definition_dirs():
        workflow_res = {}

        metadata = get_workflow_metadata(workflow_definition_dir)
        workflow_res["id"] = metadata["id"]
        workflow_res["name"] = metadata["name"]

        with open(os.path.join(str(workflow_definition_dir), "Snakefile")) as f:
            workflow_res["definition"] = f.read()

        res.append(workflow_res)

    return res
