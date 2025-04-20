from fastapi import APIRouter

from config import worker_db
from routers.online_course.dict_names import add_dict_names, update_dict_names, delete_dict_names
from schemas import DictNames, DictNamesInDB, InfoOCInFile, InfoOCInFileInDB, InfoOnlineCourseInDB


router_course = APIRouter(
    prefix="/course",
    tags=["Course"],
)


@router_course.get("/in_file")
async def get_courses_in_file() -> list[InfoOCInFileInDB]:
    return worker_db.onl_cr_in_file.get_all(limit=-1)


@router_course.get("/in_file/names")
async def get_courses_in_file() -> list[str]:
    cl_oc = worker_db.onl_cr_in_file.get_collect()

    return cl_oc.find().distinct("name")


@router_course.get("/search")
async def get_courses(name: str, university: str | None = None) -> InfoOnlineCourseInDB:
    collection = worker_db.info_online_course.get_collect()
    query = {"name": {"$regex": name, "$options": "i"}}
    if university:
        query["university"] = {"$regex": university, "$options": "i"}
    course = collection.find_one(query)
    return InfoOnlineCourseInDB(**course)


@router_course.get("/names")
async def get_names() -> list[str]:
    return worker_db.info_online_course.get_collect().distinct("name")


@router_course.post("/dict_names")
async def post_dict_modeus_inf(modeus: str = None, site_inf: str = None, file_course: str = None) -> DictNamesInDB:
    return add_dict_names(modeus, site_inf, file_course, worker_db)


@router_course.get("/dict_names")
async def get_list_modeus_to_inf(limit: int = None) -> list[DictNamesInDB]:
    if limit == None:
        limit = -1
    return worker_db.dict_names.get_all(limit=limit)


@router_course.put("/dict_names")
async def put_list_modeus_to_inf(dict: list[DictNamesInDB | DictNames]) -> list[DictNamesInDB]:
    res = []
    for d in dict:
        dict_db = update_dict_names(dict, worker_db, upsert=True)
        res.append(dict_db)
    return res


@router_course.get("/dict_names/names")
async def get_modeus_to_inf_names(modeus: str = None, site_inf: str = None, file_course: str = None) -> DictNamesInDB:
    req = {}
    if modeus != None:
        req["modeus"] = modeus
    if site_inf != None:
        req["site_inf"] = site_inf
    if file_course != None:
        req["file_course"] = file_course

    return worker_db.dict_names.get_one(find_dict=req)


@router_course.get("/dict_names/{id}")
async def get_modeus_to_inf_one(id: str) -> DictNamesInDB:
    return worker_db.dict_names.get_one(id=id)


@router_course.put("/dict_names/one")
async def put_modeus_to_inf(dict: DictNamesInDB) -> DictNamesInDB:
    return update_dict_names(dict, worker_db)


@router_course.delete("/dict_names/{id}")
async def delete_modeus_to_inf(id: str) -> dict[str, str]:
    dict = worker_db.dict_names.get_one(id=id)
    return delete_dict_names(dict, worker_db)
