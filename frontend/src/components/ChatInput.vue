<template>
  <div class="input-wrapper">
    <!-- 待上传文件列表 -->
    <div v-if="pendingFiles.length > 0" class="pending-files">
      <div 
        v-for="(file, index) in pendingFiles" 
        :key="index"
        class="pending-file-item"
        @click="$emit('preview-file', file)"
      >
        <div class="file-icon">
          <el-icon v-if="file.name.endsWith('.csv')"><Document /></el-icon>
          <el-icon v-else-if="file.name.endsWith('.sql')"><Connection /></el-icon>
          <el-icon v-else-if="file.name.endsWith('.xlsx') || file.name.endsWith('.xls')"><Grid /></el-icon>
        </div>
        <div class="file-info">
          <div class="file-name">{{ file.name }}</div>
          <div class="file-size">{{ formatFileSize(file.size) }}</div>
        </div>
        <div class="file-actions">
          <el-button 
            type="text" 
            size="small"
            @click.stop="removePendingFile(index)"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
    
    <div class="input-container">
      <!-- 输入框（功能按钮内置到底部） -->
      <div class="input-box">
        <!-- 输入区域 -->
        <div class="input-area">
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="1"
            placeholder="发消息或输入'/'选择技能"
            @keyup.enter="handleSendMessage"
            class="chat-input"
            :autosize="{ minRows: 1, maxRows: 4 }"
            :disabled="loading"
          />
          
          <el-button 
            class="send-btn"
            type="primary" 
            :icon="Position" 
            :loading="loading"
            :disabled="(loading)"
            @click="handleSendMessage"
            circle
          />
        </div>

        <!-- 功能按钮栏（内置到底部） -->
        <div class="action-buttons">
          <div class="action-btn" @click="showUploadMenu = !showUploadMenu">
            <div class="btn-content">
              <el-icon><Paperclip /></el-icon>
              <span>传附件</span>
            </div>
            
            <!-- 上传类型选择菜单 -->
            <div v-if="showUploadMenu" class="upload-menu">
              <div class="upload-option" @click="selectFile('csv')">
                <el-icon><Document /></el-icon>
                <span>CSV 文件</span>
              </div>
              <div class="upload-option" @click="selectFile('sql')">
                <el-icon><Connection /></el-icon>
                <span>SQL 文件</span>
              </div>
              <div class="upload-option" @click="selectFile('excel')">
                <el-icon><Grid /></el-icon>
                <span>Excel 文件</span>
              </div>
            </div>
          </div>

          <div class="action-btn" @click="$emit('database-connect')">
            <div class="btn-content">
              <el-icon><Database /></el-icon>
              <span>数据库连接</span>
            </div>
          </div>

          <div class="divider"></div>

          <div class="action-btn" @click="$emit('quick-ask', '数据分析')">
            <div class="btn-content">
              <el-icon><DataAnalysis /></el-icon>
              <span>数据分析</span>
            </div>
          </div>

          <div class="action-btn" @click="$emit('quick-ask', '生成图表')">
            <div class="btn-content">
              <el-icon><Picture /></el-icon>
              <span>生成图表</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { 
  Paperclip, Picture, Position, 
  DataAnalysis, Document, Connection, Grid, Close, Database
} from '@element-plus/icons-vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'send-message',
  'file-select',
  'quick-ask',
  'preview-file',
  'send-with-files',
  'database-connect'
])

const userInput = ref('')
const showUploadMenu = ref(false)
const pendingFiles = ref([])

// 监听外部清除输入的事件
const clearInput = () => {
  userInput.value = ''
  pendingFiles.value = []
}

// 暴露方法
defineExpose({
  clearInput,
  pendingFiles
})

// 处理发送消息
const handleSendMessage = () => {
  if (pendingFiles.value.length > 0) {
    // 有文件待上传，触发发送带文件的消息
    emit('send-with-files', userInput.value, pendingFiles.value)
    // 清空输入和文件列表
    userInput.value = ''
    pendingFiles.value = []
  } else {
    // 无文件，触发普通消息发送
    emit('send-message', userInput.value)
  }
}

// 选择文件
const selectFile = (type) => {
  const fileTypes = {
    csv: '.csv',
    sql: '.sql',
    excel: '.xlsx,.xls'
  }
  
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = fileTypes[type]
  input.onchange = (e) => {
    const file = e.target.files[0]
    if (file) {
      pendingFiles.value.push(file)
      // 触发文件选择事件，用于预览
      emit('file-select', type, file)
    }
  }
  input.click()
  showUploadMenu.value = false
}

// 移除待上传文件
const removePendingFile = (index) => {
  pendingFiles.value.splice(index, 1)
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

// 当上传菜单显示时，点击外部关闭
const handleClickOutside = (event) => {
  if (showUploadMenu.value) {
    const uploadMenu = document.querySelector('.upload-menu')
    const actionBtn = document.querySelector('.action-btn')
    if (uploadMenu && actionBtn && !uploadMenu.contains(event.target) && !actionBtn.contains(event.target)) {
      showUploadMenu.value = false
    }
  }
}

// 监听点击事件
window.addEventListener('click', handleClickOutside)

// 组件卸载时移除事件监听
import { onUnmounted } from 'vue'
onUnmounted(() => {
  window.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.input-wrapper {
  padding: 20px 24px 24px;
  background-color: var(--bg-primary);
}

/* 待上传文件列表 */
.pending-files {
  max-width: 900px;
  margin: 0 auto 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pending-file-item {
  display: flex;
  align-items: center;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 6px 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  white-space: nowrap;
}

.pending-file-item:hover {
  border-color: var(--accent-color);
  box-shadow: 0 2px 4px var(--shadow-color);
}

.file-icon {
  margin-right: 8px;
  color: var(--accent-color);
  font-size: 14px;
}

.file-info {
  min-width: 0;
  margin-right: 8px;
}

.file-name {
  font-size: 12px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.file-size {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
}

.file-actions {
  margin-left: 4px;
}

.file-actions .el-button {
  color: var(--text-muted);
  font-size: 10px;
  padding: 0;
  min-width: 20px;
  height: 20px;
}

.file-actions .el-button:hover {
  color: var(--accent-color);
}

.input-container {
  max-width: 900px;
  margin: 0 auto;
}

.input-box {
  background-color: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 24px;
  padding: 16px 20px;
  transition: all 0.2s;
  box-shadow: 0 2px 10px var(--shadow-color);
}

.input-box:focus-within {
  border-color: var(--accent-color);
  box-shadow: 0 4px 20px var(--shadow-color);
}

.input-area {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.chat-input {
  flex: 1;
}

/* 关键：去掉输入框内嵌白框 */
.chat-input :deep(.el-textarea__inner) {
  background-color: transparent;
  border: none;
  box-shadow: none;
  color: var(--text-primary);
  padding: 0;
  resize: none;
  font-size: 15px;
  line-height: 1.5;
}

.chat-input :deep(.el-textarea__inner):focus {
  border: none;
  box-shadow: none;
  outline: none;
}

.chat-input :deep(.el-textarea__inner)::placeholder {
  color: var(--text-muted);
}

.send-btn {
  background-color: var(--accent-color);
  border: none;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.send-btn:hover {
  background-color: var(--accent-hover);
}

/* 功能按钮栏（内置到底部） */
.action-buttons {
  display: flex;
  gap: 8px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border-color);
  flex-wrap: wrap;
  align-items: center;
}

.action-btn {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 8px 14px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  min-width: fit-content;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background-color: var(--bg-hover);
  border-color: var(--accent-color);
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.action-btn:hover .btn-content {
  color: var(--accent-color);
}

.divider {
  width: 1px;
  height: 20px;
  background-color: var(--border-color);
  margin: 0 4px;
}

/* 上传菜单 */
.upload-menu {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 6px;
  min-width: 160px;
  box-shadow: 0 10px 40px var(--shadow-color);
  z-index: 100;
}

.upload-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 13px;
  color: var(--text-secondary);
}

.upload-option:hover {
  background-color: var(--bg-hover);
  color: var(--accent-color);
}
</style>