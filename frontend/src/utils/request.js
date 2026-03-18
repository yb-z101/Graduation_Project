import axios from 'axios';

// 创建axios实例，指向你的FastAPI后端
const service = axios.create({
  baseURL: '/api', // 使用代理配置
  timeout: 30000, // 请求超时时间
  withCredentials: true // 允许携带Cookie
});

// 请求拦截器：可选，比如添加token、统一处理请求头
service.interceptors.request.use(
  (config) => {
    // 示例：如果后续有登录token，可在这里添加到请求头
    // config.headers.Authorization = `Bearer ${localStorage.getItem('token')}`;
    return config;
  },
  (error) => {
    console.error('请求错误：', error);
    return Promise.reject(error);
  }
);

// 响应拦截器：统一处理后端返回结果
service.interceptors.response.use(
  (response) => {
    // 直接返回后端数据（FastAPI返回的原始数据）
    return response.data;
  },
  (error) => {
    // 统一捕获接口错误
    console.error('响应错误：', error.response?.data || error.message);
    alert(`接口请求失败：${error.message}`);
    return Promise.reject(error);
  }
);

export default service;