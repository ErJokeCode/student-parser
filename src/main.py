from contextlib import asynccontextmanager
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.upload.router import router_data
from routers.student.router import router_user
from routers.online_course.router import router_course
from routers.subject.router import router_subject
from routers.bot.router_onboard import router_bot_onboard
from routers.bot.router_faq import router_bot_faq

_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log.info("Start server")
    yield
    _log.info("Stop server")


app = FastAPI(
    openapi_url=f"/openapi.json",
    docs_url=f"/docs",
    redoc_url=f"/redoc",
    root_path="/parser"
)

origins = [
    settings.URLS_CORS
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def ping():
    return "ok"

app.include_router(router_data)
app.include_router(router_user)
app.include_router(router_course)
app.include_router(router_subject)
app.include_router(router_bot_onboard)
app.include_router(router_bot_faq)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=5)
