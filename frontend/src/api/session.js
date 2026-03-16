import request from '@/utils/request';

// 发送消息到后端会话接口
export function sendMessage(sessionId, message) {
  return request({
    url: '/api/v1/session/send_message',
    method: 'post',
    data: {
      session_id: sessionId,
      message: message
    }
  });
}

// 获取会话历史
export function getSessionHistory(sessionId) {
  return request({
    url: '/api/v1/session/history',
    method: 'get',
    params: {
      session_id: sessionId
    }
  });
}