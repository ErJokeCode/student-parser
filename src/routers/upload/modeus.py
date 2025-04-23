from fastapi import HTTPException, UploadFile
import numpy as np
import pandas as pd
from database.worker_db import WorkerDataBase
from worker import update_status_history
from schemas.schemas import StudentInDB, StudentInTeam, Subject, SubjectInStudent, Team, TeamInSubjectInStudent, TypeFormSubject, HistoryUploadFileInDB


def upload_modeus(file: UploadFile, hist: HistoryUploadFileInDB, worker_db: WorkerDataBase) -> dict[str, str]:
    try:
        df = pd.read_excel(file.file.read(), sheet_name=0)
    except Exception as e:
        print(e)
        update_status_history(hist, text_status="Error file read")
        raise HTTPException(status_code=500, detail="File read error")

    worker_db.student.get_collect().update_many(
        {"status": True}, {"$set": {"subjects": []}})

    fill_subjects(df, worker_db, hist)
    fill_students(df, worker_db, hist)

    return {"status": "success"}


def fill_subjects(df: pd.DataFrame, worker_db: WorkerDataBase, hist: HistoryUploadFileInDB):
    worker_db.subject.delete_many()
    try:
        data = df.groupby(["РМУП название", "МУП или УК", "Частный план название"])[
            ["Студент", "Специальность", "Сотрудники", "Группа название"]]
    except Exception as e:
        print(e)
        update_status_history(
            hist, text_status=f"Error work with file. Use stucture file example")

    try:
        subjects: list[Subject] = []
        for key, info in data:
            teams: list[Team] = []

            number_course = get_number_course(key[2], hist)

            for group, item in info.groupby(["Группа название"]):
                teachers = item["Сотрудники"].drop_duplicates(
                ).dropna().to_list()
                students = item["Студент"].drop_duplicates().to_list()

                students_in_team: list[StudentInTeam] = []
                for student in students:
                    sername, name, patronymic = get_split_fio(student)

                    st_team = StudentInTeam(
                        sername=sername,
                        name=name,
                        patronymic=patronymic
                    )

                    find_dict = {
                        "surname": sername,
                        "name": name,
                        "patronymic": patronymic
                    }
                    if number_course != None:
                        find_dict["group.number_course"] = number_course

                    student_db: StudentInDB | None = worker_db.student.get_one(
                        get_none=True, find_dict=find_dict)

                    if student_db != None:
                        st_team.id = student_db.id

                    students_in_team.append(st_team)

                teams.append(Team(
                    name=group[0],
                    teachers=teachers,
                    students=students_in_team
                ))

            subject = Subject(
                full_name=key[0],
                name=key[1],
                teams=teams,
                form_education=get_form_edu(key[0]).value
            )
            subjects.append(subject)

        worker_db.subject.insert_many(subjects)

    except Exception as e:
        print(e)
        update_status_history(
            hist, text_status=f"Ошибка заполнение предметов, используйте шаблон")


def get_number_course(plan: str, hist: HistoryUploadFileInDB) -> int:
    try:
        start_index = plan.rindex("курс")
        return int(plan[start_index - 2: start_index - 1])
    except Exception as e:
        return None


def fill_students(df: pd.DataFrame, worker_db: WorkerDataBase, hist: HistoryUploadFileInDB):
    try:
        data = df.groupby(["Студент", "Поток", "Специальность", "Профиль"])[
            ["РМУП название", "Группа название", "МУП или УК", "Частный план название"]]
    except Exception as e:
        print(e)
        update_status_history(
            hist, text_status=f"Error work with file. Use stucture file example")

    update_students: list[StudentInDB] = []

    for key, value in data:
        surname, name, patronymic = get_split_fio(key[0])
        direction_code, name_speciality = get_info_speciality(key[2])
        number_course = get_number_course(value["Частный план название"], hist)

        find_dict = {
            "surname": surname,
            "name": name,
            "patronymic": patronymic
        }

        if number_course != None:
            find_dict["group.number_course"] = number_course

        student: StudentInDB | None = worker_db.student.get_one(
            get_none=True, find_dict=find_dict)

        if student != None:
            subjects: list[SubjectInStudent] = []
            for names, item in value.groupby(["РМУП название", "МУП или УК"])[["Группа название"]]:
                subject = create_subject_in_student(names, item, worker_db)
                subjects.append(subject)
            student.group.direction_code = direction_code
            student.group.name_speciality = name_speciality
            student.subjects = subjects

            print(student)

            update_students.append(student)

    worker_db.student.bulk_update(StudentInDB.modeus_filter_update_fields(),
                                  StudentInDB.modeus_update_fields(),
                                  update_students)


def create_subject_in_student(names, item: pd.DataFrame, worker_db: WorkerDataBase) -> SubjectInStudent:
    try:
        full_name = names[0]
        name = names[1]
        form_education = get_form_edu(names[0]).value
        teams = item["Группа название"].drop_duplicates().tolist()

        subject_db = worker_db.subject.get_one(
            get_none=True, full_name=full_name, name=name, form_education=form_education)

        teams_sabject: list[TeamInSubjectInStudent] = []
        if subject_db != None:
            for team in subject_db.teams:
                team_in_subject_in_student = TeamInSubjectInStudent(
                    name=team.name,
                    teachers=team.teachers
                )
                if team.name in teams:
                    teams_sabject.append(team_in_subject_in_student)

        dict_onl_cr = worker_db.dict_names.get_one(
            get_none=True, modeus=full_name)
        site_oc_id = None
        file_oc_id = None

        if dict_onl_cr != None:
            online_course = worker_db.onl_cr_in_file.get_one(
                name=dict_onl_cr.file_course, get_none=True)
            online_course_in_site = worker_db.info_online_course.get_one(
                name=dict_onl_cr.site_inf, get_none=True)
            if online_course != None:
                file_oc_id = online_course.id
            if online_course_in_site != None:
                site_oc_id = online_course_in_site.id

        subject = SubjectInStudent(
            full_name=full_name,
            name=name,
            teams=teams_sabject,
            form_education=form_education,
            site_oc_id=site_oc_id,
            file_oc_id=file_oc_id
        )
        print(subject)
        return subject
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="Error create subject in student")


def get_form_edu(rmup: str) -> TypeFormSubject:
    try:
        rmup = rmup.lower()
        if rmup.find("смешанн") != -1:
            return TypeFormSubject.mixed
        elif rmup.find("онлайн") != -1:
            return TypeFormSubject.online
        elif rmup.find("традицион") != -1 or (rmup.find(")") == -1 and rmup.find("(") == -1):
            return TypeFormSubject.traditional
        else:
            return TypeFormSubject.other
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="Error get type form education")


def get_split_fio(fio: str) -> tuple[str, str, str]:
    try:
        fio = fio.split()

        surname = fio[0] if len(fio) > 0 else ""
        name = fio[1] if len(fio) > 1 else ""
        patronymic = fio[2] if len(fio) > 2 else ""

        return (surname, name, patronymic)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error get split fio")


def get_info_speciality(speciality: str) -> tuple[str, str]:
    try:
        speciality = speciality.split()

        direction_code = speciality[0]
        name_speciality = " ".join(speciality[1:])

        return (direction_code, name_speciality)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="Error get info speciality")
