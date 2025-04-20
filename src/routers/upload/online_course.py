from fastapi import HTTPException, UploadFile
import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import WorkerDataBase
from database.core_s3 import s3_client
from worker import update_status_history
from schemas import HistoryUploadFileInDB, InfoOCInFile, InfoOCInFileInDB, InfoOnlineCourse, InfoOnlineCourseInDB, InfoOnlineCourseInStudent


def parse_info_online_courses(worker_db: WorkerDataBase, hist: HistoryUploadFileInDB):

    url = "https://inf-online.urfu.ru/ru/onlain-kursy/#urfu"

    try:
        response = requests.get(url)
    except Exception as e:
        print(e)
        hist.status_upload = "Not connect to urfu"
        worker_db.history.update_one(hist, get_item=False)

    if response.status_code != 200:
        hist.status_upload = "Error connect to urfu"
        worker_db.history.update_one(hist, get_item=False)
        raise HTTPException(status_code=500, detail="Error connect to urfu")
    else:
        try:
            soup = BeautifulSoup(response.content, 'html.parser')

            tables = soup.find_all('table')

            courses = []
            for table in tables[1:]:
                rows = table.find_all('tr')
                university = ""
                info = ""
                for row in rows:
                    cols = row.find_all('td')
                    if (len(cols) > 0):
                        text_col_0 = cols[0].text
                        if (text_col_0 == '№'):
                            university = cols[1].text.replace(
                                "\xa0", " ").rstrip()
                        elif (text_col_0.rstrip().isdigit() == False):
                            university = cols[0].text.replace(
                                "\xa0", " ").rstrip()
                        elif (text_col_0.rstrip().isdigit() == True):
                            name_and_date = str(cols[1]).split('<br/>')
                            date = ""
                            if (len(name_and_date) == 1):
                                end_index = name_and_date[0].find("</")
                                start_index = name_and_date[0].find("p>")
                                name = name_and_date[0][start_index + 2:end_index]
                            elif (len(name_and_date) == 2):
                                end_index = name_and_date[0].rfind(">")
                                name = name_and_date[0][end_index + 1:]
                                start_index = name_and_date[1].find("<")
                                date = name_and_date[1][:start_index]
                            if (len(cols) == 3):
                                info = cols[2].text.replace("\xa0", " ")

                            split_university = university.split()
                            if split_university[0] == "Курсы" or split_university[0] == "курсы":
                                university = " ".join(split_university[1:])
                            course = InfoOnlineCourse(
                                name=name, date_start=date, deadline=None, university=university, info=info)

                            res = worker_db.info_online_course.update_one(
                                course, upsert=True, name=course.name, university=course.university
                            )
        except Exception as e:
            print(e)
            update_status_history(hist, text_status="Error parse site urfu")
        return {"status": "success"}


def upload_report(file: UploadFile, worker_db: WorkerDataBase, hist: HistoryUploadFileInDB) -> dict[str, str]:
    try:
        excel = pd.ExcelFile(file.file.read())
    except Exception as e:
        print(e)
        update_status_history(
            hist, text_status="File read error. Please upload again")
        raise HTTPException(status_code=500, detail="File read error")

    try:
        worker_db.student.get_collect().update_many(
            {"status": True}, {"$set": {"online_course": []}})
        students = parse_students(excel, worker_db)
    except Exception as e:
        print(e)
        update_status_history(
            hist, text_status="Error parse data file. Use template file")
        raise HTTPException(status_code=500, detail="Error parse data file")

    try:
        update_collection(students, worker_db)
    except Exception as e:
        print(e)
        update_status_history(hist, text_status="Error update data")
        raise HTTPException(status_code=500, detail="Error update data")

    return {"status": "success"}


def parse_students(excel: pd.ExcelFile, worker_db: WorkerDataBase):
    all_students = {}

    for sheet_name in excel.sheet_names[1:]:
        df = excel.parse(sheet_name)

        df = df[df["Группа"].apply(lambda x: "РИ-" in x)]

        fill_file_online_course_info(df, worker_db)

        fill_in_students_from_one_sheet(df, all_students, worker_db)

    return all_students.values()


def fill_file_online_course_info(df: pd.DataFrame, worker_db: WorkerDataBase):
    cols_course = df.columns[5:11]
    file_course_info = df[cols_course].drop_duplicates()

    cols = file_course_info.columns

    for index, row in file_course_info.iterrows():
        platform = row[cols[0]]
        university = row[cols[1]]
        name_subject = row[cols[2]]
        form_edu = row[cols[4]]
        name = row[cols[5]]

        onl_course = InfoOCInFile(
            name=name,
            name_subject=name_subject,
            platform=platform,
            university=university,
            form_edu=form_edu
        )

        worker_db.onl_cr_in_file.update_one(onl_course, upsert=True, dict_keys={
            "name": onl_course.name,
            "name_subject": onl_course.name_subject
        })


def fill_in_students_from_one_sheet(df: pd.DataFrame, all_students: dict, worker_db: WorkerDataBase):
    cols_fill_name = df.columns[:3]
    col_email = df.columns[4]
    col_name_course = df.columns[10]
    col_university = df.columns[6]
    cols_scores = df.columns[11:]
    col_group = df.columns[3]

    for index, row in df.iterrows():
        email = row[col_email]

        course = get_info_online_course(
            row, col_name_course, col_university, cols_scores, worker_db)

        if email not in all_students.keys():
            all_students[email] = create_student_for_dict(
                row, cols_fill_name, col_group, email, course)
        else:
            all_students[email]["courses"].append(course.model_dump())


def get_info_online_course(row, col_name_course: str, col_university: str, cols_scores: str, worker_db: WorkerDataBase) -> InfoOnlineCourseInStudent:
    name_course = row[col_name_course]
    university = row[col_university]
    scores = {}
    for col_score in cols_scores:
        scores[col_score] = row[col_score]

    file_course = worker_db.onl_cr_in_file.get_one(
        name=name_course, get_none=True)

    info_course = None
    dict_name = worker_db.dict_names.get_one(
        get_none=True, file_course=name_course)

    if dict_name != None:
        info_course = worker_db.info_online_course.get_one(
            get_none=True, name=dict_name.site_inf)
    else:
        info_course = worker_db.info_online_course.get_one(get_none=True, find_dict={
                                                           "name": name_course, "university": {"$regex": university}})

    if info_course == None:
        info_course = create_default_info_course_in_db(
            name_course, university, worker_db)

    info_course.name = name_course
    course = create_course_in_student(info_course, file_course, scores)

    return course


def create_default_info_course_in_db(name: str, university: str, worker_db: WorkerDataBase) -> InfoOnlineCourse:
    online_course = InfoOnlineCourse(name=name, university=university)
    return online_course


def create_course_in_student(info_course: InfoOnlineCourse, file_course: InfoOCInFileInDB, scores: dict) -> InfoOnlineCourseInStudent:
    if file_course != None:
        if info_course.info != None:
            info_course.info = f"Предмет: {file_course.name_subject}, платформа: {file_course.platform}, форма обучения: {file_course.form_edu}. Дополнительная информация: {info_course.info}"
        else:
            info_course.info = f"Предмет: {file_course.name_subject}, платформа: {file_course.platform}, форма обучения: {file_course.form_edu}"

    dict = info_course.model_dump(by_alias=True, exclude="_id")
    return InfoOnlineCourseInStudent(**dict, scores=scores)


def create_student_for_dict(row, cols_full_name, col_group, email, course: InfoOnlineCourseInStudent) -> dict[str, any]:
    return {
        "surname": str(row[cols_full_name[0]]).strip(),
        "name": str(row[cols_full_name[1]]).strip(),
        "patronymic": None if str(row[cols_full_name[2]]) == 'nan' else str(row[cols_full_name[2]]).strip(),
        "email": email,
        "group": row[col_group],
        "courses": [course.model_dump()]
    }


def update_collection(students: list, worker_db: WorkerDataBase):
    for student in students:
        student_in_db = worker_db.student.update_one(dict_keys={
            "name": student["name"],
            "surname": student["surname"],
            "patronymic": student["patronymic"],
            "group.number": student["group"]
        },
            update_data={
            "$set":
            {"email": student["email"],
                "online_course": student["courses"]}
        },
            get_item=False)


def update_info_from_inf(worked_db: WorkerDataBase):
    cl_st = worked_db.student.get_collect()
    courses = worked_db.info_online_course.get_all(limit=-1)

    for course in courses:
        dict_names = worked_db.dict_names.get_one(
            get_none=True, site_inf=course.name)

        find_name = course.name
        find_university = course.university
        info = course.info

        if dict_names != None:
            file_course = worked_db.onl_cr_in_file.get_one(
                name=dict_names.file_course, get_none=True)

            if file_course != None:
                find_name = file_course.name
                find_university = file_course.university
                info = f"Предмет: {file_course.name_subject}, платформа: {file_course.platform}, форма обучения: {file_course.form_edu}. Дополнительная информация: {course.info}"

        cl_st.update_many({
            "online_course.name": find_name,
            "online_course.university": find_university
        },
            {
                "$set": {
                    "online_course.$.date_start": course.date_start,
                    "online_course.$.deadline": course.deadline,
                    "online_course.$.info": info
                }
        })
