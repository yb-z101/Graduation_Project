<template>
  <el-upload
    :action="uploadUrl"
    :show-file-list="false"
    :before-upload="beforeUpload"
    :on-success="handleSuccess"
    :on-error="handleError"
    accept=".csv,.xlsx,.xls"
    class="file-uploader-comp"
  >
    <el-button type="primary" :icon="Upload">
      选择文件 (CSV/Excel)
    </el-button>
    <template #tip>
      <div class="el-upload__tip">
        支持 .csv, .xlsx 文件，大小不超过 10MB
      </div>
    </template>
  </el-upload>
</template>

<script setup>
import { Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 定义 emits，用于向父组件传递上传成功后的数据
const emit = defineEmits(['file-uploaded'])

// ⚠️ 重要：请根据您后端的实际接口地址修改此处
// 如果是本地开发，通常配置在 vite.config.js 或 vue.config.js 的 proxy 中
const uploadUrl = '/api/v1/upload' 

const beforeUpload = (file) => {
  // 1. 校验文件类型
  const isValidType = file.name.endsWith('.csv') || 
                      file.name.endsWith('.xlsx') || 
                      file.name.endsWith('.xls')
  
  if (!isValidType) {
    ElMessage.error('只能上传 CSV 或 Excel 文件！')
    return false
  }

  // 2. 校验文件大小 (10MB)
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB！')
    return false
  }

  return true
}

const handleSuccess = (response, uploadFile) => {
  // 假设后端返回格式为: { code: 200, data: { session_id, filename, preview_data, columns } }
  // 请根据实际后端返回结构调整
  if (response.code === 200 || response.status === 'success') {
    ElMessage.success('文件上传成功，正在分析...')
    // 将后端返回的数据传递给父组件 (Chat.vue)
    emit('file-uploaded', response.data || response)
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleError = (err) => {
  console.error('Upload Error:', err)
  ElMessage.error('网络错误，上传失败')
}
</script>

<style scoped>
.file-uploader-comp {
  display: inline-block;
}
.el-upload__tip {
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
}
</style>