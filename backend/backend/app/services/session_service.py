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


async def send_message(session_id: str, message: str, db: Session) -> Dict[str, Any]:
    """发送消息并处理"""
    # 获取会话数据
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 创建工作流状态
    state = {
        "session_id": session_id,
        "file_name": session_data["filename"],
        "data": session_data["dataframe"],
        "columns": session_data["columns"],
        "user_query": message,
        "history": session_data.get("history", [])
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
    
    db_task = AnalysisTask(
        task_name="对话分析任务",
        source_id=None,
        user_prompt=message,
        generated_sql="",
        sql_exec_result=json.dumps(result.get("analysis_result").to_dict() if result.get("analysis_result") is not None else None),
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
            "result": result.get("analysis_result").to_dict() if result.get("analysis_result") is not None else None,
            "chart_option": result.get("chart_option")
        }, ensure_ascii=False)
    ))

    # 添加到内存历史
    add_history(session_id, "user", message, {"task_id": db_task.id})
    add_history(session_id, "assistant", assistant_content, {"task_id": db_task.id})

    # 返回结果
    return {
        "status": "ok",
        "message": "消息处理成功",
        "task_id": db_task.id,
        "result": result.get("analysis_result").to_dict() if result.get("analysis_result") is not None else None,
        "chart_option": result.get("chart_option"),
        "error": result.get("error"),
        "analysis_summary": result.get("analysis_summary")
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
        base = filename.rsplit(".", 1)[0] if "." in filename else filename
        if filename and (has_upload_msg or has_analysis_msg):
            display_name = f"{base}文件数据分析"
        else:
            title = (last_user_msg.content or "").strip() if last_user_msg else ""
            if len(title) > 10:
                title = title[:10] + "…"
            display_name = title or (f"{base}会话" if base else "新会话")

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
