<template>
  <div class="data-table-container">
    <el-table 
      :data="data" 
      style="width: 100%" 
      border 
      max-height="500"
      size="default"
      stripe
      :fit="true"
    >
      <el-table-column 
        v-for="col in columns" 
        :key="col"
        :prop="col" 
        :label="col"
        :min-width="120"
        show-overflow-tooltip
        resizable
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

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  color: #303133;
  font-weight: 600;
}

:deep(.el-table .cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>