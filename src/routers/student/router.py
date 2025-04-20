from fastapi import APIRouter

from config import worker_db
from schemas import InfoOnlineCourseInStudent, StudentInDB


router_user = APIRouter(
    prefix="/student",
    tags=["Student"],
)


@router_user.get("/all")
async def get_student(limit: int = None) -> list[StudentInDB]:
    if limit is None:
        limit = -1
    return worker_db.student.get_all(limit=limit, status=True)


@router_user.get("/number_groups")
async def get_number_group_student() -> list[str]:
    return worker_db.student.get_collect().distinct("group.number")


@router_user.get("/{id}")
async def get_courses(id: str) -> StudentInDB:
    return worker_db.student.get_one(id=id)


@router_user.get("/{id}/courses")
async def get_courses(id: str) -> list[InfoOnlineCourseInStudent]:
    return worker_db.student.get_one(id=id).online_course


@router_user.get("/")
async def get_student(email: str) -> StudentInDB:
    return worker_db.student.get_one(email=email)
