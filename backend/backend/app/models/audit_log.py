from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "operation_audit_logs"

    id = Column(String(64), primary_key=True, comment="日志唯一ID")
    timestamp = Column(DateTime, default=func.now(), index=True, comment="操作时间")
    operation_type = Column(String(50), index=True, comment="操作类型代码")
    operation_name = Column(String(100), comment="操作类型名称")
    user_id = Column(String(100), index=True, comment="用户标识")
    session_id = Column(String(100), index=True, comment="会话ID")
    dataset_name = Column(String(255), comment="数据集名称")
    dataset_type = Column(String(20), comment="数据集类型: file/sql/database")
    query_content = Column(Text, comment="用户查询内容")
    query_hash = Column(String(32), index=True, comment="查询内容哈希")
    result_summary = Column(Text, comment="操作结果摘要")
    status = Column(String(20), index=True, comment="操作状态: success/failure/warning")
    error_message = Column(Text, comment="错误信息")
    ip_address = Column(String(45), comment="客户端IP地址")
    user_agent = Column(Text, comment="客户端User-Agent")
    extra_data = Column(Text, comment="额外数据(JSON)")
    sensitivity_level = Column(Integer, default=0, comment="敏感级别")
    server_hostname = Column(String(100), comment="服务器主机名")
