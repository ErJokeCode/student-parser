from bson import ObjectId
from database.worker_db import WorkerDataBase
from schemas.schemas import DictNames, DictNamesInDB


def add_dict_names(modeus: str, site_inf: str, file_course: str, worker_db: WorkerDataBase) -> DictNamesInDB:
    dict = DictNames(
        modeus=modeus,
        site_inf=site_inf,
        file_course=file_course
    )

    dict_db = worker_db.dict_names.insert_one(dict)

    update_student_course_and_subject(dict_db, worker_db)

    return dict_db


def update_dict_names(dict: DictNamesInDB, worker_db: WorkerDataBase, upsert: bool = False) -> DictNamesInDB:
    dict_db = worker_db.dict_names.update_one(dict, upsert=upsert)

    update_student_course_and_subject(dict_db, worker_db)

    return dict_db


def update_student_course_and_subject(dict: DictNamesInDB, worker_db: WorkerDataBase):
    st_col = worker_db.student.get_collect()

    course_db = worker_db.info_online_course.get_one(name=dict.site_inf)

    file_course = worker_db.onl_cr_in_file.get_one(name=dict.file_course)

    info = f"Предмет: {file_course.name_subject}, платформа: {file_course.platform}, форма обучения: {file_course.form_edu}. Дополнительная информация: {course_db.info}"

    st_col.update_many({
        "online_course.name": dict.file_course
    },
        {"$set":
            {
                "online_course.$.university": course_db.university,
                "online_course.$.date_start": course_db.date_start,
                "online_course.$.deadline": course_db.deadline,
                "online_course.$.info": info
            }
         })

    st_col.update_many(
        {
            "subjects.full_name": dict.modeus
        },
        {
            "$set":
            {
                "subjects.$.site_oc_id": course_db.id,
                "subjects.$.file_oc_id": file_course.id
            }
        }
    )


def delete_dict_names(dict: DictNamesInDB, worker_db: WorkerDataBase) -> dict[str, str]:
    st_col = worker_db.student.get_collect()

    file_course = worker_db.onl_cr_in_file.get_one(name=dict.file_course)

    info = f"Предмет: {file_course.name_subject}, платформа: {file_course.platform}, форма обучения: {file_course.form_edu}"

    st_col.update_many({
        "online_course.name": dict.file_course
    },
        {"$set":
            {
                "online_course.$.university": file_course.university,
                "online_course.$.date_start": None,
                "online_course.$.deadline": None,
                "online_course.$.info": info
            }
         })

    st_col.update_many(
        {
            "subjects.full_name": dict.modeus
        },
        {
            "$set":
            {
                "subjects.$.site_oc_id": None,
                "subjects.$.file_oc_id": None
            }
        }
    )

    return worker_db.dict_names.delete_one(dict.id)
