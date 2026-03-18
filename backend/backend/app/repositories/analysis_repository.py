from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import AnalysisTask, ChatRecord


class AnalysisRepository:
    """分析任务数据访问类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_analysis_task(self, task: AnalysisTask) -> AnalysisTask:
        """创建分析任务"""
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_task_by_id(self, task_id: int) -> Optional[AnalysisTask]:
        """根据ID获取分析任务"""
        return self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    
    def get_all_tasks(self, limit: int = 10) -> List[AnalysisTask]:
        """获取所有分析任务"""
        return self.db.query(AnalysisTask).order_by(AnalysisTask.create_time.desc()).limit(limit).all()
    
    def update_task(self, task: AnalysisTask) -> AnalysisTask:
        """更新分析任务"""
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def create_chat_record(self, record: ChatRecord) -> ChatRecord:
        """创建聊天记录"""
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def get_chat_records_by_task_id(self, task_id: int) -> List[ChatRecord]:
        """根据任务ID获取聊天记录"""
        return self.db.query(ChatRecord).filter(
            ChatRecord.task_id == task_id
        ).order_by(ChatRecord.create_time.asc()).all()
