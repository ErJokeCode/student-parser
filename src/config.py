from pydantic_settings import BaseSettings
import logging

from database.db import MongoDataBase, WorkerCollection
from schemas import FAQ, DictNames, DictNamesInDB, FAQTopic, FAQTopicInDB, HistoryUploadFile, HistoryUploadFileInDB, InfoOCInFile, InfoOCInFileInDB, OnboardCourse, OnboardCourseInDB, Student, StudentInDB, Subject, SubjectInDB, InfoOnlineCourse, InfoOnlineCourseInDB


class WorkerDataBase(MongoDataBase):
    def __init__(self, host: str, port: int, name_db: str):
        super().__init__(host, port, name_db)

        self.history = WorkerCollection[HistoryUploadFile, HistoryUploadFileInDB](
            self.db["history"], HistoryUploadFile, HistoryUploadFileInDB)
        self.student = WorkerCollection[Student, StudentInDB](
            self.db["student"], Student, StudentInDB)
        self.subject = WorkerCollection[Subject, SubjectInDB](
            self.db["subject"], Subject, SubjectInDB)
        self.info_online_course = WorkerCollection[InfoOnlineCourse, InfoOnlineCourseInDB](
            self.db["info_online_course"], InfoOnlineCourse, InfoOnlineCourseInDB)
        self.dict_names = WorkerCollection[DictNames, DictNamesInDB](
            self.db["dict_names"], DictNames, DictNamesInDB)
        self.bot_faq = WorkerCollection[FAQTopic, FAQTopicInDB](
            self.db["bot_faq"], FAQTopic, FAQTopicInDB)
        self.bot_onboard = WorkerCollection[OnboardCourse, OnboardCourseInDB](
            self.db["bot_onboard"], OnboardCourse, OnboardCourseInDB)
        self.onl_cr_in_file = WorkerCollection[InfoOCInFile, InfoOCInFileInDB](
            self.db["onl_cr_in_file"], InfoOCInFile, InfoOCInFileInDB)


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


worker_db = WorkerDataBase(
    host=settings.MGO_HOST,
    port=settings.MGO_PORT,
    name_db=settings.MGO_NAME_DB)
