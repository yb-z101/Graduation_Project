from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
import pandas as pd
import json
from datetime import datetime

from app.core.database import get_db
from app.core.session_manager import get_session, update_session_dataframe, add_history
from app.models.models import ChatRecord, AnalysisTask
from app.utils.safe_executor import execute_pandas_code
from app.utils.llm_client import generate_clean_code, call_qwen

router = APIRouter(prefix="/api/v1/session", tags=["会话管理"])


@router.post("/clean")
def clean_session_data(
        session_id: str = Form(...),
        clean_instruction: str = Form(...),
        task_name: Optional[str] = Form(None),
        db: Session = Depends(get_db)
):
    """
    对会话中的数据进行清洗操作。
    参数：
    - session_id: 会话ID
    - clean_instruction: 清洗指令，如“删除年龄为空的行”
    - task_name: 可选，任务名称，用于存储记录
    """
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
        db_task = AnalysisTask(
            task_name=task_name or "会话清洗任务",
            source_id=None,
            user_prompt=clean_instruction,
            generated_sql=clean_code,
            sql_exec_result=json.dumps({"error": str(e)}),
            llm_analysis="",
            task_status=3
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        raise HTTPException(status_code=500, detail=f"清洗代码执行失败: {str(e)}")

    # 6. 更新会话中的 DataFrame
    if not update_session_dataframe(session_id, result_df):
        raise HTTPException(status_code=500, detail="更新会话数据失败")

    # 7. 记录到数据库（可选，也可只记录到 chat_record）
    # 创建一个分析任务记录清洗操作（类型可用 task_name 标识）
    db_task = AnalysisTask(
        task_name=task_name or "会话清洗任务",
        source_id=None,
        user_prompt=clean_instruction,
        generated_sql=clean_code,
        sql_exec_result=json.dumps(result_df.head(5).to_dict(orient="records"), ensure_ascii=False),
        llm_analysis="",
        task_status=2
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 8. 记录对话历史
    user_record = ChatRecord(
        task_id=db_task.id,
        role=1,
        content=clean_instruction,
        create_time=datetime.now()
    )
    db.add(user_record)
    assistant_content = f"清洗完成，数据从 {len(df)} 行变为 {len(result_df)} 行。"
    assistant_record = ChatRecord(
        task_id=db_task.id,
        role=2,
        content=assistant_content,
        create_time=datetime.now()
    )
    db.add(assistant_record)
    db.commit()

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