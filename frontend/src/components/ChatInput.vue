<template>
  <div class="input-wrapper">
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
            @keyup.enter="$emit('send-message', userInput)"
            class="chat-input"
            :autosize="{ minRows: 1, maxRows: 4 }"
            :disabled="loading"
          />
          
          <el-button 
            class="send-btn"
            type="primary" 
            :icon="Position" 
            :loading="loading"
            :disabled="!userInput.trim() || loading"
            @click="$emit('send-message', userInput)"
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
              <div class="upload-option" @click="$emit('file-select', 'csv')">
                <el-icon><Document /></el-icon>
                <span>CSV 文件</span>
              </div>
              <div class="upload-option" @click="$emit('file-select', 'sql')">
                <el-icon><Connection /></el-icon>
                <span>SQL 文件</span>
              </div>
              <div class="upload-option" @click="$emit('file-select', 'excel')">
                <el-icon><Grid /></el-icon>
                <span>Excel 文件</span>
              </div>
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
  DataAnalysis, Document, Connection, Grid 
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
  'quick-ask'
])

const userInput = ref('')
const showUploadMenu = ref(false)

// 监听外部清除输入的事件
const clearInput = () => {
  userInput.value = ''
}

// 暴露清除输入的方法
defineExpose({
  clearInput
})

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
  padding: 6px 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  min-width: fit-content;
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