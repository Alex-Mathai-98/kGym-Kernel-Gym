# api.py
from urllib.parse import urljoin
import requests
from aiohttp import ClientSession

class KBDrSession:
    """ Multiple requests can be made in the given session """

    def __init__(self, kbdr_api_url: str, timeout: int=5):
        self.api_url = kbdr_api_url
        self.timeout = timeout

    def create_job(self, job_workers: list[str], worker_arguments: list[dict], kv: dict[str, str]) -> str:
        """
        Create a new job on server accroding to the given workers, arguments and kv pairs
        If created successfully, return the job ID
        If not, throw a ValueError with error text
        """
        resp = requests.post(urljoin(self.api_url, 'jobs/new_raw_job'), json={
            'job_workers': job_workers,
            'worker_arguments': worker_arguments,
            'kv': kv
        }, timeout=self.timeout)
        if resp.status_code == 200:
            return resp.text
        else:
            raise ValueError("Failed to create the job", resp.status_code, resp.text)

    def reset_job(self, job_id: str, job_workers: list[str], worker_arguments: list[dict], kv: dict[str, str], restart_from: int=0):
        """
        Reset the status of the job.
        Replace workers and arguments according to the function parameters.
        If not resetted, throw a ValueError with error text
        """
        resp = requests.post(
            urljoin(self.api_url, f'jobs/{job_id}/reset?restart_from={restart_from}'), json={
                'job_workers': job_workers,
                'worker_arguments': worker_arguments,
                'kv': kv
            },
            timeout=self.timeout)
        if resp.status_code != 200:
            raise ValueError("Failed to reset the job", resp.status_code, resp.text)

    def restart_job(self, job_id: str, restart_from: int=-1):
        resp = requests.post(urljoin(self.api_url, f'jobs/{job_id}/restart?restart_from={restart_from}'), timeout=self.timeout)
        if resp.status_code != 200:
            raise ValueError("Failed to restart the job", resp.status_code, resp.text)

    def abort_job(self, job_id: str):
        resp = requests.post(urljoin(self.api_url, f'jobs/{job_id}/abort'), timeout=self.timeout)
        if resp.status_code != 200:
            raise ValueError("Failed to abort the job", resp.status_code, resp.text)

    def get_job_ctx(self, job_id: str):
        resp = requests.get(urljoin(self.api_url, f'jobs/{job_id}'), timeout=self.timeout)
        if resp.status_code != 200:
            raise ValueError("Failed to get the job", resp.status_code, resp.text)
        return resp.json()

    def update_kv(self, job_id: str, kv: dict[str, str]):
        resp = requests.post(
            urljoin(self.api_url, f'jobs/{job_id}/keys'), json=kv, timeout=self.timeout)
        if resp.status_code != 200:
            raise ValueError("Failed to update the KV", job_id, resp.status_code, resp.text)

    def get_kv(self, job_id: str):
        resp = requests.get(
            urljoin(
                self.api_url, f'jobs/{job_id}/keys') + '?with_values=true', timeout=self.timeout)
        if resp.status_code != 200:
            raise ValueError("Failed to get the kv", job_id, resp.status_code, resp.text)
        return resp.json()

class KBDrAsyncSession:
    """ Multiple requests can be made in the given session """

    def __init__(self, kbdr_api_url: str, timeout: int=5):
        self.api_url = kbdr_api_url
        self.timeout = timeout
        self.sess = ClientSession(self.api_url, timeout=timeout)

    async def create_job(self, job_workers: list[str], worker_arguments: list[dict], kv: dict[str, str]) -> str:
        """
        Create a new job on server accroding to the given workers, arguments and kv pairs
        If created successfully, return the job ID
        If not, throw a ValueError with error text
        """
        resp = await self.sess.post('/jobs/new_raw_job', json={
            'job_workers': job_workers,
            'worker_arguments': worker_arguments,
            'kv': kv
        })
        if resp.status == 200:
            return await resp.text()
        else:
            raise ValueError("Failed to create the job", resp.status, await resp.text())

    async def reset_job(self, job_id: str, job_workers: list[str], worker_arguments: list[dict], kv: dict[str, str], restart_from: int=0):
        """
        Reset the status of the job.
        Replace workers and arguments according to the function parameters.
        If not resetted, throw a ValueError with error text
        """
        resp = await self.sess.post(f'/jobs/{job_id}/reset?restart_from={restart_from}', json={
            'job_workers': job_workers,
            'worker_arguments': worker_arguments,
            'kv': kv
        })
        if resp.status != 200:
            raise ValueError("Failed to reset the job", resp.status, await resp.text())

    async def restart_job(self, job_id: str, restart_from: int=0):
        resp = await self.sess.post(f'/jobs/{job_id}/restart?restart_from={restart_from}')
        if resp.status != 200:
            raise ValueError("Failed to restart the job", resp.status, await resp.text())

    async def abort_job(self, job_id: str):
        resp = await self.sess.post(f'/jobs/{job_id}/abort')
        if resp.status != 200:
            raise ValueError("Failed to abort the job", resp.status, await resp.text())

    async def get_job_ctx(self, job_id: str):
        resp = await self.sess.get(f'/jobs/{job_id}')
        if resp.status != 200:
            raise ValueError("Failed to get the job", resp.status, resp.text())
        return await resp.json()

    async def update_kv(self, job_id: str, kv: dict[str, str]):
        resp = await self.sess.post(f'/jobs/{job_id}/keys', json=kv)
        if resp.status != 200:
            raise ValueError("Failed to update the KV", job_id, resp.status, await resp.text())

    async def get_kv(self, job_id: str):
        resp = await self.sess.get(f'/jobs/{job_id}/keys' + '?with_values=true')
        if resp.status != 200:
            raise ValueError("Failed to get the kv", job_id, resp.status, await resp.text())
        return await resp.json()
