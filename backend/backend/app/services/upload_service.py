from typing import Optional
import pandas as pd
import os
import io
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.session_manager import create_session, get_session, update_session_dataframe
from app.models.models import Session as SessionModel, SessionMessage
from app.repositories.session_repository import SessionRepository


def parse_csv_excel_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
    """解析 CSV 或 Excel 文件内容（bytes）"""
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.csv':
        try:
            return pd.read_csv(io.BytesIO(content), encoding='utf-8-sig')
        except UnicodeDecodeError:
            try:
                return pd.read_csv(io.BytesIO(content), encoding='gbk')
            except UnicodeDecodeError:
                return pd.read_csv(io.BytesIO(content), encoding='utf-8')
    elif ext in ['.xlsx', '.xls']:
        return pd.read_excel(io.BytesIO(content))
    else:
        raise ValueError("不支持的文件格式，请上传 CSV 或 Excel 文件")


def handle_file_upload(file_content: bytes, filename: str, session_id: Optional[str], db: Session):
    """处理文件上传逻辑"""
    ext = os.path.splitext(filename)[1].lower()

    # 如果上传的是 SQL 文件，返回友好提示
    if ext == '.sql':
        raise HTTPException(
            status_code=400,
            detail="SQL 文件解析功能已移除，请上传 CSV 或 Excel 文件"
        )

    try:
        df = parse_csv_excel_from_bytes(file_content, filename)
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_detail = str(e) if str(e) else "未知错误"
        raise HTTPException(status_code=400, detail=f"文件解析失败：{error_detail}")

    session_repository = SessionRepository(db)
    # 处理会话
    if session_id and get_session(session_id):
        if not update_session_dataframe(session_id, df):
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 更新数据库中的会话信息
        db_session = session_repository.get_session_by_id(session_id)
        if db_session:
            db_session.row_count = len(df)
            session_repository.update_session(db_session)
    else:
        session_id = create_session(df, filename)
        
        # 在数据库中创建会话记录
        session_data = get_session(session_id)
        new_session = SessionModel(
            id=session_id,
            filename=filename,
            row_count=session_data["row_count"],
            columns=json.dumps(session_data["columns"]),
            preview_data=json.dumps(session_data["preview"])
        )
        session_repository.create_session(new_session)

        # 写入一条系统消息，便于“最近会话”恢复上下文
        session_repository.create_session_message(SessionMessage(
            session_id=session_id,
            role=3,
            content=f"已上传文件：{filename}（{session_data['row_count']} 行）",
            extra=json.dumps({
                "type": "upload",
                "filename": filename,
                "row_count": session_data["row_count"],
                "columns": session_data["columns"]
            }, ensure_ascii=False)
        ))

    session_data = get_session(session_id)
    return {
        "status": "ok",
        "message": "文件上传成功",
        "session_id": session_id,
        "filename": filename,
        "data": session_data["preview"],
        "columns": session_data["columns"],
        "row_count": session_data["row_count"]
    }