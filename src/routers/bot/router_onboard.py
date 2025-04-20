from bson import ObjectId
from fastapi import APIRouter, HTTPException

from config import worker_db
from schemas import OnboardCourse, OnboardCourseInDB, OnboardSection, OnboardTopic


router_bot_onboard = APIRouter(
    prefix="/bot/onboard",
    tags=["Bot onboard"],
)


@router_bot_onboard.post("/one_course")
async def add_course(course: OnboardCourse) -> OnboardCourseInDB:
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        id = collection_bot.insert_one(course.model_dump()).inserted_id
        return OnboardCourseInDB(**collection_bot.find_one({"_id": ObjectId(id)}))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Error add")


@router_bot_onboard.post("/{id}/section")
async def add_section(id: str, section: OnboardSection) -> OnboardCourseInDB:
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        collection_bot.update_one({"_id": ObjectId(id)},
                                  {"$push": {"sections": section.model_dump()}})
        return OnboardCourseInDB(**collection_bot.find_one({"_id": ObjectId(id)}))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Error add")


@router_bot_onboard.post("/{id}/{section_index}/topic")
async def add_topic(id: str, section_index: int, topic: OnboardTopic) -> OnboardCourseInDB:
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        course_db = OnboardCourseInDB(
            **collection_bot.find_one({"_id": ObjectId(id)}))
        section_topics = course_db.sections[section_index].topics
        section_topics.append(topic)
        collection_bot.update_one({"_id": ObjectId(id)},
                                  {"$set": course_db.model_dump()})

        return course_db
    except IndexError as index_error:
        print(index_error)
        raise HTTPException(status_code=404, detail="Index section error")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Error add")


@router_bot_onboard.put("/{id}")
async def put_course(id: str, course: OnboardCourse) -> OnboardCourseInDB:
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        collection_bot.update_one({"_id": ObjectId(id)},
                                  {"$set": course.model_dump()})
        return OnboardCourseInDB(**collection_bot.find_one({"_id": ObjectId(id)}))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Error update")


@router_bot_onboard.put("/{id}/{section_index}")
async def put_section(id: str, section_index: int, section: OnboardSection) -> OnboardCourseInDB:
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        course_db = OnboardCourseInDB(
            **collection_bot.find_one({"_id": ObjectId(id)}))
        course_db.sections[section_index] = section

        collection_bot.update_one({"_id": ObjectId(id)},
                                  {"$set": course_db.model_dump()})
        return course_db
    except IndexError as index_error:
        print(index_error)
        raise HTTPException(status_code=404, detail="Index section error")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Error update")


@router_bot_onboard.put("/{id}/{section_index}/{topic_index}")
async def put_topic(id: str, section_index: int, topic_index: int, topic: OnboardTopic) -> OnboardCourseInDB:
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        course_db = OnboardCourseInDB(
            **collection_bot.find_one({"_id": ObjectId(id)}))
        section = course_db.sections[section_index]
        section.topics[topic_index] = topic

        collection_bot.update_one({"_id": ObjectId(id)},
                                  {"$set": course_db.model_dump()})
        return course_db
    except IndexError as index_error:
        print(index_error)
        raise HTTPException(status_code=404, detail="Index error")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Error update")


@router_bot_onboard.delete("/{id}")
async def delete_course(id: str) -> dict:
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        collection_bot.delete_one({"_id": ObjectId(id)})
        return {"status": "success"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Error delete")


@router_bot_onboard.delete("/{id}/{section_index}")
async def delete_section(id: str, section_index: int) -> OnboardCourseInDB:
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        course_db = OnboardCourseInDB(
            **collection_bot.find_one({"_id": ObjectId(id)}))
        course_db.sections.pop(section_index)
        collection_bot.update_one({"_id": ObjectId(id)},
                                  {"$set": course_db.model_dump()})
        return course_db
    except IndexError as index_error:
        print(index_error)
        raise HTTPException(status_code=404, detail="Index section error")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Error delete")


@router_bot_onboard.delete("/{id}/{section_index}/{topic_index}")
async def delete_topic(id: str, section_index: int, topic_index: int) -> OnboardCourseInDB:
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        course_db = OnboardCourseInDB(
            **collection_bot.find_one({"_id": ObjectId(id)}))
        section = course_db.sections[section_index]
        section.topics.pop(topic_index)

        collection_bot.update_one({"_id": ObjectId(id)},
                                  {"$set": course_db.model_dump()})
        return course_db
    except IndexError as index_error:
        print(index_error)
        raise HTTPException(status_code=404, detail="Index error")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Error delete")


@router_bot_onboard.get("/{id}")
async def get_course(id: str) -> OnboardCourseInDB:
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        course = collection_bot.find_one({"_id": ObjectId(id)})
        return OnboardCourseInDB(**course)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Error get")


@router_bot_onboard.get("/")
async def get_courses(is_active: bool = None, is_main: bool = None) -> list[OnboardCourseInDB]:
    keys = {}
    if is_active is not None:
        keys["is_active"] = is_active
    if is_main is not None:
        keys["is_main"] = is_main
    try:
        collection_bot = worker_db.bot_onboard.get_collect()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error DB")
    try:
        courses = []
        for course in collection_bot.find(keys):
            courses.append(OnboardCourseInDB(**course))
        return courses
    except Exception as e:
        print(e)
