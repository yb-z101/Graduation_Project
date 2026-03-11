#数据库连接配置（SQLAlchemy）
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base  # 关键：从orm导入declarative_base
from app.core.config import settings

# 创建引擎（连接MySQL）
engine = create_engine(settings.database_url, echo=True)  # echo=True会打印SQL，方便调试
# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 基础模型类（后续ORM模型继承这个）
Base = declarative_base()

# 依赖函数：获取数据库会话（FastAPI接口中用）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()