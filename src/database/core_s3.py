import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import hashlib
import logging
from typing import AsyncGenerator, AsyncIterator, BinaryIO
from aiobotocore.session import get_session  # type: ignore
from aiobotocore.client import AioBaseClient  # type: ignore
from fastapi import UploadFile
from types_aiobotocore_s3 import S3Client  # Типы для S3
from botocore.config import Config

from schemas.schemas import HistoryUploadFile, TypeFile
from config import settings


_log = logging.getLogger(__name__)


class CoreS3:
    def __init__(
            self,
            user: str,
            password: str,
            endpoint_url: str,
            bucket_name: str,
    ):
        self.__config = {
            "aws_access_key_id": user,
            "aws_secret_access_key": password,
            "endpoint_url": endpoint_url,
            "config": Config(
                signature_version="s3v4",
                connect_timeout=10,
                retries={"max_attempts": 3},
            ),
            "verify": False,
        }

        self.__bucket_name = bucket_name

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[S3Client]:
        session = get_session()
        async with session.create_client("s3", **self.__config) as client:
            yield client

    async def create_bucket(self) -> None:
        name = self.__bucket_name
        async with self.get_client() as client:
            try:
                # Проверяем существование бакета
                existing_buckets = await client.list_buckets()
                bucket_names = [b["Name"] for b in existing_buckets["Buckets"]]

                if name not in bucket_names:
                    # Создаем бакет
                    await client.create_bucket(Bucket=name)
                    _log.info(f"Бакет {name} создан")
                else:
                    _log.info(f"Бакет {name} уже существует")

            except Exception as e:
                _log.error(f"Ошибка при создании бакета: {e}")

    async def upload_file(
        self,
        file_key: str,
        file: UploadFile
    ) -> str:
        async with self.get_client() as client:
            try:
                await file.seek(0)
                await client.put_object(
                    Bucket=self.__bucket_name,
                    Key=file_key,
                    Body=file.file,
                    ContentType=file.content_type if file.content_type is not None else ""
                )
                await file.seek(0)
                _log.info("Файл %s загружен", file.filename)
            except Exception as e:
                _log.error("Ошибка загрузки файла %s: %s", file.filename, e)
                raise

        return settings.MY_URL + "/upload/history/file/" + file_key

    async def get_file_read(self, file_key: str) -> AsyncIterator[bytes]:
        async with self.get_client() as client:
            try:
                response = await client.get_object(
                    Bucket=self.__bucket_name,
                    Key=file_key
                )
                stream = response["Body"]
                while True:
                    # Читаем по 1MB за раз
                    chunk = await stream.read(1024 * 1024)
                    if not chunk:
                        break
                    yield chunk
                _log.info("Файл успешно получен из хранилища %s", file_key)
            except Exception as e:
                _log.error("Ошибка получения файла %s: %s", file_key, e)
                raise

    async def delete_file(self, file_key: str) -> None:
        async with self.get_client() as client:
            try:
                await client.delete_object(
                    Bucket=self.__bucket_name,
                    Key=file_key
                )
                _log.info("Файл %s успешно удален", file_key)
            except Exception as e:
                _log.error("Ошибка удаления файла %s: %s", file_key, e)
                raise

    async def create_hist_file(self, file: UploadFile, type: TypeFile, is_upload: bool = True) -> HistoryUploadFile:
        time = datetime.now()
        hash = hashlib.sha256(file.filename.encode(
            "utf-8") + str(time).encode("utf-8")).hexdigest()
        key = hash + "." + file.filename.split(".")[-1]
        if is_upload:
            link = await self.upload_file(key, file)
        else:
            link = None

        hist_file = HistoryUploadFile(
            name_file=file.filename,
            key=key,
            date=time,
            type=type,
            link=link
        )

        return hist_file


s3_client = CoreS3(
    user=settings.MINIO_ROOT_USER,
    password=settings.MINIO_ROOT_PASSWORD,
    endpoint_url=settings.MINIO_URL,
    bucket_name=settings.MINIO_BUCKET_NAME
)
