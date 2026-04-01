import uuid
import pandas as pd
import numpy as np
from typing import Dict, Optional, Any, List
from datetime import datetime


def replace_nan_in_dict(obj):
    """递归替换字典中的NaN值为None"""
    if isinstance(obj, dict):
        return {k: replace_nan_in_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan_in_dict(item) for item in obj]
    elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    else:
        return obj

# 内存存储会话数据（键为session_id，值为会话信息）
sessions: Dict[str, Dict[str, Any]] = {}

def create_session(dataframe: pd.DataFrame, filename: str, sql_content: Optional[str] = None, sql_result: Optional[Dict[str, Any]] = None, columns: Optional[List[Dict[str, str]]] = None) -> str:
    """创建新会话，返回session_id"""
    session_id = str(uuid.uuid4())
    
    # 如果传入了自定义columns，使用传入的；否则从dataframe构建
    if columns:
        session_columns = columns
    else:
        session_columns = [
            {"name": col, "type": str(dataframe[col].dtype)}
            for col in dataframe.columns
        ]
    
    # 处理预览数据，确保没有NaN值
    preview_data = dataframe.head(5).to_dict(orient="records")
    preview_data = replace_nan_in_dict(preview_data)
    
    sessions[session_id] = {
        "dataframe": dataframe,
        "filename": filename,
        "preview": preview_data,
        "columns": session_columns,
        "row_count": len(dataframe),
        "created_at": datetime.now().isoformat(),
        "history": [],  # 新增：存储对话历史
        "sql_content": sql_content,  # 新增：存储SQL内容
        "sql_result": sql_result  # 新增：存储SQL执行结果
    }
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """获取会话数据"""
    return sessions.get(session_id)

def update_session_dataframe(session_id: str, dataframe: pd.DataFrame) -> bool:
    """更新会话中的DataFrame（如清洗后）"""
    if session_id not in sessions:
        return False
    # 处理预览数据，确保没有NaN值
    preview_data = dataframe.head(5).to_dict(orient="records")
    preview_data = replace_nan_in_dict(preview_data)
    
    sessions[session_id]["dataframe"] = dataframe
    sessions[session_id]["preview"] = preview_data
    sessions[session_id]["row_count"] = len(dataframe)
    return True

def add_history(session_id: str, role: str, content: str, metadata: dict = None):
    """添加一条历史记录到会话内存中"""
    if session_id in sessions:
        sessions[session_id]["history"].append({
            "role": role,  # "user" 或 "assistant"
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })
        return True
    return False

def delete_session(session_id: str) -> bool:
    """删除会话（释放内存）"""
    if session_id in sessions:
        del sessions[session_id]
        return True
    return False