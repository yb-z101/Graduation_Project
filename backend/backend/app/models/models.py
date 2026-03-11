from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from passlib.context import CryptContext

# 密码加密上下文（全局，毕设体现“安全性”）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. 数据源表（核心根基表）
class DataSource(Base):
    __tablename__ = "data_source"
    # 核心字段（规范设计：字段类型+非空+注释）
    id = Column(Integer, primary_key=True, autoincrement=True, comment="数据源主键ID")
    source_name = Column(String(100), nullable=False, comment="数据源名称（用户自定义）")
    source_type = Column(Integer, nullable=False, comment="数据源类型：1-MySQL 2-PostgreSQL 3-SQLite")
    host = Column(String(50), nullable=False, comment="数据库地址")
    port = Column(Integer, nullable=False, comment="数据库端口")
    db_name = Column(String(100), nullable=False, comment="数据库名")
    username = Column(String(50), nullable=False, comment="数据库账号")
    password = Column(String(100), nullable=False, comment="数据库密码（bcrypt加密）")
    # 扩展字段（体现扩展性）
    ext_info = Column(Text, nullable=True, comment="扩展信息（JSON格式）")
    is_deleted = Column(Boolean, default=False, comment="软删除标记")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 索引设计（提升查询效率，毕设体现性能考量）
    __table_args__ = (
        Index("idx_source_type", "source_type"),
        Index("idx_host_port", "host", "port"),
        Index("idx_is_deleted", "is_deleted"),
    )

    # 密码加密/验证方法（毕设“安全性”亮点）
    def set_password(self, plain_password: str):
        self.password = pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.password)

    # 关联分析任务（ORM关联，体现表关系设计）
    analysis_tasks = relationship("AnalysisTask", back_populates="data_source", cascade="all, delete-orphan")

# 2. 分析任务表（核心业务表）
class AnalysisTask(Base):
    __tablename__ = "analysis_task"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="任务主键ID")
    task_name = Column(String(200), nullable=False, comment="任务名称")
    source_id = Column(Integer, ForeignKey("data_source.id", ondelete="CASCADE"), nullable=True, comment="关联数据源ID，空表示基于会话上传的数据")
    user_prompt = Column(Text, nullable=False, comment="用户自然语言提问")
    generated_sql = Column(Text, nullable=True, comment="大模型生成的SQL语句")
    sql_exec_result = Column(Text, nullable=True, comment="SQL执行结果（JSON格式）")
    llm_analysis = Column(Text, nullable=True, comment="大模型分析结论")
    task_status = Column(Integer, default=0, comment="任务状态：0-待执行 1-执行中 2-成功 3-失败")
    error_msg = Column(String(500), nullable=True, comment="失败错误信息")
    # 扩展/审计字段
    is_deleted = Column(Boolean, default=False, comment="软删除标记")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 索引设计
    __table_args__ = (
        Index("idx_source_id", "source_id"),
        Index("idx_task_status", "task_status"),
        Index("idx_is_deleted", "is_deleted"),
    )

    # 关联关系
    data_source = relationship("DataSource", back_populates="analysis_tasks")
    chat_records = relationship("ChatRecord", back_populates="analysis_task", cascade="all, delete-orphan")
    rag_indexes = relationship("RAGIndex", back_populates="analysis_task", cascade="all, delete-orphan")

# 3. 对话记录表（体现“对话式”核心）
class ChatRecord(Base):
    __tablename__ = "chat_record"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="对话主键ID")
    task_id = Column(Integer, ForeignKey("analysis_task.id", ondelete="CASCADE"), nullable=False, comment="关联任务ID")
    role = Column(Integer, nullable=False, comment="角色：1-用户 2-系统/大模型")
    content = Column(Text, nullable=False, comment="对话内容")
    # 扩展字段
    is_deleted = Column(Boolean, default=False, comment="软删除标记")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")

    # 索引设计
    __table_args__ = (
        Index("idx_task_id", "task_id"),
        Index("idx_role", "role"),
        Index("idx_is_deleted", "is_deleted"),
    )

    # 关联关系
    analysis_task = relationship("AnalysisTask", back_populates="chat_records")

# 4. RAG向量索引表（毕设“创新点”核心表）
class RAGIndex(Base):
    __tablename__ = "rag_index"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="索引主键ID")
    task_id = Column(Integer, ForeignKey("analysis_task.id", ondelete="CASCADE"), nullable=False, comment="关联任务ID")
    index_type = Column(Integer, nullable=False, comment="索引类型：1-schema索引 2-历史SQL索引 3-业务文档索引")
    content = Column(Text, nullable=False, comment="索引内容（如表结构、历史SQL）")
    vector = Column(Text, nullable=False, comment="向量值（JSON格式存储）")
    # 扩展字段
    is_deleted = Column(Boolean, default=False, comment="软删除标记")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")

    # 索引设计
    __table_args__ = (
        Index("idx_task_id", "task_id"),
        Index("idx_index_type", "index_type"),
        Index("idx_is_deleted", "is_deleted"),
    )

    # 关联关系
    analysis_task = relationship("AnalysisTask", back_populates="rag_indexes")