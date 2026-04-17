import json
import hashlib
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogger:
    OP_TYPE = {
        'SESSION_CREATE': '创建会话',
        'SESSION_DELETE': '删除会话',
        'SESSION_SWITCH': '切换会话',
        'FILE_UPLOAD': '文件上传',
        'DATABASE_CONNECT': '数据库连接',
        'DATABASE_DISCONNECT': '断开数据库',
        'TABLE_QUERY': '表数据查询',
        'CHAT_SEND': '发送分析查询',
        'CHAT_RESPONSE': 'AI回复生成',
        'CHART_GENERATE': '图表生成',
        'DATA_CLEAN': '数据清洗',
        'SQL_EXECUTE': 'SQL执行',
        'DATA_EXPORT': '数据导出',
        'REPORT_EXPORT': '报告导出'
    }

    def __init__(self, db: Session = None):
        self.db = db
        self._buffer: List[Dict] = []
        self._buffer_size = 10

    def log(self, operation_type: str, user_id: Optional[str] = None,
             session_id: Optional[str] = None, dataset_name: Optional[str] = None,
             dataset_type: Optional[str] = None, query_content: Optional[str] = None,
             result_summary: Optional[str] = None, status: str = 'success',
             error_message: Optional[str] = None, ip_address: Optional[str] = None,
             user_agent: Optional[str] = None, extra_data: Optional[Dict] = None,
             sensitivity_level: int = 0):

        log_entry = {
            'id': f"audit_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(datetime.now()) % 10000:04d}",
            'timestamp': datetime.now().isoformat(),
            'operation_type': operation_type,
            'operation_name': self.OP_TYPE.get(operation_type, operation_type),
            'user_id': user_id or 'anonymous',
            'session_id': session_id,
            'dataset_name': self._sanitize(dataset_name),
            'dataset_type': dataset_type,
            'query_content': self._sanitize_query(query_content, sensitivity_level),
            'query_hash': self._hash(query_content) if query_content else None,
            'result_summary': self._truncate(result_summary, 500),
            'status': status,
            'error_message': self._truncate(error_message, 1000) if error_message else None,
            'ip_address': ip_address,
            'user_agent': self._truncate(user_agent, 500),
            'extra_data': json.dumps(extra_data, ensure_ascii=False) if extra_data else None,
            'sensitivity_level': sensitivity_level,
            'server_hostname': 'local'
        }

        self._buffer.append(log_entry)
        if len(self._buffer) >= self._buffer_size:
            self.flush()

    def flush(self):
        if not self._buffer or not self.db:
            return

        try:
            for entry in self._buffer:
                record = AuditLog(
                    id=entry['id'],
                    timestamp=datetime.fromisoformat(entry['timestamp']),
                    operation_type=entry['operation_type'],
                    operation_name=entry['operation_name'],
                    user_id=entry['user_id'],
                    session_id=entry['session_id'],
                    dataset_name=entry['dataset_name'],
                    dataset_type=entry['dataset_type'],
                    query_content=entry['query_content'],
                    query_hash=entry['query_hash'],
                    result_summary=entry['result_summary'],
                    status=entry['status'],
                    error_message=entry['error_message'],
                    ip_address=entry['ip_address'],
                    user_agent=entry['user_agent'],
                    extra_data=entry['extra_data'],
                    sensitivity_level=entry['sensitivity_level']
                )
                self.db.add(record)

            self.db.commit()
            self._buffer.clear()
        except Exception as e:
            print(f"[AUDIT-ERROR] 写入失败: {e}")
            self.db.rollback()

    @staticmethod
    def _sanitize(name: Optional[str]) -> Optional[str]:
        if not name:
            return name
        import os
        return os.path.basename(name)

    @staticmethod
    def _sanitize_query(query: Optional[str], sensitivity: int = 0) -> Optional[str]:
        if not query:
            return None
        if sensitivity >= 2:
            return f"[SENSITIVE] length={len(query)}"
        elif sensitivity == 1:
            return query[:50] + "..." if len(query) > 50 else query
        return query[:500] if len(query) > 500 else query

    @staticmethod
    def _hash(content: str) -> str:
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def _truncate(text: Optional[str], max_length: int) -> Optional[str]:
        if not text:
            return None
        return text[:max_length] + "..." if len(text) > max_length else text

    def get_stats(self, start_date: datetime, end_date: datetime) -> Dict:
        if not self.db:
            return {}
        from sqlalchemy import func
        stats = self.db.query(
            func.count(AuditLog.id).label('total'),
            func.sum(func.case((AuditLog.status == 'success', 1), else_=0)).label('success_count'),
            func.sum(func.case((AuditLog.status == 'failure', 1), else_=0)).label('failure_count')
        ).filter(
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        ).first()
        total = stats.total or 0
        return {
            'total_operations': total,
            'success_count': stats.success_count or 0,
            'failure_count': stats.failure_count or 0,
            'success_rate': round((stats.success_count or 0) / max(total, 1) * 100, 2)
        }


_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(db: Session = None) -> AuditLogger:
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger(db)
    elif db is not None:
        _global_audit_logger.db = db
    return _global_audit_logger
