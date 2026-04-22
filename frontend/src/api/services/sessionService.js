import apiClient from './apiClient';

/**
 * 会话服务
 * 封装与会话相关的 API 调用
 */
const sessionService = {
  /**
   * 发送消息到会话
   * @param {string} sessionId - 会话 ID
   * @param {string} message - 消息内容
   * @param {string} modelId - 模型 ID
   * @returns {Promise} - 返回 API 响应
   */
  sendMessage: (sessionId, message, modelId = 'ali-qwen') => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('message', message);
    formData.append('model_id', modelId);
    
    return apiClient({
      url: '/v1/session/send_message',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 获取历史会话列表
   * @returns {Promise} - 返回 API 响应
   */
  getSessionHistory: () => {
    return apiClient({
      url: '/v1/session/history',
      method: 'get'
    });
  },

  /**
   * 获取指定会话的完整对话消息
   * @param {string} sessionId - 会话 ID
   * @param {number} limit - 消息数量限制
   * @returns {Promise} - 返回 API 响应
   */
  getSessionMessages: (sessionId, limit = 200) => {
    return apiClient({
      url: '/v1/session/messages',
      method: 'get',
      params: {
        session_id: sessionId,
        limit
      }
    });
  },

  /**
   * 删除指定会话
   * @param {string} sessionId - 会话 ID
   * @returns {Promise} - 返回 API 响应
   */
  deleteSession: (sessionId) => {
    return apiClient({
      url: `/v1/session/${sessionId}`,
      method: 'delete'
    });
  },

  /**
   * 清空全部会话
   * @returns {Promise} - 返回 API 响应
   */
  clearAllSessions: () => {
    return apiClient({
      url: '/v1/session',
      method: 'delete'
    });
  },

  /**
   * 清洗会话数据
   * @param {string} sessionId - 会话 ID
   * @param {string} cleanInstruction - 清洗指令
   * @param {string} taskName - 任务名称
   * @returns {Promise} - 返回 API 响应
   */
  cleanSessionData: (sessionId, cleanInstruction, taskName) => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('clean_instruction', cleanInstruction);
    if (taskName) {
      formData.append('task_name', taskName);
    }
    
    return apiClient({
      url: '/v1/session/clean',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  getInsights: (sessionId, modelId = 'ali-qwen') => {
    return apiClient({
      url: `/sessions/${sessionId}/insights`,
      method: 'get',
      params: { model_id: modelId },
      timeout: 60000
    });
  },

  getDataProfile: (sessionId) => {
    return apiClient({
      url: '/v1/session/data_profile',
      method: 'get',
      params: { session_id: sessionId }
    });
  }
};

export default sessionService;