from functools import wraps

from .config import config
from .utils import pull_workflow_definitions


def with_updated_workflow_definitions(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        pull_workflow_definitions(
            config.app.workflow_definition_dir,
            config.app.workflow_definition_repo,
            config.app.workflow_definition_branch,
        )
        return f(*args, **kwargs)

    return decorated
