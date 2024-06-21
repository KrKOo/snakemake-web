from .models import Workflow as WorkflowModel


def get_workflows_by_user(username):
    workflows = WorkflowModel.objects(created_by=username).only(
        "id", "state", "created_at", "total_jobs", "finished_jobs"
    )

    res = []
    for workflow in workflows:
        workflow_res = {
            "id": workflow.id,
            "created_at": workflow.created_at.timestamp() * 1000,
            "state": workflow.state.value,
            "total_jobs": workflow.total_jobs,
            "finished_jobs": workflow.finished_jobs,
        }

        res.append(workflow_res)

    return res
