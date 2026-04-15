from fastapi import APIRouter
from app.api.v1 import api_v1_router
from app.api.export_routes import router as export_router

# 创建API主路由
api_router = APIRouter()

# 注册v1版本路由
api_router.include_router(api_v1_router, prefix="/v1")

# 注册导出路由（PDF等）
api_router.include_router(export_router)
