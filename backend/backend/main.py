# 原有导入 + 新增建表相关导入
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
# 新增：建表相关导入（核心）
from app.core.database import Base, engine
from app.models.models import DataSource, AnalysisTask, ChatRecord, RAGIndex, Session as UploadSession
# 原有导入（保留）
from app.core.database import get_db
from app.utils.llm_client import test_qwen_api
from app.core.config import settings


# 原有FastAPI实例创建（保留，标题可优化）
app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    docs_url="/docs",
    swagger_ui_init_oauth={
        "use_local_assets": True  # 关键：使用本地Swagger资源，不依赖CDN
    }
)

# 启动时自动建表（开发/答辩演示用）
# 说明：如果你后续接入 Alembic 迁移，可替换为迁移脚本；create_all 重复执行是安全的（只会补缺失表）。
@app.on_event("startup")
def _create_tables_on_startup():
    Base.metadata.create_all(bind=engine)

# 使用配置文件中的 CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,     # 仅允许配置的前端地址跨域
    allow_credentials=True,    # 允许前端携带Cookie/Token（本地调试常用）
    allow_methods=["*"],       # 允许所有HTTP方法（GET/POST等）
    allow_headers=["*"],       # 允许所有请求头（如Content-Type、Authorization）
    expose_headers=["*"],      # 暴露所有响应头
    max_age=86400,             # 预检请求的缓存时间
)

# 注册API路由
from app.api import api_router
app.include_router(api_router, prefix="/api")

# 原有健康检查接口（保留，优化提示语）
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "系统启动成功，数据库表已创建（若首次执行）"}

# 原有数据库测试接口（保留，已修复text()语法）
@app.get("/db/test")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "数据库连接成功"}
    except Exception as e:
        return {"status": "error", "message": f"数据库连接失败：{str(e)}"}

# 原有大模型测试接口（保留，已修复API调用逻辑）
@app.get("/llm/test")
def test_llm(prompt: str = "你好，请介绍一下自己"):
    result = test_qwen_api(prompt)
    return {"status": "ok", "response": result}

from app.core.session_manager import sessions

@app.get("/debug/sessions")
def debug_sessions():
    """返回所有会话的元信息（仅用于调试）"""
    return {
        sid: {
            "filename": info["filename"],
            "row_count": info["row_count"],
            "columns": info["columns"],
            "created_at": info["created_at"]
        }
        for sid, info in sessions.items()
    }