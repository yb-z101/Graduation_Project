import axios from 'axios';

/**
 * 创建 API 客户端实例
 * @param {Object} config - 配置选项
 * @returns {AxiosInstance} - API 客户端实例
 */
const createApiClient = (config = {}) => {
  const defaultConfig = {
    baseURL: '/api',
    timeout: 30000,
    withCredentials: true,
    ...config
  };

  const apiClient = axios.create(defaultConfig);

  // 请求拦截器
  apiClient.interceptors.request.use(
    (config) => {
      // 可以在这里添加认证信息等
      // const token = localStorage.getItem('token');
      // if (token) {
      //   config.headers.Authorization = `Bearer ${token}`;
      // }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // 响应拦截器
  apiClient.interceptors.response.use(
    (response) => {
      return response.data;
    },
    (error) => {
      // 统一错误处理
      const errorMessage = error.response?.data?.message || error.message || '请求失败';
      console.error('API 错误:', errorMessage);
      
      // 可以在这里添加错误通知等
      // ElMessage.error(errorMessage);
      
      return Promise.reject(error);
    }
  );

  return apiClient;
};

// 创建默认 API 客户端
const apiClient = createApiClient();

export { createApiClient, apiClient };
export default apiClient;