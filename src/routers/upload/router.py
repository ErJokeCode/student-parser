from datetime import datetime
import asyncio
import io
import shutil
from tempfile import SpooledTemporaryFile
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from config import worker_db
from database.core_s3 import s3_client
from worker import update_status_history
from routers.upload.online_course import parse_info_online_courses, update_info_from_inf, upload_report
from schemas import HistoryUploadFile, HistoryUploadFileInDB, TypeFile

from routers.upload.student import upload_student
from routers.upload.modeus import upload_modeus


router_data = APIRouter(
    prefix="/upload",
    tags=["Upload Files"],
)


@router_data.post("/student")
async def upload_data_student(file: UploadFile) -> dict[str, str]:
    hist = await get_history()
    if hist and hist[0].status_upload is None:
        raise HTTPException(
            status_code=400, detail=f"Wait for the {hist[0].name_file} file to be processed")

    hist_info = await s3_client.create_hist_file(file, TypeFile.student, is_upload=False)
    hist_info_db = worker_db.history.insert_one(hist_info)

    contents = await file.read()
    file_copy = UploadFile(
        filename=file.filename,
        file=io.BytesIO(contents),
        headers=file.headers,
        size=file.size
    )

    asyncio.create_task(background_student(file_copy, hist_info_db))

    return {"status": "success"}


@router_data.get("/student/example")
async def get_example_file_student():
    return FileResponse(
        path="src/static/example/example_students.xls",
        filename="Студенты.xls",
        media_type="multipart/form-data")


@router_data.post("/choice_in_modeus")
async def post_choice_in_modeus(file: UploadFile) -> dict[str, str]:
    hist = await get_history(type=TypeFile.student)
    if len(hist) == 0:
        raise HTTPException(
            status_code=400, detail=f"First upload the file with students")

    hist = await get_history()
    if len(hist) == 1 and hist[0].status_upload is None:
        raise HTTPException(
            status_code=400, detail=f"Wait for the {hist[0].name_file} file to be processed")

    hist_info = await s3_client.create_hist_file(file, TypeFile.modeus, is_upload=False)
    hist_info_db = worker_db.history.insert_one(hist_info)

    contents = await file.read()
    file_copy = UploadFile(
        filename=file.filename,
        file=io.BytesIO(contents),
        headers=file.headers,
        size=file.size
    )

    asyncio.create_task(background_modeus(file_copy, hist_info_db))

    return {"status": "success"}


@router_data.get("/choice_in_modeus/example")
async def get_example_file_modeus():
    return FileResponse(
        path="src/static/example/example_modeus.xlsx",
        filename="Модеус.xlsx",
        media_type="multipart/form-data")


@router_data.post("/report_online_course")
async def post_online_course_report(file: UploadFile) -> dict[str, str]:
    hist = await get_history(type=TypeFile.student)
    if len(hist) == 0:
        raise HTTPException(
            status_code=400, detail=f"First upload the file with students")

    hist = await get_history(type=TypeFile.modeus)
    if len(hist) == 0:
        raise HTTPException(
            status_code=400, detail=f"First upload the file with modeus")

    hist = await get_history()
    if len(hist) == 1 and hist[0].status_upload is None:
        raise HTTPException(
            status_code=400, detail=f"Wait for the {hist[0].name_file} file to be processed")

    hist_info = await s3_client.create_hist_file(file, TypeFile.online_course, is_upload=False)
    hist_info_db = worker_db.history.insert_one(hist_info)

    contents = await file.read()
    file_copy = UploadFile(
        filename=file.filename,
        file=io.BytesIO(contents),
        headers=file.headers,
        size=file.size
    )

    asyncio.create_task(background_online_course(file_copy, hist_info_db))

    return {"status": "success"}


@router_data.get("/report_online_course/example")
async def get_example_file_online_course():
    return FileResponse(
        path="src/static/example/example_online_course.xlsx",
        filename="ОнлайнКурсы.xlsx",
        media_type="multipart/form-data")


@router_data.post("/report_online_course/site_inf")
async def update_online_course_inf():
    hist = await get_history()
    if len(hist) == 1 and hist[0].status_upload is None:
        raise HTTPException(
            status_code=400, detail=f"Wait for the {hist[0].name_file} file to be processed")

    hist_info = HistoryUploadFile(
        name_file="Обновление информации с сайта",
        key="",
        date=datetime.now(),
        type=TypeFile.site_inf,
    )
    hist = worker_db.history.insert_one(hist_info)

    asyncio.create_task(background_site_inf(hist))

    return {"status": "success"}


@router_data.get("/history")
async def get_history(limit: int = 1, type: TypeFile | None = None) -> list[HistoryUploadFileInDB]:

    try:
        collect = worker_db.history.get_collect()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error collection")

    query = {}
    if type:
        query["type"] = type

    history = []
    i = 0
    for hist in collect.find(query).sort("date", -1):
        history.append(HistoryUploadFileInDB(**hist))
        i += 1
        if i == limit:
            break

    return history


@router_data.get("/history/file/{file_key}")
async def get_file(file_key: str):
    info = worker_db.history.get_one(find_dict={"key": file_key})

    if info is None:
        raise HTTPException(status_code=404, detail="File not found")

    return StreamingResponse(
        content=s3_client.get_file_read(file_key),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={info.name_file}"}
    )


async def save_file_to_s3(file: UploadFile, hist_info_db: HistoryUploadFileInDB):
    try:
        link = await s3_client.upload_file(hist_info_db.key, file)
    except Exception as e:
        print(e)
        update_status_history(
            hist_info_db, text_status="Error save file to S3")

    hist_info_db.link = link
    worker_db.history.update_one(hist_info_db, get_item=False)

    return hist_info_db


async def background_student(file: UploadFile, hist_info_db: HistoryUploadFileInDB):
    await upload_student(file, worker_db, hist_info_db)

    try:
        update_status_history(hist_info_db, text_status="Success")
    except Exception as e:
        print(e)


async def background_modeus(file: UploadFile, hist_info_db: HistoryUploadFileInDB):
    upload_modeus(file, hist_info_db, worker_db)

    try:
        update_status_history(hist_info_db, text_status="Success")
    except Exception as e:
        print(e)


async def background_online_course(file: UploadFile, hist_info_db: HistoryUploadFileInDB):
    parse_info_online_courses(worker_db, hist_info_db)
    upload_report(file, worker_db, hist_info_db)

    try:
        update_status_history(hist_info_db, text_status="Success")
    except Exception as e:
        print(e)


async def background_site_inf(hist: HistoryUploadFileInDB):
    try:
        parse_info_online_courses(worker_db, hist)
        update_info_from_inf(worker_db)
        try:
            update_status_history(hist, text_status="Success")
        except Exception as e:
            print(e)
    except Exception as e:
        update_status_history(hist, text_status="Error update info from inf")
        print(e)
