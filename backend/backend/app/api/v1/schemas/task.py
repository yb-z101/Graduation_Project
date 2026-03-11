from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List  # 新增List，适配后续列表接口
from typing import Optional, Dict, Any, List


# 创建分析任务的请求模型
class TaskCreate(BaseModel):
    task_name: str  # 分析任务名称（用户自定义）
    source_id: int  # 关联的数据源ID（关联data_source表主键）
    user_prompt: str  # 用户自然语言分析提问

    # 参数校验（毕设健壮性亮点）
    @validator("task_name")
    def validate_task_name(cls, v):
        if len(v) < 2 or len(v) > 200:
            raise ValueError("任务名称长度必须在2-200字符之间")
        return v.strip()

    @validator("user_prompt")
    def validate_prompt(cls, v):
        if len(v) < 5 or len(v) > 1000:
            raise ValueError("提问内容长度必须在5-1000字符之间")
        return v.strip()

# 新增：创建任务+密码的请求体模型（核心修复）
class TaskCreateWithPassword(BaseModel):
    task: TaskCreate  # 原有任务信息
    plain_password: str  # 数据源明文密码（仅临时使用，不存储）

# 分析任务响应模型（脱敏，不返回敏感信息）
class TaskResponse(BaseModel):
    id: int  # 任务主键ID
    task_name: str  # 任务名称
    source_id: Optional[int]  # 关联数据源ID
    user_prompt: str  # 用户提问内容
    generated_sql: Optional[str]  # 大模型生成的SQL语句
    llm_analysis: Optional[str]  # 大模型生成的分析结论
    task_status: int  # 任务状态：0-待执行 1-执行中 2-成功 3-失败
    create_time: str  # 创建时间（格式化字符串）

    class Config:
        from_attributes = True  # Pydantic V2兼容ORM模型转换

# SQL执行结果模型（用于单独返回SQL执行状态）
class SQLResult(BaseModel):
    success: bool  # 执行是否成功
    data: Optional[list] = None  # 执行成功返回的数据
    error: Optional[str] = None  # 执行失败返回的错误信息


class SessionTaskResponse(TaskResponse):
    chart_option: Optional[Dict[str, Any]] = None
    data: Optional[List[Dict[str, Any]]] = None