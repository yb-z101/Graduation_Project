from typing import Optional, Dict, Any
import pandas as pd
import os
import io
import json
import re
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
import sqlalchemy as sa

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


def parse_sql_from_bytes(content: bytes, filename: str) -> str:
    """解析 SQL 文件内容（bytes）"""
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.sql':
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return content.decode('gbk')
            except UnicodeDecodeError:
                return content.decode('utf-8')
    else:
        raise ValueError("不支持的文件格式，请上传 SQL 文件")


def execute_sql_file(content: str, filename: str) -> Dict[str, Any]:
    """执行 SQL 文件，在 TempSQL_db 中创建临时表并返回表结构和数据"""
    # 创建临时数据库连接
    # 使用用户提供的正确凭据
    db_url = "mysql+pymysql://root:123456@localhost:3306/tempsql_db?charset=utf8mb4"
    engine = sa.create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args={
            'connect_timeout': 10,
            'read_timeout': 10,
            'write_timeout': 10
        }
    )
    
    # 生成唯一的前缀，避免表名冲突
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_prefix = re.sub(r'[^a-zA-Z0-9]', '_', os.path.splitext(filename)[0])
    table_prefix = f"temp_{file_prefix}_{timestamp}_"
    
    # 解析 SQL 语句
    statements = re.split(r';\s*$', content, flags=re.MULTILINE)
    statements = [stmt.strip() for stmt in statements if stmt.strip()]
    
    # 存储创建的表名
    created_tables = []
    table_structures = {}
    
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            for stmt in statements:
                # 检查是否是 CREATE TABLE 语句
                create_match = re.match(r'CREATE\s+TABLE\s+`?([a-zA-Z0-9_]+)`?', stmt, re.IGNORECASE)
                if create_match:
                    # 获取原始表名
                    original_table_name = create_match.group(1)
                    # 生成新的表名
                    new_table_name = f"{table_prefix}{original_table_name}"
                    # 替换表名
                    modified_stmt = re.sub(r'CREATE\s+TABLE\s+`?([a-zA-Z0-9_]+)`?', f'CREATE TABLE `{new_table_name}`', stmt, flags=re.IGNORECASE)
                    # 执行修改后的语句
                    conn.execute(sa.text(modified_stmt))
                    created_tables.append(new_table_name)
                    # 记录表结构
                    inspector = sa.inspect(engine)
                    columns = inspector.get_columns(new_table_name)
                    table_structures[new_table_name] = {
                        'original_name': original_table_name,
                        'columns': [{
                            'name': col['name'],
                            'type': str(col['type']),
                            'nullable': col['nullable']
                        } for col in columns]
                    }
                else:
                    # 对于其他语句（如 INSERT），需要替换表名
                    modified_stmt = stmt
                    for table in created_tables:
                        original_name = table_structures[table]['original_name']
                        # 替换 INSERT INTO 语句中的表名
                        modified_stmt = re.sub(
                            r'INSERT\s+INTO\s+`?' + re.escape(original_name) + r'`?',
                            f'INSERT INTO `{table}`',
                            modified_stmt,
                            flags=re.IGNORECASE
                        )
                    # 执行修改后的语句
                    conn.execute(sa.text(modified_stmt))
            
            # 提交事务
            trans.commit()
            
            # 获取每个表的数据
            table_data = {}
            for table in created_tables:
                # 读取表数据
                df = pd.read_sql_table(table, engine)
                table_data[table] = {
                    'original_name': table_structures[table]['original_name'],
                    'columns': table_structures[table]['columns'],
                    'data': df.to_dict('records'),
                    'row_count': len(df)
                }
                
        # 返回结果
        return {
            'status': 'ok',
            'tables': table_data,
            'table_prefix': table_prefix,
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
    except Exception as e:
        # 回滚事务
        if 'trans' in locals():
            trans.rollback()
        # 清理已创建的表
        try:
            with engine.connect() as conn:
                for table in created_tables:
                    try:
                        conn.execute(sa.text(f'DROP TABLE IF EXISTS `{table}`'))
                    except:
                        pass
        except:
            pass
        raise HTTPException(status_code=400, detail=f"SQL 执行失败：{str(e)}")
    finally:
        # 关闭引擎
        engine.dispose()


def handle_file_upload(file_content: bytes, filename: str, session_id: Optional[str], db: Session):
    """处理文件上传逻辑"""
    ext = os.path.splitext(filename)[1].lower()

    session_repository = SessionRepository(db)
    
    if ext == '.sql':
        # 处理 SQL 文件
        try:
            sql_content = parse_sql_from_bytes(file_content, filename)
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_detail = str(e) if str(e) else "未知错误"
            raise HTTPException(status_code=400, detail=f"SQL 文件解析失败：{error_detail}")
        
        # 执行 SQL 文件，在 TempSQL_db 中创建临时表
        try:
            sql_result = execute_sql_file(sql_content, filename)
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_detail = str(e) if str(e) else "未知错误"
            raise HTTPException(status_code=400, detail=f"SQL 执行失败：{error_detail}")
        
        # 为 SQL 文件创建会话
        # 使用第一个表的数据作为主数据
        tables = sql_result['tables']
        if tables:
            # 获取第一个表的数据
            first_table_name = next(iter(tables))
            first_table = tables[first_table_name]
            # 创建 DataFrame
            df = pd.DataFrame(first_table['data'])
            # 提取列信息
            columns = [{'name': col['name'], 'type': col['type']} for col in first_table['columns']]
            row_count = first_table['row_count']
        else:
            # 如果没有表，创建空 DataFrame
            df = pd.DataFrame()
            columns = []
            row_count = 0
        
        # 创建会话，存储 SQL 执行结果
        session_id = create_session(df, filename, sql_content, sql_result)
        
        # 在数据库中创建会话记录
        new_session = SessionModel(
            id=session_id,
            filename=filename,
            row_count=row_count,
            columns=json.dumps(columns),
            preview_data=json.dumps(df.head(5).to_dict('records'))
        )
        session_repository.create_session(new_session)
        
        # 写入一条系统消息，便于“最近会话”恢复上下文
        session_repository.create_session_message(SessionMessage(
            session_id=session_id,
            role=3,
            content=f"已上传文件：{filename}（{row_count} 行）",
            extra=json.dumps({
                "type": "upload",
                "filename": filename,
                "sql_content": sql_content[:1000],  # 只存储前 1000 个字符，避免存储过多内容
                "sql_result": sql_result
            }, ensure_ascii=False)
        ))
        
        # 返回 SQL 文件上传成功的响应
        return {
            "status": "ok",
            "message": "SQL 文件上传成功",
            "session_id": session_id,
            "filename": filename,
            "data": df.head(5).to_dict('records'),
            "columns": columns,
            "row_count": row_count
        }
    else:
        # 处理 CSV 或 Excel 文件
        try:
            df = parse_csv_excel_from_bytes(file_content, filename)
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_detail = str(e) if str(e) else "未知错误"
            raise HTTPException(status_code=400, detail=f"文件解析失败：{error_detail}")

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