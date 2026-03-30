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

from app.core.config import settings
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


def execute_sql_file_in_temp_db(sql_content: str, filename: str) -> Dict[str, Any]:
    """在临时数据库中执行SQL文件，创建表并返回表信息"""
    # 使用临时数据库配置
    temp_db_name = settings.sql_temp_db.db
    db_url_without_db = f"mysql+pymysql://{settings.sql_temp_db.user}:{settings.sql_temp_db.password}@{settings.sql_temp_db.host}:{settings.sql_temp_db.port}?charset=utf8mb4"
    
    # 先连接到MySQL服务器，确保临时数据库存在
    try:
        engine_no_db = sa.create_engine(
            db_url_without_db,
            pool_pre_ping=True,
            connect_args={
                'connect_timeout': 10,
                'read_timeout': 10,
                'write_timeout': 10
            }
        )
        
        with engine_no_db.connect() as conn:
            # 创建临时数据库（如果不存在）
            conn.execute(sa.text(f"CREATE DATABASE IF NOT EXISTS `{temp_db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
        
        engine_no_db.dispose()
    except Exception as db_err:
        raise HTTPException(status_code=400, detail=f"无法创建临时数据库：{str(db_err)}")
    
    # 现在连接到临时数据库
    db_url = settings.sql_temp_db.database_url
    engine = sa.create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args={
            'connect_timeout': 10,
            'read_timeout': 10,
            'write_timeout': 10
        }
    )
    
    # 解析SQL语句 - 使用更健壮的分割方式
    # 按分号分割，但忽略注释中的分号
    statements = []
    current_stmt = []
    
    # 处理多行SQL
    lines = sql_content.split('\n')
    for line in lines:
        line = line.strip()
        # 跳过注释行
        if line.startswith('--') or line.startswith('#'):
            continue
        if not line:
            continue
        # 如果行以分号结尾，说明是一个完整语句
        if line.endswith(';'):
            current_stmt.append(line[:-1].strip())  # 去掉结尾的分号
            if current_stmt:
                statements.append(' '.join(current_stmt).strip())
                current_stmt = []
        else:
            current_stmt.append(line)
    
    # 处理最后一个可能没有分号的语句
    if current_stmt:
        statements.append(' '.join(current_stmt).strip())
    
    # 过滤掉空语句
    statements = [stmt for stmt in statements if stmt.strip()]
    
    # 存储创建的表名
    created_tables = []
    table_info_list = []
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            # 先清空临时数据库中的所有表，避免表已存在的问题
            inspector = sa.inspect(engine)
            existing_tables = inspector.get_table_names()
            for table_name in existing_tables:
                try:
                    conn.execute(sa.text(f"DROP TABLE IF EXISTS `{table_name}`"))
                except Exception as drop_err:
                    print(f"删除表 {table_name} 失败: {drop_err}")
            
            for stmt in statements:
                # 跳过SELECT、SHOW等查询语句，只执行建表和插入语句
                stmt_upper = stmt.upper().strip()
                if (stmt_upper.startswith('SELECT') or 
                    stmt_upper.startswith('SHOW') or 
                    stmt_upper.startswith('DESCRIBE') or
                    stmt_upper.startswith('DESC') or
                    stmt_upper.startswith('EXPLAIN')):
                    continue
                
                # 执行SQL语句
                try:
                    conn.execute(sa.text(stmt))
                except Exception as stmt_err:
                    print(f"执行SQL语句失败: {stmt_err}")
                    print(f"问题语句: {stmt}")
                    # 继续执行其他语句，而不是直接失败
                    continue
                
                # 如果是CREATE TABLE语句，记录表名
                create_match = re.match(r'CREATE\s+TABLE\s*(?:IF\s+NOT\s+EXISTS\s*)?`?([a-zA-Z0-9_]+)`?', stmt, re.IGNORECASE)
                if create_match:
                    table_name = create_match.group(1)
                    if table_name not in created_tables:
                        created_tables.append(table_name)
            
            trans.commit()
            
            # 获取所有创建的表的结构和数据
            for table_name in created_tables:
                try:
                    # 获取表结构
                    inspector = sa.inspect(engine)
                    columns = inspector.get_columns(table_name)
                    
                    # 读取数据（前100行）
                    df = pd.read_sql_table(table_name, engine, chunksize=100)
                    first_chunk = next(df)
                    
                    table_info_list.append({
                        'table_name': table_name,
                        'columns': [{'name': col['name'], 'type': str(col['type'])} for col in columns],
                        'data': first_chunk.to_dict('records'),
                        'row_count': len(first_chunk)
                    })
                except Exception as table_err:
                    # 单个表读取失败不影响其他表
                    print(f"读取表 {table_name} 时出错: {table_err}")
                    continue
                
        return {
            'status': 'ok',
            'tables': table_info_list,
            'created_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        if 'trans' in locals():
            try:
                trans.rollback()
            except:
                pass
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"SQL 执行失败：{str(e)}")
    finally:
        try:
            engine.dispose()
        except:
            pass


def handle_file_upload(file_content: bytes, filename: str, session_id: Optional[str], db: Session):
    """处理文件上传逻辑"""
    ext = os.path.splitext(filename)[1].lower()

    session_repository = SessionRepository(db)
    
    if ext == '.sql':
        # 处理SQL文件 - 新逻辑
        try:
            sql_content = parse_sql_from_bytes(file_content, filename)
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_detail = str(e) if str(e) else "未知错误"
            raise HTTPException(status_code=400, detail=f"SQL 文件解析失败：{error_detail}")
        
        # 在临时数据库中执行SQL
        try:
            sql_result = execute_sql_file_in_temp_db(sql_content, filename)
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_detail = str(e) if str(e) else "未知错误"
            raise HTTPException(status_code=400, detail=f"SQL 执行失败：{error_detail}")
        
        # 使用第一个表的数据创建会话
        tables = sql_result['tables']
        if tables:
            first_table = tables[0]
            df = pd.DataFrame(first_table['data'])
            # 给analysis_workflow使用的完整columns（包含type）
            columns_with_type = first_table['columns']
            # 给前端显示的简化columns（只包含name）
            columns_simple = [{'name': col['name']} for col in columns_with_type]
            row_count = first_table['row_count']
        else:
            df = pd.DataFrame()
            columns_with_type = []
            columns_simple = []
            row_count = 0
        
        # 创建会话，存储SQL执行结果，传入包含type的columns给analysis_workflow使用
        session_id = create_session(df, filename, sql_content, sql_result, columns_with_type)
        
        # 在数据库中创建会话记录
        new_session = SessionModel(
            id=session_id,
            filename=filename,
            row_count=row_count,
            columns=json.dumps(columns_simple),
            preview_data=json.dumps(df.head(5).to_dict('records'))
        )
        session_repository.create_session(new_session)
        
        # 写入系统消息
        # 为返回给前端创建简化的tables（只包含name字段的columns）
        simplified_tables = []
        for table in tables:
            simplified_table = table.copy()
            simplified_table['columns'] = [{'name': col['name']} for col in table['columns']]
            simplified_tables.append(simplified_table)
        
        session_repository.create_session_message(SessionMessage(
            session_id=session_id,
            role=3,
            content=f"已上传SQL文件：{filename}（{len(tables)}个表）",
            extra=json.dumps({
                "type": "sql_upload",
                "filename": filename,
                "sql_content": sql_content[:2000],
                "tables": simplified_tables,
                "is_sql_file": True
            }, ensure_ascii=False)
        ))
        
        # 返回成功响应，使用简化的columns和tables
        return {
            "status": "ok",
            "message": "SQL 文件上传成功",
            "session_id": session_id,
            "filename": filename,
            "data": df.head(5).to_dict('records'),
            "columns": columns_simple,
            "row_count": row_count,
            "tables": simplified_tables,
            "sql_content": sql_content  # 添加SQL内容
        }
    else:
        # 处理CSV或Excel文件
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
            
            db_session = session_repository.get_session_by_id(session_id)
            if db_session:
                db_session.row_count = len(df)
                session_repository.update_session(db_session)
        else:
            session_id = create_session(df, filename)
            
            session_data = get_session(session_id)
            new_session = SessionModel(
                id=session_id,
                filename=filename,
                row_count=session_data["row_count"],
                columns=json.dumps(session_data["columns"]),
                preview_data=json.dumps(session_data["preview"])
            )
            session_repository.create_session(new_session)

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
