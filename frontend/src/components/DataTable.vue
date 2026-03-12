<template>
  <div class="data-table-container">
    <el-table 
      :data="data" 
      style="width: 100%" 
      border 
      max-height="400"
      size="small"
      stripe
    >
      <el-table-column 
        v-for="col in columns" 
        :key="col"
        :prop="col" 
        :label="col"
        :min-width="100"
        show-overflow-tooltip
      />
      
      <!-- 如果没有数据时的提示 -->
      <template #empty>
        <div style="padding: 20px; color: #909399;">
          暂无数据展示
        </div>
      </template>
    </el-table>
  </div>
</template>

<script setup>
// 定义 Props
defineProps({
  // 表格数据数组: [{name: '张三', age: 18}, ...]
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  // 表头列名数组: ['name', 'age']
  columns: {
    type: Array,
    required: true,
    default: () => []
  }
})
</script>

<style scoped>
.data-table-container {
  margin-top: 10px;
  background: #fff;
  border-radius: 4px;
  overflow: hidden;
}
</style>