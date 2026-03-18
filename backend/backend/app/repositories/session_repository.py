from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Session as SessionModel, SessionMessage


class SessionRepository:
    """会话数据访问类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, session: SessionModel) -> SessionModel:
        """创建会话"""
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_session_by_id(self, session_id: str) -> Optional[SessionModel]:
        """根据ID获取会话"""
        return self.db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.is_deleted == False
        ).first()
    
    def get_all_sessions(self, limit: int = 5) -> List[SessionModel]:
        """获取所有会话"""
        return self.db.query(SessionModel).filter(
            SessionModel.is_deleted == False
        ).order_by(
            SessionModel.create_time.desc()
        ).limit(limit).all()
    
    def update_session(self, session: SessionModel) -> SessionModel:
        """更新会话"""
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话（软删除）"""
        session = self.get_session_by_id(session_id)
        if not session:
            return False
        
        # 软删除会话
        session.is_deleted = True
        
        # 软删除相关消息
        self.db.query(SessionMessage).filter(
            SessionMessage.session_id == session_id,
            SessionMessage.is_deleted == False
        ).update({"is_deleted": True}, synchronize_session=False)
        
        self.db.commit()
        return True
    
    def delete_all_sessions(self) -> bool:
        """删除所有会话（软删除）"""
        # 软删除全部会话
        self.db.query(SessionModel).filter(SessionModel.is_deleted == False).update(
            {"is_deleted": True}, synchronize_session=False
        )
        
        # 软删除全部会话消息
        self.db.query(SessionMessage).filter(SessionMessage.is_deleted == False).update(
            {"is_deleted": True}, synchronize_session=False
        )
        
        self.db.commit()
        return True
    
    def create_session_message(self, message: SessionMessage) -> SessionMessage:
        """创建会话消息"""
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_session_messages(self, session_id: str, limit: int = 200) -> List[SessionMessage]:
        """获取会话消息"""
        return self.db.query(SessionMessage).filter(
            SessionMessage.session_id == session_id,
            SessionMessage.is_deleted == False
        ).order_by(SessionMessage.create_time.asc()).limit(limit).all()
    
    def get_last_session_message(self, session_id: str) -> Optional[SessionMessage]:
        """获取会话最后一条消息"""
        return self.db.query(SessionMessage).filter(
            SessionMessage.session_id == session_id,
            SessionMessage.is_deleted == False
        ).order_by(SessionMessage.create_time.desc()).first()
    
    def get_last_user_message(self, session_id: str) -> Optional[SessionMessage]:
        """获取会话最后一条用户消息"""
        return self.db.query(SessionMessage).filter(
            SessionMessage.session_id == session_id,
            SessionMessage.role == 1,
            SessionMessage.is_deleted == False
        ).order_by(SessionMessage.create_time.desc()).first()
