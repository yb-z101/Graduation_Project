<template>
  <div class="file-uploader">
    <el-upload
      class="upload-demo"
      :action="uploadUrl"
      :on-success="handleSuccess"
      :on-error="handleError"
      :before-upload="beforeUpload"
      :auto-upload="false"
      ref="upload"
    >
      <el-button type="primary">
        <el-icon><Upload /></el-icon>
        选择文件
      </el-button>
      <template #tip>
        <div class="el-upload__tip">
          请上传 CSV、Excel 或 SQL 文件
        </div>
      </template>
    </el-upload>
    <el-button type="success" @click="submitUpload" :disabled="!hasFile">
      上传
    </el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { uploadService } from '@/api/services'

const upload = ref(null)
const hasFile = ref(false)

const uploadUrl = '/api/v1/upload'

const beforeUpload = (file) => {
  const isCSV = file.type === 'text/csv' || file.name.endsWith('.csv')
  const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls')
  const isSQL = file.name.endsWith('.sql')
  if (!isCSV && !isExcel && !isSQL) {
    ElMessage.error('只能上传 CSV、Excel 或 SQL 文件!')
    return false
  }
  hasFile.value = true
  return false // 阻止自动上传
}

const submitUpload = async () => {
  if (!upload.value) return
  
  const files = upload.value.uploadFiles
  if (files.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  const file = files[0].raw
    try {
      ElMessage.info('正在上传文件...')
      const response = await uploadService.uploadFile(file)
      if (response.status === 'ok') {
        // 详细的成功提示
        const rowCount = response.row_count ? `共 ${response.row_count} 条数据` : ''
        ElMessage.success({
          message: `✅ ${file.name} 上传成功！${rowCount}`,
          duration: 1000,
          showClose: true
        })
        // 触发上传成功事件，传递会话信息
        emit('upload-success', response)
        // 清空上传列表
        upload.value.clearFiles()
        hasFile.value = false
      } else {
        ElMessage.error(`上传失败：${response.message || '未知错误'}`)
      }
    } catch (error) {
      ElMessage.error(`上传失败：${error.message || '网络错误'}`)
      console.error('上传错误：', error)
    }
}

const handleSuccess = (response) => {
  // 这个方法不会被调用，因为我们使用了手动上传
}

const handleError = (error) => {
  ElMessage.error('上传失败，请重试')
  console.error('上传错误：', error)
}

// 定义事件
const emit = defineEmits(['upload-success'])
</script>

<style scoped>
.file-uploader {
  margin: 20px 0;
}

.upload-demo {
  margin-right: 10px;
}
</style>