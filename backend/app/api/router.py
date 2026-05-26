from fastapi import APIRouter

from app.api.tasks import router as tasks_router
from app.api.library import router as library_router
from app.api.files import router as files_router

api_router = APIRouter()
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(library_router, prefix="/library", tags=["library"])
api_router.include_router(files_router, prefix="/files", tags=["files"])
