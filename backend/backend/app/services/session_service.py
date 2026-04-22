from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime

from app.core.session_manager import get_session, update_session_dataframe, add_history, delete_session as delete_memory_session, sessions as memory_sessions
from app.models.models import ChatRecord, AnalysisTask, Session as SessionModel, SessionMessage
from app.repositories.session_repository import SessionRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.utils.safe_executor import execute_pandas_code
from app.utils.llm_client import generate_clean_code, call_qwen
from app.workflows.analysis_workflow import create_analysis_workflow


# 创建工作流实例
analysis_workflow = create_analysis_workflow()


def get_session_messages(session_id: str, limit: int, db: Session) -> Dict[str, Any]:
    """获取指定会话的对话消息（用于恢复上下文）"""
    session_repository = SessionRepository(db)
    msgs = session_repository.get_session_messages(session_id, limit)

    return {
        "status": "ok",
        "messages": [
            {
                "id": m.id,
                "session_id": m.session_id,
                "role": m.role,
                "content": m.content,
                "extra": json.loads(m.extra) if m.extra else None,
                "timestamp": m.create_time.isoformat() if m.create_time else None
            }
            for m in msgs
        ]
    }


def delete_one_session(session_id: str, db: Session) -> Dict[str, Any]:
    """删除指定会话（软删除数据库 + 释放内存）"""
    session_repository = SessionRepository(db)
    if not session_repository.delete_session(session_id):
        raise HTTPException(status_code=404, detail="会话不存在或已删除")

    # 释放内存会话
    delete_memory_session(session_id)

    return {"status": "ok", "message": "会话已删除", "session_id": session_id}


def clear_all_sessions(db: Session) -> Dict[str, Any]:
    """清空全部会话（软删除数据库 + 清空内存）"""
    session_repository = SessionRepository(db)
    session_repository.delete_all_sessions()

    # 清空内存会话
    memory_sessions.clear()

    return {"status": "ok", "message": "已清空全部会话"}


def clean_session_data(session_id: str, clean_instruction: str, task_name: Optional[str], db: Session) -> Dict[str, Any]:
    """对会话中的数据进行清洗操作"""
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

    # 3. 获取历史
    history = session_data.get("history", [])

    # 4. 生成清洗代码
    try:
        clean_code = generate_clean_code(df_info, clean_instruction, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清洗代码生成失败: {str(e)}")

    # 5. 执行清洗代码（注意：代码应修改 df 变量）
    try:
        # 准备执行环境：需要传入 df，并期望执行后 df 被修改
        # 我们构造一个代码片段，先执行清洗代码，然后将 df 赋值给 result 以便获取
        # 因为 execute_pandas_code 期望 result 变量
        # 我们可以将清洗代码包装一下
        wrapped_code = f"""
{clean_code}
result = df
"""
        result_df = execute_pandas_code(wrapped_code, df.copy())  # 传入副本防止污染
    except Exception as e:
        # 记录失败任务
        analysis_repository = AnalysisRepository(db)
        db_task = AnalysisTask(
            task_name=task_name or "会话清洗任务",
            source_id=None,
            user_prompt=clean_instruction,
            generated_sql=clean_code,
            sql_exec_result=json.dumps({"error": str(e)}),
            llm_analysis="",
            task_status=3
        )
        analysis_repository.create_analysis_task(db_task)
        raise HTTPException(status_code=500, detail=f"清洗代码执行失败: {str(e)}")

    # 6. 更新会话中的 DataFrame
    if not update_session_dataframe(session_id, result_df):
        raise HTTPException(status_code=500, detail="更新会话数据失败")

    # 7. 记录到数据库（可选，也可只记录到 chat_record）
    # 创建一个分析任务记录清洗操作（类型可用 task_name 标识）
    analysis_repository = AnalysisRepository(db)
    session_repository = SessionRepository(db)
    
    db_task = AnalysisTask(
        task_name=task_name or "会话清洗任务",
        source_id=None,
        user_prompt=clean_instruction,
        generated_sql=clean_code,
        sql_exec_result=json.dumps(result_df.head(5).to_dict(orient="records"), ensure_ascii=False),
        llm_analysis="",
        task_status=2
    )
    db_task = analysis_repository.create_analysis_task(db_task)

    # 8. 记录对话历史
    user_record = ChatRecord(
        task_id=db_task.id,
        role=1,
        content=clean_instruction,
        create_time=datetime.now()
    )
    analysis_repository.create_chat_record(user_record)
    
    assistant_content = f"清洗完成，数据从 {len(df)} 行变为 {len(result_df)} 行。"
    assistant_record = ChatRecord(
        task_id=db_task.id,
        role=2,
        content=assistant_content,
        create_time=datetime.now()
    )
    analysis_repository.create_chat_record(assistant_record)

    # 8.1 同步写入会话消息表（用于持久化上下文）
    session_repository.create_session_message(SessionMessage(
        session_id=session_id,
        role=1,
        content=clean_instruction,
        extra=json.dumps({"task_id": db_task.id, "type": "clean"}, ensure_ascii=False)
    ))
    session_repository.create_session_message(SessionMessage(
        session_id=session_id,
        role=2,
        content=assistant_content,
        extra=json.dumps({"task_id": db_task.id, "type": "clean"}, ensure_ascii=False)
    ))

    # 9. 添加到内存历史
    add_history(session_id, "user", clean_instruction, {"task_id": db_task.id})
    add_history(session_id, "assistant", assistant_content, {"task_id": db_task.id})

    # 10. 返回清洗后的预览信息
    return {
        "session_id": session_id,
        "task_id": db_task.id,
        "filename": session_data["filename"],
        "row_count_before": len(df),
        "row_count_after": len(result_df),
        "preview": result_df.head(5).to_dict(orient="records"),
        "columns": [
            {"name": col, "type": str(result_df[col].dtype)}
            for col in result_df.columns
        ]
    }


def get_data_profile(session_id: str) -> Dict[str, Any]:
    import pandas as pd
    import numpy as np
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")
    df = session_data["dataframe"]
    total_rows = len(df)
    total_cols = len(df.columns)
    null_counts = df.isnull().sum().to_dict()
    null_percentages = {col: round(cnt / total_rows * 100, 2) if total_rows > 0 else 0 for col, cnt in null_counts.items()}
    duplicate_count = int(df.duplicated().sum())
    column_profiles = []
    for col in df.columns:
        col_info = {"name": col, "dtype": str(df[col].dtype), "null_count": int(null_counts.get(col, 0)), "null_percentage": null_percentages.get(col, 0), "unique_count": int(df[col].nunique())}
        if pd.api.types.is_numeric_dtype(df[col]):
            valid_series = df[col].dropna()
            if len(valid_series) > 0:
                col_info["min"] = float(valid_series.min()) if not pd.isna(valid_series.min()) else None
                col_info["max"] = float(valid_series.max()) if not pd.isna(valid_series.max()) else None
                col_info["mean"] = round(float(valid_series.mean()), 4) if not pd.isna(valid_series.mean()) else None
                col_info["median"] = float(valid_series.median()) if not pd.isna(valid_series.median()) else None
                col_info["std"] = round(float(valid_series.std()), 4) if len(valid_series) > 1 else None
            else:
                col_info.update({"min": None, "max": None, "mean": None, "median": None, "std": None})
        else:
            value_counts = df[col].value_counts().head(5)
            col_info["top_values"] = [{str(k): int(v)} for k, v in value_counts.items()]
        column_profiles.append(col_info)
    overall_score = 100
    if total_rows > 0:
        total_null_ratio = sum(null_counts.values()) / (total_rows * total_cols) * 100
        dup_ratio = duplicate_count / total_rows * 100
        overall_score = max(0, round(100 - total_null_ratio - dup_ratio, 1))
    return {"status": "ok", "session_id": session_id, "filename": session_data["filename"], "total_rows": total_rows, "total_columns": total_cols, "duplicate_rows": duplicate_count, "total_null_cells": int(sum(null_counts.values())), "overall_quality_score": overall_score, "column_profiles": column_profiles}


async def send_message(session_id: str, message: str, model_id: str, db: Session) -> Dict[str, Any]:
    """发送消息并处理"""
    from app.utils.audit_logger import get_audit_logger
    audit_logger = get_audit_logger(db)

    # 获取会话数据
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 🆕 调试日志：检查SQL数据传递状态
    sql_result = session_data.get("sql_result")
    print(f"[SESSION-DEBUG] 发送消息 - Session: {session_id}")
    print(f"[SESSION-DEBUG]   文件名: {session_data.get('filename')}")
    print(f"[SESSION-DEBUG]   sql_content存在: {bool(session_data.get('sql_content'))}")
    print(f"[SESSION-DEBUG]   sql_result存在: {bool(sql_result)}")

    if sql_result and sql_result.get('tables'):
        tables = sql_result['tables']
        print(f"[SESSION-DEBUG]   表数量: {len(tables)}")
        for tname, tdata in tables.items():
            rows = len(tdata.get('data', []))
            print(f"[SESSION-DEBUG]   - {tdata.get('original_name', tname)}: {rows}行数据")
    else:
        print(f"[SESSION-DEBUG]   ⚠️ 无sql_result或tables为空！")

    # 创建工作流状态
    state = {
        "session_id": session_id,
        "file_name": session_data["filename"],
        "data": session_data["dataframe"],
        "columns": session_data["columns"],
        "user_query": message,
        "history": session_data.get("history", []),
        "sql_content": session_data.get("sql_content"),
        "sql_result": session_data.get("sql_result"),
        "model_id": model_id
    }

    # 执行工作流
    result = await analysis_workflow.ainvoke(state)

    # 更新会话历史
    if not session_data.get("history"):
        session_data["history"] = []
    session_data["history"] = result.get("history", [])
    if result.get("analysis_result") is not None:
        session_data["last_result"] = result.get("analysis_result").to_dict()

    # 保存聊天记录
    # 创建分析任务
    analysis_repository = AnalysisRepository(db)
    session_repository = SessionRepository(db)
    
    # 处理 analysis_result 为 None 的情况
    analysis_result_dict = None
    if result.get("analysis_result") is not None:
        try:
            analysis_result_dict = result.get("analysis_result").to_dict(orient="records")
        except:
            analysis_result_dict = None
    
    # 审计日志：记录查询操作
    audit_logger.log(
        operation_type='CHAT_SEND',
        session_id=session_id,
        dataset_name=session_data.get("filename"),
        dataset_type='sql' if session_data.get("sql_content") else 'file',
        query_content=message,
        status='success',
        sensitivity_level=1
    )

    db_task = AnalysisTask(
        task_name="对话分析任务",
        source_id=None,
        user_prompt=message,
        generated_sql="",
        sql_exec_result=json.dumps(analysis_result_dict),
        llm_analysis=json.dumps({
            "chart_option": result.get("chart_option"),
            "error": result.get("error")
        }),
        task_status=2
    )
    db_task = analysis_repository.create_analysis_task(db_task)

    # 记录对话历史
    user_record = ChatRecord(
        task_id=db_task.id,
        role=1,
        content=message,
        create_time=datetime.now()
    )
    analysis_repository.create_chat_record(user_record)

    assistant_content = result.get("analysis_summary") or result.get("error") or "分析完成"
    if result.get("chart_option"):
        assistant_content += "（已生成图表）"
        audit_logger.log(
            operation_type='CHART_GENERATE',
            session_id=session_id,
            query_content=message,
            status='success'
        )

    assistant_record = ChatRecord(
        task_id=db_task.id,
        role=2,
        content=assistant_content,
        create_time=datetime.now()
    )
    analysis_repository.create_chat_record(assistant_record)

    # 同步写入会话消息表（用于持久化上下文，extra 可携带结果表/图表配置）
    session_repository.create_session_message(SessionMessage(
        session_id=session_id,
        role=1,
        content=message,
        extra=json.dumps({"task_id": db_task.id, "type": "analysis"}, ensure_ascii=False)
    ))
    session_repository.create_session_message(SessionMessage(
        session_id=session_id,
        role=2,
        content=assistant_content,
        extra=json.dumps({
            "task_id": db_task.id,
            "type": "analysis",
            "analysis_summary": result.get("analysis_summary"),
            "result": analysis_result_dict,
            "chart_option": result.get("chart_option")
        }, ensure_ascii=False)
    ))

    # 添加到内存历史
    add_history(session_id, "user", message, {"task_id": db_task.id})
    add_history(session_id, "assistant", assistant_content, {"task_id": db_task.id})

    # 构建执行日志
    execution_log = []
    from datetime import datetime as dt
    t0 = dt.now().isoformat(timespec='seconds')
    intent = result.get("intent", "unknown")
    execution_log.append({"node": "意图识别", "status": "success", "description": f"识别意图: {intent}", "timestamp": t0})
    if result.get("generated_sql"):
        execution_log.append({"node": "SQL生成", "status": "success", "description": "已生成查询SQL", "timestamp": t0, "code": result["generated_sql"], "language": "sql"})
    if result.get("analysis_result") is not None:
        execution_log.append({"node": "数据分析", "status": "success", "description": "数据分析完成", "timestamp": t0})
    if result.get("chart_option"):
        execution_log.append({"node": "图表生成", "status": "success", "description": "已生成可视化图表", "timestamp": t0})
    if result.get("error"):
        execution_log.append({"node": "异常", "status": "error", "description": result["error"], "timestamp": t0})
    if not result.get("error"):
        execution_log.append({"node": "完成", "status": "success", "description": "分析流程结束", "timestamp": t0})

    # 刷新审计日志缓冲区
    audit_logger.flush()
    
    # 返回结果
    return {
        "status": "ok",
        "message": "消息处理成功",
        "task_id": db_task.id,
        "result": analysis_result_dict,
        "chart_option": result.get("chart_option"),
        "error": result.get("error"),
        "analysis_summary": result.get("analysis_summary"),
        "generated_sql": result.get("generated_sql"),
        "execution_log": execution_log,
        # 多表数据支持
        "is_multi_table_response": result.get("is_multi_table_response", False),
        "multi_table_data": result.get("multi_table_data", None),
        "current_table_name": result.get("current_table_name", None),
        "total_rows": result.get("total_rows", None),
        "displayed_rows": result.get("displayed_rows", None)
    }


def get_session_history(db: Session) -> Dict[str, Any]:
    """获取历史会话列表"""
    session_repository = SessionRepository(db)
    # 查询最近的5个会话，按创建时间倒序排列
    sessions = session_repository.get_all_sessions(5)
    
    # 构建响应数据
    session_list = []
    for session in sessions:
        # 获取该会话最后一条消息（用于列表预览）
        last_msg = session_repository.get_last_session_message(session.id)

        # 获取该会话最后一条“用户消息”（用于命名）
        last_user_msg = session_repository.get_last_user_message(session.id)

        # 判断是否为“文件数据分析”型会话：存在上传系统消息/分析型消息即可认为是
        # 简化处理，直接基于文件名判断
        has_upload_msg = True if session.filename else False
        has_analysis_msg = True

        # 生成 displayName（你提的规则）
        display_name = None
        filename = session.filename or ""
        if filename and (has_upload_msg or has_analysis_msg):
            # 按照用户要求的格式生成displayName
            if filename.lower().endswith('.csv'):
                display_name = f"{filename}文件分析"
            elif filename.lower().endswith('.sql'):
                display_name = f"{filename}文件分析"
            elif filename.lower().endswith('.xlsx') or filename.lower().endswith('.xls'):
                display_name = f"{filename}文件分析"
            elif "数据库" in filename:
                display_name = f"{filename}数据库数据分析"
            else:
                display_name = f"{filename}文件分析"
        else:
            title = (last_user_msg.content or "").strip() if last_user_msg else ""
            if len(title) > 10:
                title = title[:10] + "…"
            display_name = title or (f"{filename}会话" if filename else "新会话")

        session_list.append({
            "id": session.id,
            "fileName": session.filename,
            "displayName": display_name,
            "rowCount": session.row_count,
            "timestamp": session.create_time.isoformat(),
            "lastMessage": last_msg.content if last_msg else None,
            "lastMessageTime": last_msg.create_time.isoformat() if last_msg and last_msg.create_time else None
        })
    
    return {
        "status": "ok",
        "message": "获取历史会话成功",
        "sessions": session_list
    }
