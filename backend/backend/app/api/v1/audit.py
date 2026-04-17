from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.models.audit_log import AuditLog
from sqlalchemy import and_, or_, func

router = APIRouter(tags=["审计日志"])


@router.get("/logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    operation_type: Optional[str] = None,
    status: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    filters = []

    if operation_type:
        filters.append(AuditLog.operation_type == operation_type)
    if status:
        filters.append(AuditLog.status == status)
    if session_id:
        filters.append(AuditLog.session_id == session_id)
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    if start_date:
        filters.append(AuditLog.timestamp >= start_date)
    if end_date:
        filters.append(AuditLog.timestamp <= end_date)
    if keyword:
        search_filter = or_(
            AuditLog.query_content.contains(keyword),
            AuditLog.dataset_name.contains(keyword),
            AuditLog.result_summary.contains(keyword),
            AuditLog.error_message.contains(keyword)
        )
        filters.append(search_filter)

    if filters:
        query = query.filter(and_(*filters))

    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc())\
                .offset((page - 1) * page_size)\
                .limit(page_size)\
                .all()

    return {
        "status": "ok",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "logs": [
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "operation_type": log.operation_type,
                    "operation_name": log.operation_name,
                    "user_id": log.user_id,
                    "session_id": log.session_id,
                    "dataset_name": log.dataset_name,
                    "dataset_type": log.dataset_type,
                    "query_content": log.query_content,
                    "result_summary": log.result_summary,
                    "status": log.status,
                    "error_message": log.error_message,
                    "ip_address": log.ip_address,
                    "sensitivity_level": log.sensitivity_level
                }
                for log in logs
            ]
        }
    }


@router.get("/stats")
async def get_audit_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    from app.utils.audit_logger import get_audit_logger

    audit_logger = get_audit_logger(db)
    end_date = datetime.now()
    start_date = datetime.fromtimestamp(end_date.timestamp() - days * 86400)

    stats = audit_logger.get_stats(start_date, end_date)

    type_stats = db.query(
        AuditLog.operation_type,
        AuditLog.operation_name,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date,
        AuditLog.timestamp <= end_date
    ).group_by(AuditLog.operation_type, AuditLog.operation_name)\
     .order_by(func.count(AuditLog.id).desc())\
     .limit(10).all()

    dataset_stats = db.query(
        AuditLog.dataset_name,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date,
        AuditLog.timestamp <= end_date,
        AuditLog.dataset_name.isnot(None)
    ).group_by(AuditLog.dataset_name)\
     .order_by(func.count(AuditLog.id).desc())\
     .limit(10).all()

    stats.update({
        'period_days': days,
        'top_operations': [{"type": t[0], "name": t[1], "count": t[2]} for t in type_stats],
        'active_datasets': [{"name": d[0], "operations": d[1]} for d in dataset_stats]
    })

    return {"status": "ok", "data": stats}


@router.post("/export")
async def export_audit_logs(
    format: str = Query("csv", regex="^(csv|json)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    import csv
    import io
    from fastapi.responses import Response

    query = db.query(AuditLog)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)

    logs = query.order_by(AuditLog.timestamp.desc()).all()

    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['时间', '操作类型', '用户', '会话', '数据集', '查询内容', '结果', '状态', 'IP地址'])
        for log in logs:
            writer.writerow([
                log.timestamp.isoformat() if log.timestamp else '',
                log.operation_name,
                log.user_id,
                log.session_id,
                log.dataset_name,
                log.query_content or '',
                log.result_summary or '',
                log.status,
                log.ip_address or ''
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.csv"}
        )

    return {
        "status": "ok",
        "export_time": datetime.now().isoformat(),
        "total_records": len(logs),
        "records": [
            {
                "timestamp": log.timestamp.isoformat(),
                "operation": log.operation_name,
                "user": log.user_id,
                "dataset": log.dataset_name,
                "query": log.query_content,
                "status": log.status
            }
            for log in logs
        ]
    }
