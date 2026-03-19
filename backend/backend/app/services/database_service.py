from typing import Dict, Any, List
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from fastapi import HTTPException

class DatabaseService:
    """数据库服务类，处理数据库连接和查询"""
    
    def __init__(self):
        self.connections = {}
    
    def create_connection(self, connection_id: str, host: str, port: int, username: str, password: str, database: str) -> Dict[str, Any]:
        """创建数据库连接"""
        try:
            # 创建数据库连接URL
            db_url = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4"
            
            # 创建引擎
            engine = sa.create_engine(
                db_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    'connect_timeout': 20,
                    'read_timeout': 20,
                    'write_timeout': 20
                }
            )
            
            # 测试连接
            with engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            
            # 保存连接
            self.connections[connection_id] = {
                "engine": engine,
                "sessionmaker": sessionmaker(bind=engine),
                "connection_info": {
                    "host": host,
                    "port": port,
                    "username": username,
                    "database": database
                }
            }
            
            return {
                "status": "ok",
                "message": "数据库连接成功",
                "connection_id": connection_id
            }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=f"数据库连接失败：{str(e)}")
    
    def test_connection(self, host: str, port: int, username: str, password: str, database: str) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            # 创建数据库连接URL
            db_url = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4"
            
            # 创建引擎
            engine = sa.create_engine(
                db_url,
                pool_pre_ping=True,
                connect_args={
                    'connect_timeout': 20,
                    'read_timeout': 20,
                    'write_timeout': 20
                }
            )
            
            # 测试连接
            with engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            
            return {
                "status": "ok",
                "message": "数据库连接测试成功"
            }
        except SQLAlchemyError as e:
            return {
                "status": "error",
                "message": f"数据库连接测试失败：{str(e)}"
            }
    
    def get_tables(self, connection_id: str) -> Dict[str, Any]:
        """获取数据库中的表列表"""
        try:
            if connection_id not in self.connections:
                raise HTTPException(status_code=404, detail="连接不存在")
            
            engine = self.connections[connection_id]["engine"]
            
            # 获取所有表
            inspector = sa.inspect(engine)
            tables = inspector.get_table_names()
            
            # 获取每个表的结构
            table_structures = []
            for table in tables:
                columns = inspector.get_columns(table)
                table_structures.append({
                    "name": table,
                    "columns": [{
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"]
                    } for col in columns]
                })
            
            return {
                "status": "ok",
                "tables": table_structures
            }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"获取表结构失败：{str(e)}")
    
    def execute_query(self, connection_id: str, query: str, limit: int = 1000) -> Dict[str, Any]:
        """执行SQL查询"""
        try:
            if connection_id not in self.connections:
                raise HTTPException(status_code=404, detail="连接不存在")
            
            engine = self.connections[connection_id]["engine"]
            
            # 处理多条SQL语句，只执行最后一条
            queries = [q.strip() for q in query.split(';') if q.strip()]
            if not queries:
                raise HTTPException(status_code=400, detail="SQL语句为空")
            
            # 只执行最后一条SQL语句
            last_query = queries[-1]
            
            # 执行查询
            df = pd.read_sql_query(last_query, engine)
            
            # 限制返回行数
            if len(df) > limit:
                df = df.head(limit)
            
            return {
                "status": "ok",
                "data": df.to_dict('records'),
                "columns": df.columns.tolist(),
                "row_count": len(df)
            }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=f"SQL执行失败：{str(e)}")
    
    def close_connection(self, connection_id: str) -> Dict[str, Any]:
        """关闭数据库连接"""
        try:
            if connection_id in self.connections:
                engine = self.connections[connection_id]["engine"]
                engine.dispose()
                del self.connections[connection_id]
            
            return {
                "status": "ok",
                "message": "连接已关闭"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"关闭连接失败：{str(e)}")
    
    def chat_to_sql(self, connection_id: str, user_query: str) -> Dict[str, Any]:
        """将自然语言查询转换为SQL语句"""
        try:
            if connection_id not in self.connections:
                raise HTTPException(status_code=404, detail="连接不存在")
            
            engine = self.connections[connection_id]["engine"]
            
            # 获取数据库表结构
            inspector = sa.inspect(engine)
            tables = inspector.get_table_names()
            
            # 构建表结构信息
            schema_info = []
            for table in tables:
                columns = inspector.get_columns(table)
                column_info = []
                for col in columns:
                    column_info.append(f"{col['name']} {col['type']}")
                schema_info.append(f"表名: {table}\n列: {', '.join(column_info)}")
            
            schema_info_str = "\n\n".join(schema_info)
            
            # 检查用户是否请求图表
            wants_chart = any(k in user_query for k in ["图表", "画图", "可视化", "折线图", "柱状图", "饼图"])
            
            # 优化提示，明确告诉模型用户可能需要图表
            if wants_chart:
                user_query += "\n\n注意：用户可能需要基于查询结果生成图表，请确保查询结果包含合适的数据类型（如数值型数据）。"
            
            # 调用大模型生成SQL
            from app.utils.llm_client import generate_sql
            sql = generate_sql(schema_info_str, user_query, "mysql")
            
            # 检查生成的SQL是否为错误消息
            if sql.startswith("错误："):
                raise HTTPException(status_code=400, detail=sql)
            
            return {
                "status": "ok",
                "sql": sql,
                "schema_info": schema_info_str
            }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"获取表结构失败：{str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成SQL失败：{str(e)}")

# 创建全局数据库服务实例
database_service = DatabaseService()
