from pydantic_settings import BaseSettings
import logging


class Settings(BaseSettings):
    CORS: str

    MY_URL: str

    URL_CORE_SERVER: str
    CORE_SERVER_SECRET_TOKEN: str

    MGO_HOST: str
    MGO_PORT: int
    MGO_NAME_DB: str

    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_URL: str
    MINIO_BUCKET_NAME: str

    KAFKA_HOST: str
    KAFKA_PORT: int
    KAFKA_TOPIC: str

    def __init__(self):
        super().__init__(
            _env_file=".env",
            _env_file_encoding="utf-8",
        )

        self.config_logging()

    def config_logging(self, level=logging.INFO) -> None:
        logging.basicConfig(
            level=level,
            datefmt="%Y-%m-%d %H:%M:%S",
            format="[%(asctime)s.%(msecs)03d] %(module)20s:%(lineno)-3d %(levelname)-7s - %(message)s",
        )

    @property
    def URLS_CORS(self) -> list[str]:
        return self.CORS.split(",")


settings = Settings()
