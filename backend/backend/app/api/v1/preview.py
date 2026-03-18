from fastapi import APIRouter, UploadFile, File
import pandas as pd
import io
import os
from app.services.upload_service import parse_csv_excel_from_bytes, parse_sql_from_bytes

router = APIRouter(tags=["文件预览"])

@router.post("")
async def preview_file(file: UploadFile = File(...)):
    """
    预览文件结构，在上传前显示数据结构
    """
    content = await file.read()
    ext = os.path.splitext(file.filename)[1].lower()
    
    try:
        if ext == '.sql':
            # 预览SQL文件
            sql_content = parse_sql_from_bytes(content, file.filename)
            
            return {
                "status": "ok",
                "message": "SQL文件预览成功",
                "file_type": "sql",
                "filename": file.filename,
                "structure": {
                    "content": sql_content
                }
            }
        else:
            # 预览CSV或Excel文件
            df = parse_csv_excel_from_bytes(content, file.filename)
            columns = [{'name': col, 'type': str(df[col].dtype)} for col in df.columns]
            preview_data = df.head(5).to_dict('records')
            
            return {
                "status": "ok",
                "message": "文件预览成功",
                "file_type": "data",
                "filename": file.filename,
                "structure": {
                    "columns": columns,
                    "row_count": len(df),
                    "preview_data": preview_data
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"文件预览失败：{str(e)}"
        }
