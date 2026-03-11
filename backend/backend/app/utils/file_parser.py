import pandas as pd
from fastapi import UploadFile, HTTPException
import io
import os

async def parse_upload_file(file: UploadFile) -> pd.DataFrame:
    """
    解析上传的文件，返回pandas DataFrame
    支持格式：.csv, .xlsx, .xls
    """
    ext = os.path.splitext(file.filename)[1].lower()
    content = await file.read()  # 读取文件内容到内存

    try:
        if ext == '.csv':
            # 尝试多种编码
            try:
                df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(content), encoding='gbk')
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式，请上传CSV或Excel文件")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败：{str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="文件为空")

    return df


def parse_csv_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.csv':
        try:
            return pd.read_csv(io.BytesIO(content), encoding='utf-8')
        except UnicodeDecodeError:
            return pd.read_csv(io.BytesIO(content), encoding='gbk')
    elif ext in ['.xlsx', '.xls']:
        return pd.read_excel(io.BytesIO(content))
    else:
        raise ValueError("不支持的文件格式")