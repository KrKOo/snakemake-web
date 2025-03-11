from .models import Workflow as WorkflowModel
from typing import Any, cast
from .schemas import WorkflowListItem


def get_workflows_by_user(username: str) -> list[WorkflowListItem]:
    workflows: list[Any] = cast(
        list[Any],
        WorkflowModel.objects(created_by=username).only(
            "id", "state", "created_at", "total_jobs", "finished_jobs"
        ),
    )

    res = []
    for workflow in workflows:
        workflow_res = WorkflowListItem(
            id=workflow.id,
            created_at=workflow.created_at,
            state=workflow.state,
            total_jobs=workflow.total_jobs,
            finished_jobs=workflow.finished_jobs,
        )

        res.append(workflow_res)

    return res
