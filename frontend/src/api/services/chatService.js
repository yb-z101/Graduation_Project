import apiClient from './apiClient';

/**
 * 聊天服务
 * 封装与聊天相关的 API 调用
 */
const chatService = {
  /**
   * 发送普通聊天消息
   * @param {string} message - 消息内容
   * @returns {Promise} - 返回 API 响应
   */
  sendChatMessage: (message) => {
    return apiClient({
      url: '/v1/chat/send',
      method: 'post',
      data: {
        message
      }
    });
  }
};

export default chatService;