from fastapi import APIRouter

from database.worker_db import worker_db
from schemas.schemas import SubjectInDB


router_subject = APIRouter(
    prefix="/subject",
    tags=["Subject"],
)


@router_subject.get("/all")
async def get_subjects(limit: int = None) -> list[SubjectInDB]:
    return worker_db.subject.get_all(limit=limit)


@router_subject.get("/names")
async def get_subject_names() -> list[str]:
    return worker_db.subject.get_collect().distinct("full_name")


@router_subject.get("/")
async def get_subject_by_full_name(full_name: str, team: str = None) -> SubjectInDB:
    subject = worker_db.subject.get_one(find_dict={"full_name": full_name})

    find_teams = []
    if team != None:
        for _team in subject.teams:
            if _team.name == team:
                find_teams.append(_team)
        subject.teams = find_teams

    return subject


@router_subject.get("/{id}")
async def get_subject_by_id(id: str) -> SubjectInDB:
    return worker_db.subject.get_one(id=id)


# @router_subject.post("/add_group_tg")
# async def add_group_tg(full_name: str, link: str) -> dict:
#     worker_db.subject.update_one(get_item=False, update_data = {"$set" : {"group_tg_link" : link}}, full_name = full_name)

    # return {"status" : "success"}
