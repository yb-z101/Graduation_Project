from fastapi import APIRouter, UploadFile, File
import pandas as pd
import numpy as np
import io
import os
from app.services.upload_service import parse_csv_excel_from_bytes, parse_sql_from_bytes
from app.utils.data_cleaner import clean_dataframe

router = APIRouter(tags=["文件预览"])

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

@router.post("")
async def preview_file(file: UploadFile = File(...)):
    """
    预览文件结构，在上传前显示数据结构（包含数据清洗前后对比）
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
            # 预览CSV或Excel文件 - 包含数据清洗
            original_df = parse_csv_excel_from_bytes(content, file.filename)
            
            # 执行数据清洗
            cleaned_df, clean_report = clean_dataframe(original_df)
            
            # 准备原始数据预览
            original_columns = [{'name': col} for col in original_df.columns]
            original_preview = original_df.head(5).to_dict('records')
            
            # 准备清洗后数据预览
            cleaned_columns = [{'name': col} for col in cleaned_df.columns]
            cleaned_preview = cleaned_df.head(5).to_dict('records')
            
            # 构建清洗摘要
            clean_summary = {
                "original_rows": clean_report.get('original_rows', 0),
                "cleaned_rows": clean_report.get('cleaned_rows', 0),
                "original_columns": clean_report.get('original_columns', 0),
                "cleaned_columns": clean_report.get('cleaned_columns', 0),
                "rows_removed": clean_report.get('rows_removed', 0),
                "columns_removed": clean_report.get('columns_removed', 0),
                "operations": clean_report.get('operations', [])
            }
            
            # 替换所有NaN值为None，便于JSON序列化
            original_preview = replace_nan_in_dict(original_preview)
            cleaned_preview = replace_nan_in_dict(cleaned_preview)
            clean_summary = replace_nan_in_dict(clean_summary)
            
            return {
                "status": "ok",
                "message": "文件预览成功",
                "file_type": "data",
                "filename": file.filename,
                "structure": {
                    "original": {
                        "columns": original_columns,
                        "row_count": len(original_df),
                        "preview_data": original_preview
                    },
                    "cleaned": {
                        "columns": cleaned_columns,
                        "row_count": len(cleaned_df),
                        "preview_data": cleaned_preview
                    },
                    "clean_summary": clean_summary
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"文件预览失败：{str(e)}"
        }
