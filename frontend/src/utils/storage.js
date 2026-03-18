/**
 * 本地存储工具函数
 */

/**
 * 设置本地存储
 * @param {string} key - 存储键名
 * @param {any} value - 存储值
 */
export const setStorage = (key, value) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('Error setting localStorage:', error);
  }
};

/**
 * 获取本地存储
 * @param {string} key - 存储键名
 * @param {any} defaultValue - 默认值
 * @returns {any} 存储值或默认值
 */
export const getStorage = (key, defaultValue = null) => {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : defaultValue;
  } catch (error) {
    console.error('Error getting localStorage:', error);
    return defaultValue;
  }
};

/**
 * 删除本地存储
 * @param {string} key - 存储键名
 */
export const removeStorage = (key) => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Error removing localStorage:', error);
  }
};

/**
 * 清空本地存储
 */
export const clearStorage = () => {
  try {
    localStorage.clear();
  } catch (error) {
    console.error('Error clearing localStorage:', error);
  }
};