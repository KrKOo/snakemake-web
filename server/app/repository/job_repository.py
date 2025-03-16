import requests
from app.schemas import JobDetail, JobListItem
from app.auth import AccessToken


class JobRepository:
    def __init__(self, tes_api_url: str):
        self.tes_api_url = tes_api_url

    def get_detail(self, job_id: str, token: AccessToken) -> JobDetail | None:
        data = self._get_data(job_id, token, list_view=False)

        try:
            job_logs = data["logs"][0]["logs"][0]["stdout"]
        except KeyError:
            job_logs = ""

        return JobDetail(
            id=data["id"],
            created_at=data["creation_time"],
            state=data["state"],
            logs=job_logs,
        )
    
    def get_list_item(self, job_id: str, token: AccessToken) -> JobListItem | None:
        data = self._get_data(job_id, token, list_view=True)

        return JobListItem(
            id=data["id"],
            created_at=data["creation_time"],
            state=data["state"]
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

    def _get_data(self, job_id: str, token: AccessToken, list_view=False):
        request_url = f"{self.tes_api_url}/v1/tasks/{job_id}"
        if not list_view:
            request_url += "?view=FULL"

        response = requests.get(request_url, headers={"Authorization": f"Bearer {token.value}"})

        if response.status_code != 200:
            return None

        return response.json()