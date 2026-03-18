from fastapi import APIRouter, Body
import uuid
from pydantic import BaseModel
from app.services.database_service import database_service

class ConnectionRequest(BaseModel):
    host: str
    port: int
    username: str
    password: str
    database: str

class QueryRequest(BaseModel):
    query: str
    limit: int = 1000

class ChatToSqlRequest(BaseModel):
    user_query: str

router = APIRouter(tags=["数据库连接"])

@router.post("/test-connection")
async def test_connection(
    request: ConnectionRequest = Body(..., description="连接请求")
):
    """
    测试数据库连接
    """
    return database_service.test_connection(request.host, request.port, request.username, request.password, request.database)

@router.post("/connect")
async def connect_database(
    request: ConnectionRequest = Body(..., description="连接请求")
):
    """
    连接数据库
    """
    connection_id = str(uuid.uuid4())
    return database_service.create_connection(connection_id, request.host, request.port, request.username, request.password, request.database)

@router.get("/tables/{connection_id}")
async def get_tables(connection_id: str):
    """
    获取数据库中的表列表
    """
    return database_service.get_tables(connection_id)

@router.post("/query/{connection_id}")
async def execute_query(
    connection_id: str,
    request: QueryRequest = Body(..., description="查询请求")
):
    """
    执行SQL查询
    """
    return database_service.execute_query(connection_id, request.query, request.limit)

@router.post("/disconnect/{connection_id}")
async def disconnect_database(connection_id: str):
    """
    关闭数据库连接
    """
    return database_service.close_connection(connection_id)

@router.post("/chat-to-sql/{connection_id}")
async def chat_to_sql(
    connection_id: str,
    request: ChatToSqlRequest = Body(..., description="自然语言查询请求")
):
    """
    将自然语言查询转换为SQL语句
    """
    return database_service.chat_to_sql(connection_id, request.user_query)
