from database.db import MongoDataBase, WorkerCollection
from schemas.schemas import FAQ, DictNames, DictNamesInDB, FAQTopic, FAQTopicInDB, HistoryUploadFile, HistoryUploadFileInDB, InfoOCInFile, InfoOCInFileInDB, OnboardCourse, OnboardCourseInDB, Student, StudentInDB, Subject, SubjectInDB, InfoOnlineCourse, InfoOnlineCourseInDB
from config import settings


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


worker_db = WorkerDataBase(
    host=settings.MGO_HOST,
    port=settings.MGO_PORT,
    name_db=settings.MGO_NAME_DB)
