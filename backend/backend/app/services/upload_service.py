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
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.csv':
        encodings = ['utf-8-sig', 'gbk', 'gb2312', 'latin-1']
        last_err = None
        for enc in encodings:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=enc, on_bad_lines='warn')
                return df
            except (UnicodeDecodeError, pd.errors.ParserError) as e:
                last_err = e
                continue
        raise ValueError(f"CSV 文件解析失败，尝试了多种编码均无效：{last_err}")
    elif ext in ['.xlsx', '.xls']:
        try:
            df = pd.read_excel(io.BytesIO(content))
            return df
        except Exception as e:
            raise ValueError(f"Excel 文件解析失败：{e}")
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
    """执行 SQL 文件，使用 SQLite 内存数据库解析并返回表结构和数据"""
    import sqlite3
    
    print(f"\n{'='*80}")
    print(f"[SQL-EXEC] 开始处理SQL文件: {filename}")
    print(f"{'='*80}\n")
    
    # 创建内存 SQLite 数据库
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    try:
        # 第一步：预处理SQL内容，移除注释但保留语句结构
        content_no_comments = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
        content_no_comments = re.sub(r'/\*[\s\S]*?\*/', '', content_no_comments)
        
        # 第二步：分割SQL语句（更健壮的分割方式）
        statements = []
        current_stmt = []
        in_string = False
        string_char = None
        
        for char in content_no_comments:
            if char in ('"', "'") and (not current_stmt or current_stmt[-1] != '\\'):
                if in_string and char == string_char:
                    in_string = False
                    string_char = None
                elif not in_string:
                    in_string = True
                    string_char = char
                current_stmt.append(char)
            elif char == ';' and not in_string:
                stmt = ''.join(current_stmt).strip()
                if stmt:
                    statements.append(stmt)
                current_stmt = []
            else:
                current_stmt.append(char)
        
        # 处理最后一个语句
        if current_stmt:
            stmt = ''.join(current_stmt).strip()
            if stmt:
                statements.append(stmt)
        
        print(f"[SQL-EXEC] 解析到 {len(statements)} 条SQL语句")
        
        for i, stmt in enumerate(statements):
            print(f"[SQL-EXEC] 执行语句 {i+1}/{len(statements)}")
            
            modified_stmt = stmt
            
            # MySQL -> SQLite 语法转换
            modified_stmt = modified_stmt.replace('`', '')
            modified_stmt = re.sub(r'AUTO_INCREMENT', 'AUTOINCREMENT', modified_stmt, flags=re.IGNORECASE)
            modified_stmt = re.sub(r'DECIMAL\([^)]+\)', 'REAL', modified_stmt, flags=re.IGNORECASE)
            modified_stmt = re.sub(r'DATETIME', 'TEXT', modified_stmt, flags=re.IGNORECASE)
            modified_stmt = re.sub(r'DATE', 'TEXT', modified_stmt, flags=re.IGNORECASE)
            modified_stmt = re.sub(r'VARCHAR\([^)]+\)', 'TEXT', modified_stmt, flags=re.IGNORECASE)
            modified_stmt = re.sub(r'INT\([^)]*\)', 'INTEGER', modified_stmt, flags=re.IGNORECASE)
            # 修复1：安全移除 FOREIGN KEY 约束（只移除 CONSTRAINT 行）
            lines = modified_stmt.split('\n')
            filtered_lines = []
            for line in lines:
                line_stripped = line.strip().upper()
                if 'FOREIGN KEY' not in line_stripped and 'CONSTRAINT' not in line_stripped:
                    filtered_lines.append(line)
            modified_stmt = '\n'.join(filtered_lines)
            # 修复2：移除CREATE TABLE语句中最后多余的逗号
            modified_stmt = re.sub(r',\s*\)', ')', modified_stmt)
            
            # 检查是否是 CREATE TABLE 语句
            create_match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)', modified_stmt, flags=re.IGNORECASE)
            
            if create_match:
                table_name = create_match.group(1)
                print(f"[SQL-EXEC]   创建表: {table_name}")
            
            # 执行语句
            try:
                cursor.execute(modified_stmt)
                
                if create_match:
                    print(f"[SQL-EXEC]   ✓ 表创建成功")
                else:
                    print(f"[SQL-EXEC]   ✓ 语句执行成功")
            except Exception as e:
                print(f"[SQL-EXEC]   ✗ 语句执行失败: {e}")
                print(f"[SQL-EXEC]   失败的语句: {modified_stmt[:150]}...")
                # 单条语句失败不中断
        
        conn.commit()
        
        # 从SQLite直接查询所有表名（最可靠的方式）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        all_tables = cursor.fetchall()
        created_tables = [t[0] for t in all_tables]
        
        print(f"[SQL-EXEC] 成功创建 {len(created_tables)} 个表: {created_tables}")
        
        # 获取每个表的数据
        tables = {}
        for table_name in created_tables:
            try:
                # 获取表结构
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                columns = []
                for col in columns_info:
                    columns.append({
                        'name': col[1],
                        'type': col[2],
                        'nullable': col[3] == 0
                    })
                
                # 获取数据
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # 转换为字典列表
                data = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col['name']] = row[i]
                    data.append(row_dict)
                
                tables[table_name] = {
                    'original_name': table_name,
                    'columns': columns,
                    'data': data,
                    'row_count': len(data)
                }
                
                print(f"[SQL-EXEC]   表 {table_name}: {len(data)} 行数据")
                
            except Exception as e:
                print(f"[SQL-EXEC]   获取表 {table_name} 数据失败: {e}")
                continue
        
        print(f"{'='*80}")
        print(f"[SQL-EXEC] SQL解析完成，共 {len(tables)} 个表")
        print(f"{'='*80}\n")
        
        return {
            'status': 'ok',
            'tables': tables,
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
    except Exception as e:
        import traceback
        print(f"[SQL-EXEC] 致命错误: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"SQL 执行失败：{str(e)}")
    finally:
        conn.close()


def df_to_serializable_dict(df, n=5):
    import decimal
    import math
    from datetime import date, datetime
    
    def convert_value(val):
        try:
            if val is pd.NA:
                return None
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return None
            if pd.isna(val):
                return None
        except (TypeError, ValueError):
            pass
        if isinstance(val, decimal.Decimal):
            return float(val)
        if isinstance(val, (date, datetime)):
            return val.isoformat()
        return val
    
    if len(df) == 0:
        return []
    
    records = df.head(n).to_dict('records')
    for record in records:
        for key, value in record.items():
            record[key] = convert_value(value)
    return records


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
            preview_data=json.dumps(df_to_serializable_dict(df, 5))
        )
        session_repository.create_session(new_session)
        
        # 准备所有表的预览数据（用于前端显示）
        all_tables_info = {}
        for table_name, table_data in tables.items():
            all_tables_info[table_name] = {
                'columns': table_data['columns'],
                'row_count': table_data['row_count'],
                'preview_data': df_to_serializable_dict(pd.DataFrame(table_data['data']), 5)
            }
        
        # 写入一条系统消息，便于"最近会话"恢复上下文
        # 注意：只保存可以被JSON序列化的内容，不保存整个sql_result
        session_repository.create_session_message(SessionMessage(
            session_id=session_id,
            role=3,
            content=f"已上传文件：{filename}（{row_count} 行，共 {len(tables)} 张表）",
            extra=json.dumps({
                "type": "upload",
                "filename": filename,
                "sql_content": sql_content,  # 存储完整SQL内容
                "table_names": list(sql_result['tables'].keys()) if sql_result and 'tables' in sql_result else []
            }, ensure_ascii=False)
        ))
        
        # 返回 SQL 文件上传成功的响应（包含所有表信息）
        return {
            "status": "ok",
            "message": f"SQL 文件上传成功（共 {len(tables)} 张表）",
            "session_id": session_id,
            "filename": filename,
            "data": df_to_serializable_dict(df, 5),
            "columns": columns,
            "row_count": row_count,
            "table_count": len(tables),
            "all_tables_info": all_tables_info
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