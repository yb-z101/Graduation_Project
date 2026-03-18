from typing import Optional

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.session_service import (
    get_session_messages,
    delete_one_session,
    clear_all_sessions,
    clean_session_data,
    send_message,
    get_session_history
)

router = APIRouter(tags=["会话管理"])

@router.get("/messages")
def get_session_messages_endpoint(
    session_id: str,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    """获取指定会话的对话消息（用于恢复上下文）"""
    return get_session_messages(session_id, limit, db)

@router.delete("/{session_id}")
def delete_one_session_endpoint(
    session_id: str,
    db: Session = Depends(get_db)
):
    """删除指定会话（软删除数据库 + 释放内存）"""
    return delete_one_session(session_id, db)

@router.delete("")
def clear_all_sessions_endpoint(
    db: Session = Depends(get_db)
):
    """清空全部会话（软删除数据库 + 清空内存）"""
    return clear_all_sessions(db)

@router.post("/clean")
def clean_session_data_endpoint(
        session_id: str = Form(...),
        clean_instruction: str = Form(...),
        task_name: Optional[str] = Form(None),
        db: Session = Depends(get_db)
):
    """
    对会话中的数据进行清洗操作。
    参数：
    - session_id: 会话ID
    - clean_instruction: 清洗指令，如“删除年龄为空的行”
    - task_name: 可选，任务名称，用于存储记录
    """
    return clean_session_data(session_id, clean_instruction, task_name, db)

@router.post("/send_message")
async def send_message_endpoint(
        session_id: str = Form(...),
        message: str = Form(...),
        db: Session = Depends(get_db)
):
    """发送消息并处理"""
    return await send_message(session_id, message, db)

@router.get("/history")
def get_session_history_endpoint(
    db: Session = Depends(get_db)
):
    """获取历史会话列表"""
    return get_session_history(db)