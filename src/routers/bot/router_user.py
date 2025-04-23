from fastapi import APIRouter, HTTPException
from bson import ObjectId

from database.worker_db import worker_db
from kafka.core import producer_kafka
from schemas.kafka_task import KafkaTask, TypeTask
from schemas.schemas import StudentInDB

router_bot_onboard = APIRouter(
    prefix="/bot/user",
    tags=["Bot for user"],
)


@router_bot_onboard.post("/{id}")
async def add_user(id: str, chat_id: int | str) -> StudentInDB:
    return_data = worker_db.student.update_one(dict_keys={"_id": ObjectId(id)}, update_data={
        "$set": {"tg_chat_id": chat_id}})

    if return_data is None:
        raise HTTPException(status_code=404, detail="Not found student")

    producer_kafka.add_task(
        KafkaTask(id=str(id), type=TypeTask.UPDATE, collect="student"))

    return return_data
