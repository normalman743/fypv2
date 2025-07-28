from fastapi import APIRouter
from app.api.v1 import auth, semesters, courses, folders, files

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(semesters.router, prefix="/semesters")
api_router.include_router(courses.router, prefix="/courses")
api_router.include_router(folders.router)  # No prefix as it has nested routes
api_router.include_router(files.router)    # No prefix as it has nested routes