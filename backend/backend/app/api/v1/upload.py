from fastapi import APIRouter, UploadFile, File, Form, Depends
from typing import Optional

from app.core.database import get_db
from app.services.upload_service import handle_file_upload
from sqlalchemy.orm import Session as DBSession

router = APIRouter(tags=["文件上传"])

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: DBSession = Depends(get_db)
):
    print(f"[UPLOAD-API] 收到上传请求: filename={file.filename}, session_id={session_id}")
    content = await file.read()
    print(f"[UPLOAD-API] 文件读取完成, 大小: {len(content)} bytes")
    result = handle_file_upload(content, file.filename, session_id, db)
    print(f"[UPLOAD-API] 处理完成: status={result.get('status')}")
    return result