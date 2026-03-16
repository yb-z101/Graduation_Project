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
          请上传 CSV 或 Excel 文件
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
import { uploadFile } from '@/api/upload'

const upload = ref(null)
const hasFile = ref(false)

const uploadUrl = '/api/v1/upload'

const beforeUpload = (file) => {
  const isCSV = file.type === 'text/csv' || file.name.endsWith('.csv')
  const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls')
  if (!isCSV && !isExcel) {
    ElMessage.error('只能上传 CSV 或 Excel 文件!')
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
    const response = await uploadFile(file)
    if (response.status === 'ok') {
      ElMessage.success('文件上传成功')
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