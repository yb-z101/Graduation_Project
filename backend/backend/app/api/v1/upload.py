from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import pandas as pd
import os
import io

from app.core.session_manager import create_session, get_session, update_session_dataframe

# 修改路由前缀，添加 /api/v1 前缀
router = APIRouter(prefix="/api/v1/upload", tags=["文件上传"])

def parse_csv_excel_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
    """解析 CSV 或 Excel 文件内容（bytes）"""
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.csv':
        try:
            return pd.read_csv(io.BytesIO(content), encoding='utf-8')
        except UnicodeDecodeError:
            return pd.read_csv(io.BytesIO(content), encoding='gbk')
    elif ext in ['.xlsx', '.xls']:
        return pd.read_excel(io.BytesIO(content))
    else:
        raise ValueError("不支持的文件格式，请上传 CSV 或 Excel 文件")

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    ext = os.path.splitext(file.filename)[1].lower()
    content = await file.read()

    # 如果上传的是 SQL 文件，返回友好提示（可选，也可以直接返回错误）
    if ext == '.sql':
        raise HTTPException(
            status_code=400,
            detail="SQL 文件解析功能已移除，请上传 CSV 或 Excel 文件"
        )

    try:
        df = parse_csv_excel_from_bytes(content, file.filename)
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_detail = str(e) if str(e) else "未知错误"
        raise HTTPException(status_code=400, detail=f"文件解析失败：{error_detail}")

    # 处理会话
    if session_id and get_session(session_id):
        if not update_session_dataframe(session_id, df):
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        session_id = create_session(df, file.filename)

    session_data = get_session(session_id)
    return {
        "status": "ok",
        "message": "文件上传成功",
        "session_id": session_id,
        "filename": file.filename,
        "data": session_data["preview"],
        "columns": session_data["columns"],
        "row_count": session_data["row_count"]
    }