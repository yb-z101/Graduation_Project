from pydantic import BaseModel, validator
from typing import Optional

# 新增数据源的请求体模型（毕设体现“接口参数校验”）
class DataSourceCreate(BaseModel):
    source_name: str
    source_type: int  # 1-MySQL 2-PostgreSQL 3-SQLite
    host: str
    port: int
    db_name: str
    username: str
    plain_password: str  # 前端传入的明文密码，后端加密存储

    # 自定义参数校验（毕设“健壮性”亮点）
    @validator("source_type")
    def validate_source_type(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError("数据源类型只能是1(MySQL)/2(PostgreSQL)/3(SQLite)")
        return v

    @validator("port")
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError("端口号必须在1-65535之间")
        return v

    @validator("source_name")
    def validate_source_name(cls, v):
        if len(v) < 2 or len(v) > 100:
            raise ValueError("数据源名称长度必须在2-100字符之间")
        return v.strip()

# 数据源列表查询的响应模型（脱敏，不返回密码）
class DataSourceResponse(BaseModel):
    id: int
    source_name: str
    source_type: int
    host: str
    port: int
    db_name: str
    username: str
    create_time: str  # 格式化后的时间

    class Config:
        from_attributes = True  # 支持从ORM模型直接转换