import uuid
import pandas as pd
import numpy as np
import math
from typing import Dict, Optional, Any, List
from datetime import datetime

sessions: Dict[str, Dict[str, Any]] = {}


def _sanitize_value(val):
    try:
        if val is pd.NA:
            return None
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
        if isinstance(val, (pd.Timestamp,)):
            return val.isoformat() if not pd.isna(val) else None
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return val


def _sanitize_preview(preview_data):
    for record in preview_data:
        for key, value in record.items():
            record[key] = _sanitize_value(value)
    return preview_data


def create_session(dataframe: pd.DataFrame, filename: str, sql_content: Optional[str] = None, sql_result: Optional[Dict[str, Any]] = None) -> str:
    session_id = str(uuid.uuid4())
    preview = _sanitize_preview(dataframe.head(5).to_dict(orient="records"))
    sessions[session_id] = {
        "dataframe": dataframe,
        "filename": filename,
        "preview": preview,
        "columns": [
            {"name": col, "type": str(dataframe[col].dtype)}
            for col in dataframe.columns
        ],
        "row_count": len(dataframe),
        "created_at": datetime.now().isoformat(),
        "history": [],
        "sql_content": sql_content,
        "sql_result": sql_result
    }
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """获取会话数据"""
    return sessions.get(session_id)

def update_session_dataframe(session_id: str, dataframe: pd.DataFrame) -> bool:
    if session_id not in sessions:
        return False
    preview = _sanitize_preview(dataframe.head(5).to_dict(orient="records"))
    sessions[session_id]["dataframe"] = dataframe
    sessions[session_id]["preview"] = preview
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