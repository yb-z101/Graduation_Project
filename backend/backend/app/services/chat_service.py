from fastapi import HTTPException
from app.utils.llm_client import call_qwen


def handle_chat_message(message: str) -> dict:
    """处理普通聊天消息，调用大模型进行回复"""
    try:
        # 调用大模型进行回复
        response = call_qwen(message)
        return {
            "status": "ok",
            "message": "消息处理成功",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")