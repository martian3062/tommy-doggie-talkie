from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
import httpx

from app.core.config import get_settings


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None

    @property
    def client(self):
        if not self.settings.supabase_enabled:
            return None
        if self._client is None:
            from supabase import create_client

            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_role_key,
            )
        return self._client

    async def save_upload(self, upload: UploadFile, owner_id: str, dog_id: str) -> str:
        suffix = Path(upload.filename or "clip.mp4").suffix or ".mp4"
        local_dir = self.settings.local_media_dir / owner_id / dog_id
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / f"{uuid4()}{suffix}"
        with local_path.open("wb") as out:
            while chunk := await upload.read(1024 * 1024):
                out.write(chunk)
        return str(local_path)

    def download_supabase_object(self, storage_path: str, owner_id: str, dog_id: str) -> str | None:
        if not self.client:
            return None
        local_dir = self.settings.local_media_dir / owner_id / dog_id
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / Path(storage_path).name
        data = self.client.storage.from_(self.settings.supabase_storage_bucket).download(storage_path)
        local_path.write_bytes(data)
        return str(local_path)

    def download_signed_url(self, signed_url: str, owner_id: str, dog_id: str) -> str:
        local_dir = self.settings.local_media_dir / owner_id / dog_id
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / f"{uuid4()}.mp4"
        with httpx.stream("GET", signed_url, timeout=60) as response:
            response.raise_for_status()
            with local_path.open("wb") as out:
                for chunk in response.iter_bytes():
                    out.write(chunk)
        return str(local_path)
