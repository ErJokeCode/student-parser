from io import BytesIO
import logging
from fastapi import HTTPException, UploadFile
import pandas as pd  # type: ignore

from database.core_s3 import s3_client
from worker import update_status_history
from schemas import HistoryUploadFileInDB, InfoGroupInStudent, Student
from config import WorkerDataBase

_log = logging.getLogger(__name__)


async def upload_student(file: UploadFile, worker_db: WorkerDataBase, hist: HistoryUploadFileInDB) -> dict[str, str]:
    try:
        await file.seek(0)
        file_excel = pd.ExcelFile(await file.read())
        df = pd.read_excel(file_excel, sheet_name=0)
        _log.info(df)
    except Exception as e:
        print(e)
        update_status_history(hist, text_status="Error file read")
        raise HTTPException(status_code=500, detail="File read error")

    try:
        students = []
        for index, item in df.iterrows():
            student = create_student(item)
            students.append(student)
    except Exception as e:
        print(e)
        update_status_history(hist, text_status="Error parse file")
        raise HTTPException(status_code=500, detail="Error parse file")

    try:
        col_st = worker_db.student.get_collect()
        col_st.update_many({}, {"$set": {"status": False}})

        fl = Student.filter_update_fields()
        up_fl = Student.update_fields()

        worker_db.student.bulk_update(fl, up_fl, students, upsert=True)

    except Exception as e:
        print(e)
        update_status_history(hist, text_status="Error update data")
        raise HTTPException(status_code=500, detail="Error update data")

    return {"status": "success"}


def create_student(item) -> Student:
    FIO = item["Фамилия, имя, отчество"].split()
    personal_number = "0" * \
        (8 - len(str(item["Личный №"]))) + str(item["Личный №"])
    student = Student(
        surname=FIO[0] if len(FIO) > 0 else "",
        name=FIO[1] if len(FIO) > 1 else "",
        patronymic=" ".join(FIO[2:]) if len(FIO) > 2 else "",
        department=item["Кафедра"],
        group=InfoGroupInStudent(
            number=item["Группа"], number_course=int(item["Курс"])),
        status=True if item["Состояние"] == "Активный" else False,
        type_of_cost=item["Вид возм. затрат"],
        type_of_education=item["Форма освоения"],
        date_of_birth=item["Дата рождения"] if isinstance(
            item["Дата рождения"], str) else item["Дата рождения"].strftime("%Y-%m-%d"),
        personal_number=personal_number,
        subjects=[],
        online_course=[]
    )

    return student
