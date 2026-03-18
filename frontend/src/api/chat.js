import request from '@/utils/request';

// 发送普通聊天消息到后端
// 注意：这里需要实现后端的普通聊天接口
export function sendChatMessage(message) {
  return request({
    url: '/v1/chat/send',
    method: 'post',
    data: {
      message: message
    },
    headers: {
      'Content-Type': 'application/json'
    }
  });
}
