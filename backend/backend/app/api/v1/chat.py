from fastapi import APIRouter, Body
from app.services.chat_service import handle_chat_message

router = APIRouter(tags=["普通聊天"])


@router.post("/send")
def send_chat_message(message: str = Body(..., embed=True), model_id: str = Body("ali-qwen", embed=True)):
    """
    发送普通聊天消息，调用大模型进行回复
    """
    return handle_chat_message(message, model_id)
