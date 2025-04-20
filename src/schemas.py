from datetime import datetime
from enum import Enum
from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field


PyObjectId = Annotated[str, BeforeValidator(str)]


class TypeFile(str, Enum):
    student = "student"
    modeus = "modeus"
    online_course = "online_course"
    site_inf = "site_inf"


class TypeFormSubject(str, Enum):
    online = "online"
    mixed = "mixed"
    traditional = "traditional"
    other = "other"


class BaseModelInDB(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)


class HistoryUploadFile(BaseModel):
    name_file: str
    key: str
    date: datetime
    type: TypeFile
    link: str | None = None
    status_upload: str | None = None


class HistoryUploadFileInDB(HistoryUploadFile, BaseModelInDB):
    pass


class InfoGroupInStudent(BaseModel):
    number: str
    number_course: int
    direction_code: str | None = None
    name_speciality: str | None = None


class StudentInTeam(BaseModel):
    sername: str
    name: str
    patronymic: str
    id: PyObjectId | None = None


class Team(BaseModel):
    name: str
    teachers: list[str]
    students: list[StudentInTeam]


class TeamInSubjectInStudent(BaseModel):
    name: str
    teachers: list[str]
    group_tg_link: str | None = None


class SubjectInStudent(BaseModel):
    full_name: str
    name: str
    teams: list[TeamInSubjectInStudent]
    form_education: str
    site_oc_id: PyObjectId | None = None
    file_oc_id: PyObjectId | None = None
    group_tg_link: str | None = None


class Subject(BaseModel):
    full_name: str
    name: str
    teams: list[Team]
    form_education: str


class SubjectInDB(Subject, BaseModelInDB):
    pass


class InfoOnlineCourse(BaseModel):
    name: str
    university: str | None = None
    date_start: str | None = None
    deadline: list[str] | None = None
    info: str | None = None


class InfoOnlineCourseInDB(InfoOnlineCourse, BaseModelInDB):
    pass


class InfoOCInFile(BaseModel):
    name: str
    name_subject: str
    platform: str
    university: str
    form_edu: str


class InfoOCInFileInDB(InfoOCInFile, BaseModelInDB):
    pass


class InfoOnlineCourseInStudent(InfoOnlineCourse):
    scores: dict | None = None


class Student(BaseModel):
    personal_number: str
    name: str
    surname: str
    patronymic: str | None = None
    email: str | None = None
    tg_chat_id: str | None = None
    date_of_birth: str
    group: InfoGroupInStudent
    status: bool | None = False
    type_of_cost: str | None = None
    type_of_education: str | None = None
    subjects: list[SubjectInStudent] = []
    online_course: list[InfoOnlineCourseInStudent] = []

    @classmethod
    def filter_update_fields(self) -> list[str]:
        return ["personal_number"]

    @classmethod
    def update_fields(self) -> list[str]:
        return ["status", "type_of_cost", "type_of_education", "group.number", "group.number_course", "surname", "name", "patronymic", "date_of_birth"]

    @classmethod
    def modeus_filter_update_fields(self) -> list[str]:
        return ["personal_number"]

    @classmethod
    def modeus_update_fields(self) -> list[str]:
        return ["group.direction_code", "group.name_speciality", "subjects"]


class StudentInDB(Student, BaseModelInDB):
    pass


class DictNames(BaseModel):
    modeus: str
    site_inf: str | None = None
    file_course: str | None = None


class DictNamesInDB(DictNames, BaseModelInDB):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)


class FAQ(BaseModel):
    question: str
    answer: str


class FAQTopic(BaseModel):
    name: str
    faqs: list[FAQ] = []


class FAQTopicInDB(FAQTopic, BaseModelInDB):
    pass


class OnboardTopic(BaseModel):
    name: str
    text: str | None = None
    question: str | None = None
    answer: str | None = None


class OnboardSection(BaseModel):
    name: str
    callback_data: str
    topics: list[OnboardTopic]


class OnboardCourse(BaseModel):
    name: str
    is_main: bool = False
    is_active: bool = True
    sections: list[OnboardSection]


class OnboardCourseInDB(OnboardCourse, BaseModelInDB):
    pass
