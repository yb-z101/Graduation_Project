from fastapi import APIRouter
from app.api.v1 import api_v1_router
from app.api.export_routes import router as export_router

api_router = APIRouter()

api_router.include_router(api_v1_router, prefix="/v1")

api_router.include_router(export_router, prefix="/v1")
