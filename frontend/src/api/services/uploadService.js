import apiClient from './apiClient';

/**
 * 上传服务
 * 封装与文件上传相关的 API 调用
 */
const uploadService = {
  /**
   * 上传文件
   * @param {File} file - 要上传的文件
   * @param {string} sessionId - 会话 ID（可选）
   * @returns {Promise} - 返回 API 响应
   */
  uploadFile: (file, sessionId = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }
    
    return apiClient({
      url: '/v1/upload',
      method: 'post',
      data: formData,
      // 当使用FormData时，不要手动设置Content-Type，让浏览器自动处理
      // 可以在这里添加上传进度监听
      // onUploadProgress: (progressEvent) => {
      //   const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      //   console.log('上传进度:', percentCompleted);
      // }
    });
  },
  
  /**
   * 预览文件结构
   * @param {File} file - 要预览的文件
   * @returns {Promise} - 返回 API 响应
   */
  previewFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient({
      url: '/v1/preview',
      method: 'post',
      data: formData
      // 当使用FormData时，不要手动设置Content-Type，让浏览器自动处理
    });
  }
};

export default uploadService;