import requests
from app.common import JobModel
from app.schemas import JobDetail, JobListItem
from app.auth import AccessToken


class JobRepository:
    def __init__(self, tes_api_url: str):
        self.tes_api_url = tes_api_url

    def get_detail(self, job_id: str, token: AccessToken) -> JobDetail | None:
        job_model = self._get_model(job_id, token, list_view=False)
        if not job_model:
            return None

        if len(job_model.logs) > 0 and len(job_model.logs[0].logs) > 0:
            job_logs = job_model.logs[0].logs[0].stdout
        else:
            job_logs = ""

        return JobDetail(
            id=job_model.id,
            created_at=job_model.creation_time,
            state=job_model.state,
            logs=job_logs,
        )
    
    def get_list_item(self, job_id: str, token: AccessToken) -> JobListItem | None:
        job_model = self._get_model(job_id, token, list_view=True)

        if not job_model:
            return None

        return JobListItem(
            id=job_model.id,
            created_at=job_model.creation_time,
            state=job_model.state
        )

    def get_list(self, job_ids: list[str], token: AccessToken) -> list[JobListItem]:
        job_list = []
        for job_id in job_ids:
            job_list_item = self.get_list_item(job_id, token)
            if job_list_item:
                job_list.append(job_list_item)
        
        return job_list
    
    def get_detail_list(self, job_ids: list[str], token: AccessToken) -> list[JobDetail]:
        job_list = []
        for job_id in job_ids:
            job_detail = self.get_detail(job_id, token)
            if job_detail:
                job_list.append(job_detail)
        
        return job_list

    def _get_model(self, job_id: str, token: AccessToken, list_view=False) -> JobModel | None:
        request_url = f"{self.tes_api_url}/v1/tasks/{job_id}"
        if not list_view:
            request_url += "?view=FULL"

        response = requests.get(request_url, headers={"Authorization": f"Bearer {token.value}"})

        if response.status_code != 200:
            return None

        job_model = JobModel.model_validate_json(response.text)
        return job_model