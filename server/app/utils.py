import os
import uuid
import requests
from git import Repo

from app import app

tes_auth = requests.auth.HTTPBasicAuth(
    app.config["TES_BASIC_AUTH_USER"], app.config["TES_BASIC_AUTH_PASSWORD"]
)


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def pull_workflow_definitions():
    workflow_definition_dir = app.config["WORKFLOW_DEFINITION_DIR"]

    if not os.path.exists(workflow_definition_dir):
        os.makedirs(workflow_definition_dir)
        Repo.clone_from(app.config["WORKFLOW_DEFINITION_REPO"], workflow_definition_dir)
    else:
        repo = Repo(workflow_definition_dir)
        repo.remotes.origin.pull()

    branch = app.config["WORKFLOW_DEFINITION_BRANCH"]
    if branch:
        repo.git.checkout(branch)
