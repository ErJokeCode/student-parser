from bson import ObjectId
from fastapi import APIRouter, HTTPException

from database.worker_db import worker_db
from schemas.schemas import FAQ, FAQTopic, FAQTopicInDB


router_bot_faq = APIRouter(
    prefix="/bot/faq",
    tags=["Bot FAQ"],
)


@router_bot_faq.post("/")
async def add_new_topic(name_topic: str) -> FAQTopicInDB:
    if worker_db.bot_faq.get_one(name=name_topic, get_none=True) != None:
        raise HTTPException(status_code=404, detail="Topic already exists")
    return worker_db.bot_faq.insert_one(FAQTopic(name=name_topic))


@router_bot_faq.get("/")
async def get_all_topics() -> list[FAQTopicInDB]:
    return worker_db.bot_faq.get_all(limit=-1)


@router_bot_faq.get("/{id_topic}")
async def get_faq(id_topic: str) -> FAQTopicInDB:
    return worker_db.bot_faq.get_one(id=id_topic)


@router_bot_faq.post("/{id_topic}")
async def add_faq(id_topic: str, faq: FAQ) -> FAQTopicInDB:
    cl_faq = worker_db.bot_faq.get_collect()

    cl_faq.update_one({"_id": ObjectId(id_topic)}, {
                      "$push": {"faqs": faq.model_dump()}})
    res = cl_faq.find_one({"_id": ObjectId(id_topic)})

    return FAQTopicInDB(**res)


@router_bot_faq.put("/{id_topic}")
async def update_topic(id_topic: str, topic: FAQTopic | FAQTopicInDB) -> FAQTopicInDB:
    if isinstance(topic, FAQTopic):
        topic_db = FAQTopicInDB(**topic.model_dump(), _id=ObjectId(id_topic))
        topic = topic_db
    return worker_db.bot_faq.update_one(topic)


@router_bot_faq.delete("/{id_topic}")
async def delete_topic(id_topic: str) -> dict[str, str]:
    return worker_db.bot_faq.delete_one(id=id_topic)
