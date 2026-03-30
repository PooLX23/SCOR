from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import UploadFile

from app.core.config import settings


class SharePointService:
    def __init__(self) -> None:
        self.enabled = all(
            [
                settings.graph_client_id,
                settings.graph_client_secret,
                settings.sharepoint_site_id,
                settings.sharepoint_drive_id,
            ]
        )

    def _token(self) -> str:
        token_url = f'https://login.microsoftonline.com/{settings.entra_tenant_id}/oauth2/v2.0/token'
        data = {
            'client_id': settings.graph_client_id,
            'client_secret': settings.graph_client_secret,
            'grant_type': 'client_credentials',
            'scope': 'https://graph.microsoft.com/.default',
        }
        response = httpx.post(token_url, data=data, timeout=15)
        response.raise_for_status()
        return response.json()['access_token']

    async def upload_files(self, application_id: int, files: list[UploadFile]) -> str:
        folder = f"{settings.sharepoint_root_folder}/{application_id}-{uuid4().hex[:8]}"
        if not self.enabled:
            local_folder = Path('uploads') / folder
            local_folder.mkdir(parents=True, exist_ok=True)
            for f in files:
                destination = local_folder / f.filename
                destination.write_bytes(await f.read())
            return str(local_folder)

        token = self._token()
        headers = {'Authorization': f'Bearer {token}'}
        async with httpx.AsyncClient(timeout=60) as client:
            for file in files:
                content = await file.read()
                upload_url = (
                    f'https://graph.microsoft.com/v1.0/drives/{settings.sharepoint_drive_id}'
                    f'/root:/{folder}/{file.filename}:/content'
                )
                response = await client.put(upload_url, headers=headers, content=content)
                response.raise_for_status()

        return folder
