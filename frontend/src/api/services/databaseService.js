/**
 * 数据库服务
 * 封装与数据库连接相关的 API 调用
 */
import apiClient from './apiClient';

const databaseService = {
  /**
   * 测试数据库连接
   * @param {Object} connectionInfo - 数据库连接信息
   * @returns {Promise} - 返回 API 响应
   */
  testConnection: (connectionInfo) => {
    return apiClient({
      url: '/v1/database/test-connection',
      method: 'post',
      data: connectionInfo
    });
  },
  
  /**
   * 连接数据库
   * @param {Object} connectionInfo - 数据库连接信息
   * @returns {Promise} - 返回 API 响应
   */
  connectDatabase: (connectionInfo) => {
    return apiClient({
      url: '/v1/database/connect',
      method: 'post',
      data: connectionInfo
    });
  },
  
  /**
   * 获取数据库表结构
   * @param {string} connectionId - 连接ID
   * @returns {Promise} - 返回 API 响应
   */
  getTables: (connectionId) => {
    return apiClient({
      url: `/v1/database/tables/${connectionId}`,
      method: 'get'
    });
  },
  
  /**
   * 执行SQL查询
   * @param {string} connectionId - 连接ID
   * @param {string} query - SQL查询语句
   * @param {number} limit - 返回结果限制行数
   * @returns {Promise} - 返回 API 响应
   */
  executeQuery: (connectionId, query, limit = 1000) => {
    return apiClient({
      url: `/v1/database/query/${connectionId}`,
      method: 'post',
      data: { query, limit }
    });
  },
  
  /**
   * 关闭数据库连接
   * @param {string} connectionId - 连接ID
   * @returns {Promise} - 返回 API 响应
   */
  disconnectDatabase: (connectionId) => {
    return apiClient({
      url: `/v1/database/disconnect/${connectionId}`,
      method: 'post'
    });
  },
  
  /**
   * 将自然语言查询转换为SQL语句
   * @param {string} connectionId - 连接ID
   * @param {string} userQuery - 自然语言查询语句
   * @returns {Promise} - 返回 API 响应
   */
  chatToSql: (connectionId, userQuery) => {
    return apiClient({
      url: `/v1/database/chat-to-sql/${connectionId}`,
      method: 'post',
      data: { user_query: userQuery }
    });
  }
};

export default databaseService;
