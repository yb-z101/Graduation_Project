# 原有导入 + 新增建表相关导入
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
# 新增：建表相关导入（核心）
from app.core.database import Base, engine
from app.models.models import DataSource, AnalysisTask, ChatRecord, RAGIndex
# 原有导入（保留）
from app.core.database import get_db
from app.utils.llm_client import test_qwen_api
from app.api.v1.analysis_task import router as analysis_task_router
from app.api.v1.datasource import router as datasource_router
from app.api.v1.upload import router as upload_router
from app.api.v1.session import router as session_router
# 新增：首次启动创建所有表（执行一次即可，后续注释）
# 说明：这行代码只需要执行1次，表创建成功后，注释掉即可，避免重复建表
#Base.metadata.create_all(bind=engine)

# 原有FastAPI实例创建（保留，标题可优化）
app = FastAPI(
    title="对话式数据分析系统",
    version="1.0",
    docs_url="/docs",
    swagger_ui_init_oauth={
        "use_local_assets": True  # 关键：使用本地Swagger资源，不依赖CDN
    }
)
# 新增：添加跨域中间件（解决前端联调+docs加载问题）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 新增：注册数据源路由（核心）
app.include_router(datasource_router)
# 在已有路由注册后添加
app.include_router(upload_router)
app.include_router(analysis_task_router)
app.include_router(session_router)
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