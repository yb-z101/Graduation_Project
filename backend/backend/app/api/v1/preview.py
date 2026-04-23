from fastapi import APIRouter, UploadFile, File
import pandas as pd
import numpy as np
import io
import os
import math
from app.services.upload_service import parse_csv_excel_from_bytes, parse_sql_from_bytes

router = APIRouter(tags=["文件预览"])


def _sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif pd.isna(obj) if not isinstance(obj, type(pd.NA)) else True:
        return None
    return obj


@router.post("")
async def preview_file(file: UploadFile = File(...)):
    content = await file.read()
    ext = os.path.splitext(file.filename)[1].lower()
    
    try:
        if ext == '.sql':
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
            df = parse_csv_excel_from_bytes(content, file.filename)
            columns = [{'name': col, 'type': str(df[col].dtype)} for col in df.columns]
            preview_data = _sanitize_for_json(df.head(5).to_dict('records'))
            
            null_counts = {}
            for col in df.columns:
                cnt = int(df[col].isnull().sum())
                if cnt > 0:
                    null_counts[col] = cnt
            
            duplicate_count = int(df.duplicated().sum())
            
            return {
                "status": "ok",
                "message": "文件预览成功",
                "file_type": "data",
                "filename": file.filename,
                "structure": {
                    "columns": columns,
                    "row_count": len(df),
                    "preview_data": preview_data,
                    "null_counts": null_counts,
                    "duplicate_count": duplicate_count
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"文件预览失败：{str(e)}"
        }
