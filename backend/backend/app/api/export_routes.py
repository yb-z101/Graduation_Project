from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json
import io

from app.core.database import get_db
from app.models.models import Session as SessionModel, SessionMessage
from app.core.session_manager import get_session, sessions
from app.services.report_service import get_report_service, REPORTLAB_AVAILABLE
from app.utils.llm_client import call_llm

router = APIRouter(prefix="/sessions", tags=["sessions"])


class ExportPdfRequest(BaseModel):
    chart_images: Optional[List[str]] = None


@router.post("/{session_id}/export-pdf")
async def export_session_pdf(session_id: str, request: ExportPdfRequest = None, db: Session = Depends(get_db)):
    """
    导出会话为PDF报告

    返回PDF文件流，可直接下载
    """
    # 检查reportlab是否安装
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="PDF生成功能未安装，请执行: pip install reportlab"
        )

    # 获取会话数据
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")

    try:
        # 获取数据库中的消息记录
        db_messages = db.query(SessionMessage).filter(
            SessionMessage.session_id == session_id
        ).order_by(SessionMessage.created_at).all()

        # 构建消息列表（只包含用户和AI的消息）
        messages = []
        for msg in db_messages:
            if msg.role in [1, 2]:  # 1=用户, 2=AI
                messages.append({
                    'role': 'user' if msg.role == 1 else 'ai',
                    'content': msg.content or ''
                })

        # 获取数据信息
        file_name = session_data.get('filename', '未知文件')
        dataframe = session_data.get('dataframe')
        columns = session_data.get('columns', [])
        sql_content = session_data.get('sql_content')
        sql_result = session_data.get('sql_result')

        # 判断文件类型
        if file_name.endswith('.sql'):
            file_type = 'sql'
        elif file_name.endswith('.csv'):
            file_type = 'csv'
        elif file_name.endswith(('.xlsx', '.xls')):
            file_type = 'excel'
        else:
            file_type = 'unknown'

        # 转换DataFrame为list of dicts
        data_list = []
        if dataframe is not None:
            import pandas as pd
            if isinstance(dataframe, pd.DataFrame):
                data_list = dataframe.to_dict('records')
            else:
                data_list = dataframe if isinstance(dataframe, list) else []

        # 获取分析摘要（从最后一条AI消息中提取）
        analysis_summary = None
        for msg in reversed(messages):
            if msg['role'] == 'ai' and len(msg['content']) > 50:
                analysis_summary = msg['content']
                break

        # 生成PDF
        chart_images = request.chart_images if request else None
        report_service = get_report_service()
        pdf_bytes = report_service.generate_pdf_report(
            session_id=session_id,
            file_name=file_name,
            file_type=file_type,
            data=data_list,
            columns=columns,
            messages=messages,
            analysis_summary=analysis_summary,
            sql_content=sql_content,
            sql_result=sql_result,
            chart_images=chart_images
        )

        # 返回PDF文件
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="analysis_report_{session_id[:8]}.pdf"'
            }
        )

    except Exception as e:
        print(f"[ERROR] PDF导出失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"PDF生成失败: {str(e)}"
        )


@router.get("/{session_id}/insights")
async def get_session_insights(session_id: str, model_id: str = "ali-qwen", db: Session = Depends(get_db)):
    """基于会话数据和分析对话，生成智能洞察"""
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")

    try:
        import pandas as pd

        db_messages = db.query(SessionMessage).filter(
            SessionMessage.session_id == session_id
        ).order_by(SessionMessage.created_at).all()

        conversation_summary = ""
        user_questions = []
        for msg in db_messages:
            if msg.role in [1, 2]:
                role = "用户" if msg.role == 1 else "AI"
                content = (msg.content or "")[:200]
                conversation_summary += f"{role}: {content}\n"
                if msg.role == 1:
                    user_questions.append(content)

        data_summary = ""
        dataframe = session_data.get('dataframe')
        sql_result = session_data.get('sql_result')

        if sql_result and isinstance(sql_result, dict) and sql_result.get('tables'):
            for tname, tdata in sql_result['tables'].items():
                rows = tdata.get('data', [])
                cols = tdata.get('columns', [])
                col_names = [c['name'] for c in cols] if cols else []
                data_summary += f"\n表 {tname}（{len(rows)}行，列：{', '.join(col_names)}）\n"
                if rows:
                    df = pd.DataFrame(rows)
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if numeric_cols:
                        desc = df[numeric_cols].describe().to_string()
                        data_summary += f"统计：{desc}\n"
        elif dataframe is not None:
            if isinstance(dataframe, pd.DataFrame) and not dataframe.empty:
                data_summary += f"\n数据（{len(dataframe)}行，列：{', '.join(dataframe.columns.tolist())}）\n"
                numeric_cols = dataframe.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    desc = dataframe[numeric_cols].describe().to_string()
                    data_summary += f"统计：{desc}\n"

        if not data_summary and not conversation_summary:
            return {"status": "ok", "insights": []}

        questions_str = "\n".join([f"- {q}" for q in user_questions]) if user_questions else "无"
        prompt = f"""你是一个数据分析专家。基于以下用户查询、数据摘要和分析对话，请生成2-3条关键洞察或建议。

要求：
1. 每条洞察必须引用具体的数据和数值
2. 洞察应针对用户关心的问题，具有决策参考价值
3. 示例格式：
   - "张伟的数学成绩仅为45分，远低于班级平均分72分，需要重点关注"
   - "市场部的平均薪资最低（5500元），低于公司平均水平（7800元）的30%"
   - "产品A的销量虽高但利润率仅5%，而产品C销量低但利润率达35%，建议调整产品策略"

用户提出的问题：
{questions_str}

数据摘要：
{data_summary}

对话记录摘要：
{conversation_summary[:1500]}

请直接输出洞察，每条一行，以"-"开头。"""

        result = call_llm(model_id, prompt)

        insights = []
        if result:
            for line in result.strip().split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    line = line.lstrip('-•* ').strip()
                    if line:
                        insights.append(line)
                elif line and len(line) > 10:
                    insights.append(line)

        return {"status": "ok", "insights": insights[:5]}

    except Exception as e:
        print(f"[ERROR] 智能洞察生成失败: {str(e)}")
        return {"status": "ok", "insights": [], "error": str(e)}
