from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import json
import io

from app.core.database import get_db
from app.models.models import Session as SessionModel, SessionMessage
from app.core.session_manager import get_session, sessions
from app.services.report_service import get_report_service, REPORTLAB_AVAILABLE

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/{session_id}/export-pdf")
async def export_session_pdf(session_id: str, db: Session = Depends(get_db)):
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
            sql_result=sql_result
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
