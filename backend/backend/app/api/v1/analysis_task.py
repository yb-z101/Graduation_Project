from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
import json
import pymysql
import psycopg2
from typing import List, Optional, Dict, Any
from app.core.session_manager import get_session
from app.utils.safe_executor import execute_pandas_code
from app.utils.chart_generator import generate_chart_config
from app.utils.llm_client import generate_pandas_code, call_qwen
from app.api.v1.schemas.task import SessionTaskResponse
# 导入你的核心依赖（路径完全匹配你的项目）
from app.core.database import get_db
from app.models.models import DataSource, AnalysisTask
from app.api.v1.schemas.task import (
    TaskCreate,
    TaskResponse,
    SQLResult,
    TaskCreateWithPassword  # 新增：包含密码的请求体模型
)
from app.core.sql.security import SQLSecurity
from app.utils.llm_client import test_qwen_api

# 创建路由实例
router = APIRouter(tags=["分析任务"])


# ------------------------------
# 工具函数1：获取数据源表结构（适配MySQL/PostgreSQL）
# ------------------------------
def get_table_structure(ds: DataSource, plain_pwd: str) -> str:
    """
    获取指定数据源的表结构（仅查询，不修改）
    :param ds: 数据源ORM对象
    :param plain_pwd: 数据源明文密码（仅临时使用，不存储）
    :return: 格式化的表结构字符串
    """
    try:
        if ds.source_type == 1:  # MySQL
            conn = pymysql.connect(
                host=ds.host,
                port=ds.port,
                user=ds.username,
                password=plain_pwd,
                db=ds.db_name,
                charset="utf8mb4"
            )
            cursor = conn.cursor()
            # 查询所有表名
            cursor.execute("SHOW TABLES")
            tables = [t[0] for t in cursor.fetchall()]
            struct = ""
            # 查询每张表的字段结构
            for table in tables:
                cursor.execute(f"DESCRIBE {table}")
                fields = [f"{f[0]} ({f[1]})" for f in cursor.fetchall()]
                struct += f"表{table}：{','.join(fields)}\n"
            cursor.close()
            conn.close()
            return struct
        elif ds.source_type == 2:  # PostgreSQL
            conn = psycopg2.connect(
                host=ds.host,
                port=ds.port,
                user=ds.username,
                password=plain_pwd,
                dbname=ds.db_name
            )
            cursor = conn.cursor()
            # 查询所有表名
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = [t[0] for t in cursor.fetchall()]
            struct = ""
            # 查询每张表的字段结构
            for table in tables:
                cursor.execute(
                    f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}'")
                fields = [f"{f[0]} ({f[1]})" for f in cursor.fetchall()]
                struct += f"表{table}：{','.join(fields)}\n"
            cursor.close()
            conn.close()
            return struct
        else:
            return "暂不支持SQLite数据源"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表结构失败：{str(e)}")


# ------------------------------
# 工具函数2：执行SQL查询（仅支持SELECT）
# ------------------------------
def execute_sql(ds: DataSource, plain_pwd: str, sql: str) -> list:
    """
    安全执行SQL查询语句
    :param ds: 数据源ORM对象
    :param plain_pwd: 数据源明文密码
    :param sql: 安全校验后的SELECT SQL
    :return: 执行结果（列表字典格式）
    """
    try:
        if ds.source_type == 1:  # MySQL
            conn = pymysql.connect(
                host=ds.host,
                port=ds.port,
                user=ds.username,
                password=plain_pwd,
                db=ds.db_name,
                charset="utf8mb4"
            )
            cursor = conn.cursor(pymysql.cursors.DictCursor)  # 返回字典格式结果
            cursor.execute(sql)
            res = cursor.fetchall()
            cursor.close()
            conn.close()
            return res
        elif ds.source_type == 2:  # PostgreSQL
            conn = psycopg2.connect(
                host=ds.host,
                port=ds.port,
                user=ds.username,
                password=plain_pwd,
                dbname=ds.db_name
            )
            cursor = conn.cursor()
            cursor.execute(sql)
            # 转换为字典格式（适配前端展示）
            cols = [desc[0] for desc in cursor.description]
            res = [dict(zip(cols, row)) for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return res
        else:
            raise HTTPException(status_code=501, detail="暂不支持SQLite数据源的SQL执行")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行SQL失败：{str(e)}")


# ------------------------------
# 核心接口：创建并执行分析任务（请求体接收密码）
# ------------------------------
@router.post("/create-and-execute", response_model=TaskResponse)
def create_and_execute_analysis_task(
        request: TaskCreateWithPassword,  # 接收包含任务+密码的请求体
        db: Session = Depends(get_db)
):
    """
    创建并执行分析任务（核心接口）
    流程：验证数据源→获取表结构→生成SQL→执行SQL→生成分析结论→存储结果
    """
    # 拆分请求参数
    task = request.task
    plain_password = request.plain_password

    # 步骤1：查询并验证数据源
    ds = db.query(DataSource).filter(
        DataSource.id == task.source_id,
        DataSource.is_deleted == False
    ).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在或已删除")

    # 验证密码正确性（使用你定义的verify_password方法）
    if not ds.verify_password(plain_password):
        raise HTTPException(status_code=400, detail="数据源密码错误")

    # 步骤2：获取数据源表结构
    table_struct = get_table_structure(ds, plain_password)

    # 步骤3：构造Prompt调用大模型生成SQL
    prompt = f"""
    严格按照以下要求生成SQL语句：
    1. 仅返回可执行的SELECT查询语句，不要任何多余文字（如解释、注释、```sql标记）
    2. 适配数据库类型：{['MySQL', 'PostgreSQL', 'SQLite'][ds.source_type - 1]}
    3. 基于以下表结构：
    {table_struct}
    4. 回答用户问题：{task.user_prompt}
    5. 禁止包含DROP/DELETE/ALTER等危险操作，防止SQL注入
    """
    # 调用你封装的大模型函数
    generated_sql = test_qwen_api(prompt)
    # 清洗SQL（移除大模型可能返回的多余格式）
    generated_sql = generated_sql.strip().replace("```sql", "").replace("```", "")

    # 步骤4：SQL安全校验（复用你的SQLSecurity类）
    if not SQLSecurity.check_safety(generated_sql):
        raise HTTPException(status_code=400, detail=f"生成的SQL包含危险操作：{generated_sql}")
    if not SQLSecurity.validate_mysql_syntax(generated_sql):
        raise HTTPException(status_code=400, detail=f"生成的SQL语法错误/非SELECT语句：{generated_sql}")

    # 步骤5：执行SQL
    sql_result = execute_sql(ds, plain_password, generated_sql)

    # 步骤6：调用大模型生成分析结论
    conclusion_prompt = f"""
    基于以下信息，用简洁易懂的自然语言生成分析结论（200字以内）：
    1. 用户提问：{task.user_prompt}
    2. 执行的SQL：{generated_sql}
    3. SQL执行结果：{json.dumps(sql_result, ensure_ascii=False)}
    """
    llm_analysis = test_qwen_api(conclusion_prompt)

    # 步骤7：存储任务结果到数据库
    db_task = AnalysisTask(
        task_name=task.task_name,
        source_id=task.source_id,
        user_prompt=task.user_prompt,
        generated_sql=generated_sql,
        sql_exec_result=json.dumps(sql_result, ensure_ascii=False),
        llm_analysis=llm_analysis,
        task_status=2  # 2-执行成功
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 步骤8：构造并返回响应（匹配你的TaskResponse模型）
    return TaskResponse(
        id=db_task.id,
        task_name=db_task.task_name,
        source_id=db_task.source_id,
        user_prompt=db_task.user_prompt,
        generated_sql=db_task.generated_sql,
        llm_analysis=db_task.llm_analysis,
        task_status=db_task.task_status,
        create_time=db_task.create_time.strftime("%Y-%m-%d %H:%M:%S")
    )


# ------------------------------
# 配套接口1：查询分析任务列表（毕设加分）
# ------------------------------
@router.get("/list", response_model=List[TaskResponse])
def list_analysis_tasks(
        source_id: Optional[int] = None,
        task_status: Optional[int] = None,
        db: Session = Depends(get_db)
):
    """查询分析任务列表（支持按数据源/状态筛选）"""
    query = db.query(AnalysisTask).filter(AnalysisTask.is_deleted == False)
    if source_id:
        query = query.filter(AnalysisTask.source_id == source_id)
    if task_status:
        query = query.filter(AnalysisTask.task_status == task_status)
    tasks = query.order_by(AnalysisTask.create_time.desc()).all()

    # 构造响应
    return [
        TaskResponse(
            id=task.id,
            task_name=task.task_name,
            source_id=task.source_id,
            user_prompt=task.user_prompt,
            generated_sql=task.generated_sql,
            llm_analysis=task.llm_analysis,
            task_status=task.task_status,
            create_time=task.create_time.strftime("%Y-%m-%d %H:%M:%S")
        ) for task in tasks
    ]


# ------------------------------
# 配套接口2：查询分析任务详情（毕设加分）
# ------------------------------
@router.get("/detail/{task_id}", response_model=TaskResponse)
def get_task_detail(
        task_id: int,
        db: Session = Depends(get_db)
):
    """查询分析任务详情"""
    task = db.query(AnalysisTask).filter(
        AnalysisTask.id == task_id,
        AnalysisTask.is_deleted == False
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在或已删除")

    return TaskResponse(
        id=task.id,
        task_name=task.task_name,
        source_id=task.source_id,
        user_prompt=task.user_prompt,
        generated_sql=task.generated_sql,
        llm_analysis=task.llm_analysis,
        task_status=task.task_status,
        create_time=task.create_time.strftime("%Y-%m-%d %H:%M:%S")
    )


@router.post("/session/execute", response_model=SessionTaskResponse)
def execute_session_analysis(
        session_id: str = Form(...),
        user_prompt: str = Form(...),
        task_name: Optional[str] = Form(None),
        db: Session = Depends(get_db)
):
    # 1. 获取会话数据
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")
    df = session_data["dataframe"]

    # 2. 构建 DataFrame 信息
    df_info = {
        "columns": session_data["columns"],
        "sample_rows": df.head(3).to_dict(orient="records")
    }

    # 3. 获取历史记录（从会话内存中）
    history = session_data.get("history", [])

    # 4. 生成 pandas 代码（传入历史）
    try:
        generated_code = generate_pandas_code(df_info, user_prompt, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码生成失败: {str(e)}")

    # 5. 执行代码
    try:
        result_df = execute_pandas_code(generated_code, df)
    except Exception as e:
        # 记录失败任务（source_id = None）
        db_task = AnalysisTask(
            task_name=task_name or "会话分析任务",
            source_id=None,
            user_prompt=user_prompt,
            generated_sql=generated_code,
            sql_exec_result=json.dumps({"error": str(e)}),
            llm_analysis="",
            task_status=3
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        raise HTTPException(status_code=500, detail=f"代码执行失败: {str(e)}")

    # 6. 生成图表配置
    chart_option = generate_chart_config(result_df, user_prompt)
    result_json = result_df.to_dict(orient="records")

    # 7. 生成分析结论（可传入历史）
    analysis_prompt = f"""
基于以下信息，用简洁易懂的自然语言生成分析结论（200字以内）：
用户提问：{user_prompt}
分析结果数据：{json.dumps(result_json[:5], ensure_ascii=False)}
如果结果为空，请说明。
"""
    llm_analysis = call_qwen(analysis_prompt)

    # 8. 存储任务到数据库
    db_task = AnalysisTask(
        task_name=task_name or "会话分析任务",
        source_id=None,
        user_prompt=user_prompt,
        generated_sql=generated_code,
        sql_exec_result=json.dumps(result_json, ensure_ascii=False),
        llm_analysis=llm_analysis,
        task_status=2
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 9. 将本次对话记录存入数据库的 chat_record 表
    from app.models.models import ChatRecord  # 确保导入
    # 用户消息
    user_record = ChatRecord(
        task_id=db_task.id,
        role=1,  # 假设 1-用户
        content=user_prompt,
        create_time=datetime.now()
    )
    db.add(user_record)
    # 系统回复（可存储分析结论或提示信息）
    assistant_content = f"分析完成，共 {len(result_df)} 行结果。"  # 可更丰富
    assistant_record = ChatRecord(
        task_id=db_task.id,
        role=2,  # 2-系统/大模型
        content=assistant_content,
        create_time=datetime.now()
    )
    db.add(assistant_record)
    db.commit()

    # 10. 将对话添加到会话内存历史中
    from app.core.session_manager import add_history
    add_history(session_id, "user", user_prompt, {"task_id": db_task.id})
    add_history(session_id, "assistant", assistant_content, {
        "task_id": db_task.id,
        "generated_code": generated_code,
        "row_count": len(result_df)
    })

    # 11. 返回响应
    return SessionTaskResponse(
        id=db_task.id,
        task_name=db_task.task_name,
        source_id=db_task.source_id,
        user_prompt=db_task.user_prompt,
        generated_sql=db_task.generated_sql,
        llm_analysis=db_task.llm_analysis,
        task_status=db_task.task_status,
        create_time=db_task.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        chart_option=chart_option,
        data=result_json
    )


@router.get("/decision")
async def get_decision_analysis(
    session_id: str,
    db: Session = Depends(get_db)
):
    from app.core.session_manager import get_session
    from app.agents.decision_agent import DecisionAgent

    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")

    df = session_data.get("dataframe")
    columns = session_data.get("columns", [])
    history = session_data.get("history", [])

    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="会话数据为空，无法生成决策建议")

    try:
        agent = DecisionAgent()
        report = agent.analyze(
            df=df,
            columns=columns,
            user_query="请对当前数据集进行全面分析并给出决策建议",
            history=[{"role": h.get("role", ""), "content": h.get("content", "")} for h in history[-10:]]
        )
        return {"status": "ok", "data": report}
    except Exception as e:
        return {"status": "error", "detail": str(e)}