from fastapi import APIRouter
from app.api.v1 import api_v1_router

# 创建API主路由
api_router = APIRouter()

# 注册v1版本路由
api_router.include_router(api_v1_router, prefix="/v1")
