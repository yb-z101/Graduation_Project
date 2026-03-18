import request from '@/utils/request';

// 发送消息到后端会话接口
export function sendMessage(sessionId, message) {
  // 创建 FormData 对象
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('message', message);
  
  return request({
    url: '/v1/session/send_message',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}

// 获取会话历史
export function getSessionHistory() {
  return request({
    url: '/v1/session/history',
    method: 'get'
  });
}

// 获取指定会话的完整对话消息（用于恢复上下文）
export function getSessionMessages(sessionId, limit = 200) {
  return request({
    url: '/v1/session/messages',
    method: 'get',
    params: {
      session_id: sessionId,
      limit
    }
  });
}

// 删除指定会话
export function deleteSession(sessionId) {
  return request({
    url: `/v1/session/${sessionId}`,
    method: 'delete'
  });
}

// 清空全部会话
export function clearAllSessions() {
  return request({
    url: '/v1/session',
    method: 'delete'
  });
}