<template>
  <!-- 必须保留template标签（哪怕为空），否则编译报错 -->
  <div class="app-container">
    <h1>对话式数据分析系统 - 前端测试页</h1>
    <button @click="testCorsRequest">点击测试跨域请求后端</button>
    <div v-if="responseData" class="response">
      <h3>后端返回结果：</h3>
      <pre>{{ JSON.stringify(responseData, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
// Vue3组合式API，需确保项目安装了vue@3.x
import { ref } from 'vue';

// 定义响应式数据存储后端返回结果
const responseData = ref(null);

// 跨域请求后端接口的方法
const testCorsRequest = async () => {
  try {
    // 调用后端健康检查接口（核心：验证跨域）
    const res = await fetch('http://localhost:8000/health', {
      method: 'GET',
      credentials: 'include', // 对应后端allow_credentials=True
      headers: {
        'Content-Type': 'application/json', // 显式指定请求头（可选，但建议加）
      },
    });

    if (!res.ok) {
      throw new Error(`HTTP错误，状态码：${res.status}`);
    }

    const data = await res.json();
    responseData.value = data; // 把结果赋值到响应式变量
    console.log('跨域请求成功：', data);
  } catch (err) {
    responseData.value = { status: 'error', message: err.message };
    console.error('跨域请求失败：', err);
  }
};
</script>

<style scoped>
/* 可选：简单样式，让页面更易读 */
.app-container {
  width: 80%;
  margin: 50px auto;
  font-family: Arial, sans-serif;
}
button {
  padding: 8px 16px;
  font-size: 16px;
  cursor: pointer;
  margin-bottom: 20px;
}
.response {
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
  background-color: #f9f9f9;
}
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>