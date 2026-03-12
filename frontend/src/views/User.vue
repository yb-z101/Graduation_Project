<template>
  <div>
    <button @click="getUsers">获取用户列表</button>
    <div v-if="userList.length">{{ userList }}</div>
    <div v-else>暂无数据</div>
  </div>
</template>

<script>
// 导入封装的FastAPI接口
import { getUserList } from '@/api/user';

export default {
  data() {
    return {
      userList: []
    };
  },
  methods: {
    async getUsers() {
      try {
        // 调用接口，传参（适配FastAPI的Query参数）
        const res = await getUserList({ page: 1, size: 10 });
        this.userList = res; // FastAPI直接返回数据，无需res.data（根据后端返回结构调整）
        console.log('后端返回数据：', res);
      } catch (err) {
        console.error('获取用户失败：', err);
      }
    }
  }
};
</script>