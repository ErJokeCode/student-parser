import requests
from config import settings
from database.worker_db import worker_db
from schemas.schemas import HistoryUploadFileInDB


def update_status_history(hist_info_db: HistoryUploadFileInDB, text_status: str):
    hist_info_db.status_upload = text_status
    worker_db.history.update_one(hist_info_db, get_item=False)

    headers = {"Authorization": f"Basic {settings.CORE_SERVER_SECRET_TOKEN}"}
    url = settings.URL_CORE_SERVER + "/core/events/upload"

    session = requests.Session()
    response = session.post(url, headers=headers)

    if response.status_code != 200:
        print(response.status_code)
