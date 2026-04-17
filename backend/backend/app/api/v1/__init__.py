from fastapi import APIRouter
from app.api.v1.upload import router as upload_router
from app.api.v1.session import router as session_router
from app.api.v1.chat import router as chat_router
from app.api.v1.analysis_task import router as analysis_task_router
from app.api.v1.datasource import router as datasource_router
from app.api.v1.preview import router as preview_router
from app.api.v1.database import router as database_router
from app.api.v1.audit import router as audit_router

# 创建主路由
api_v1_router = APIRouter()

# 注册子路由
api_v1_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_v1_router.include_router(session_router, prefix="/session", tags=["session"])
api_v1_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_v1_router.include_router(analysis_task_router, prefix="/analysis-task", tags=["analysis-task"])
api_v1_router.include_router(datasource_router, prefix="/datasource", tags=["datasource"])
api_v1_router.include_router(preview_router, prefix="/preview", tags=["preview"])
api_v1_router.include_router(database_router, prefix="/database", tags=["database"])
api_v1_router.include_router(audit_router, prefix="/audit", tags=["audit"])
