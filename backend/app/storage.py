from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os
import io
import aiofiles
from urllib.parse import urljoin
from .config import get_settings

settings = get_settings()


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, file_path: str, file_data: bytes) -> str:
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        pass

    @abstractmethod
    def get_url(self, file_path: str) -> str:
        pass


class LocalStorage(StorageBackend):
    def __init__(self):
        self.base_path = settings.STORAGE_LOCAL_PATH
        self.base_url = settings.STORAGE_BASE_URL
        os.makedirs(self.base_path, exist_ok=True)

    async def save(self, file_path: str, file_data: bytes) -> str:
        full_path = os.path.join(self.base_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(file_data)
        
        return self.get_url(file_path)

    async def delete(self, file_path: str) -> bool:
        full_path = os.path.join(self.base_path, file_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception:
            return False

    async def exists(self, file_path: str) -> bool:
        full_path = os.path.join(self.base_path, file_path)
        return os.path.exists(full_path)

    def get_url(self, file_path: str) -> str:
        base_url = self.base_url if self.base_url.endswith('/') else self.base_url + '/'
        return urljoin(base_url, file_path)


class S3Storage(StorageBackend):
    def __init__(self):
        try:
            import boto3
            from botocore.client import Config
            
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                endpoint_url=settings.S3_ENDPOINT or None,
                config=Config(signature_version='s3v4')
            )
            self.bucket = settings.S3_BUCKET
            self.base_url = settings.STORAGE_BASE_URL
        except ImportError:
            raise ImportError("boto3 is required for S3 storage. Install it with: pip install boto3")

    async def save(self, file_path: str, file_data: bytes) -> str:
        self.s3.put_object(
            Bucket=self.bucket,
            Key=file_path,
            Body=file_data,
            ACL='public-read'
        )
        return self.get_url(file_path)

    async def delete(self, file_path: str) -> bool:
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=file_path)
            return True
        except Exception:
            return False

    async def exists(self, file_path: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=file_path)
            return True
        except Exception:
            return False

    def get_url(self, file_path: str) -> str:
        if self.base_url:
            base_url = self.base_url if self.base_url.endswith('/') else self.base_url + '/'
            return urljoin(base_url, file_path)
        return f"https://{self.bucket}.s3.{settings.S3_REGION}.amazonaws.com/{file_path}"


class OSSStorage(StorageBackend):
    def __init__(self):
        try:
            import oss2
            
            self.auth = oss2.Auth(settings.OSS_ACCESS_KEY, settings.OSS_SECRET_KEY)
            self.bucket = oss2.Bucket(
                self.auth,
                settings.OSS_ENDPOINT,
                settings.OSS_BUCKET
            )
            self.base_url = settings.STORAGE_BASE_URL
        except ImportError:
            raise ImportError("oss2 is required for OSS storage. Install it with: pip install oss2")

    async def save(self, file_path: str, file_data: bytes) -> str:
        self.bucket.put_object(file_path, file_data)
        return self.get_url(file_path)

    async def delete(self, file_path: str) -> bool:
        try:
            self.bucket.delete_object(file_path)
            return True
        except Exception:
            return False

    async def exists(self, file_path: str) -> bool:
        try:
            return self.bucket.object_exists(file_path)
        except Exception:
            return False

    def get_url(self, file_path: str) -> str:
        if self.base_url:
            base_url = self.base_url if self.base_url.endswith('/') else self.base_url + '/'
            return urljoin(base_url, file_path)
        return f"https://{settings.OSS_BUCKET}.{settings.OSS_ENDPOINT}/{file_path}"


def get_storage_backend() -> StorageBackend:
    if settings.STORAGE_TYPE == "s3":
        return S3Storage()
    elif settings.STORAGE_TYPE == "oss":
        return OSSStorage()
    else:
        return LocalStorage()
