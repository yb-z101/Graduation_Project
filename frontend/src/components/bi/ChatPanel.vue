<template>
  <div class="chat-panel">
    <div class="panel-header">
      <span class="panel-title">智能对话</span>
      <span v-if="fileName" class="file-badge">{{ fileName }}</span>
    </div>
    
    <div class="messages-area" ref="messagesAreaRef">
      <div v-if="messages.length === 0" class="welcome-area">
        <div class="welcome-icon">
          <svg viewBox="0 0 80 80" width="80" height="80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="40" cy="40" r="36" fill="#F9F0FF"/>
            <path d="M24 50V32L40 24L56 32V50" stroke="#6B5CE8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M30 44V36M50 44V36M40 44V32" stroke="#6B5CE8" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </div>
        <h3>开启智能数据分析之旅</h3>
        <p>上传文件或连接数据源，开始您的分析</p>
      </div>
      
      <div v-else class="message-list">
        <div v-for="(msg, idx) in messages" :key="idx" class="message-item" :class="msg.role">
          <div class="avatar" :class="msg.role">
            <svg v-if="msg.role === 'user'" viewBox="0 0 40 40" width="40" height="40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="20" cy="20" r="20" fill="#FF7D00"/>
              <circle cx="20" cy="16" r="6" fill="white"/>
              <path d="M10 34C12 28 20 26 20 26C20 26 28 28 30 34" fill="white"/>
            </svg>
            <svg v-else viewBox="0 0 40 40" width="40" height="40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="20" cy="20" r="20" fill="url(#grad1)"/>
              <defs>
                <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#6B5CE8;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#8B7DF2;stop-opacity:1" />
                </linearGradient>
              </defs>
              <rect x="10" y="12" width="20" height="16" rx="2" fill="white"/>
              <path d="M12 18H28M12 22H24" stroke="#6B5CE8" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="30" cy="28" r="4" fill="#8B7DF2"/>
            </svg>
          </div>
          <div class="message-content">
            <div v-if="msg.type === 'code'" class="code-block">
              <div class="code-lang">{{ msg.language || 'code' }}</div>
              <pre><code>{{ msg.content }}</code></pre>
            </div>
            <div v-else class="text-content">{{ msg.content }}</div>
          </div>
        </div>
        
        <div v-if="loading" class="message-item ai">
          <div class="avatar ai">
            <svg viewBox="0 0 40 40" width="40" height="40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="20" cy="20" r="20" fill="url(#grad1)"/>
              <defs>
                <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#6B5CE8;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#8B7DF2;stop-opacity:1" />
                </linearGradient>
              </defs>
              <rect x="10" y="12" width="20" height="16" rx="2" fill="white"/>
              <path d="M12 18H28M12 22H24" stroke="#6B5CE8" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="30" cy="28" r="4" fill="#8B7DF2"/>
            </svg>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="input-area">
      <div class="input-tools">
        <el-upload
          ref="uploadRef"
          class="upload-btn"
          :show-file-list="false"
          :auto-upload="false"
          @change="handleFileChange"
          accept=".csv,.xlsx,.xls,.sql"
        >
          <el-button :icon="Upload" class="upload-file-btn">
            上传文件
          </el-button>
        </el-upload>
      </div>
      
      <div class="format-hint">
        <span class="hint-icon">💡</span>
        <span class="hint-text">支持 CSV、Excel、SQL 三种格式</span>
      </div>
      
      <div class="input-box">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="输入您的分析问题... (Enter发送，Shift+Enter换行)"
          @keydown="handleKeyDown"
          class="message-input"
        />
        <el-button 
          type="primary" 
          :icon="Promotion" 
          @click="handleSend" 
          :loading="loading"
          class="send-btn"
        >
          发送
        </el-button>
      </div>
    </div>

    <el-dialog v-model="showPreviewDialog" title="文件预览" width="680px" :close-on-click-modal="false">
      <div v-if="previewData && previewData.preview" style="padding:8px 0;">
        <div style="display:flex;gap:24px;padding:12px 16px;background:#F5F7FA;border-radius:6px;margin-bottom:12px;font-size:13px;color:#4E5969;">
          <span><b>文件名：</b>{{ previewData.filename }}</span>
          <span><b>行数：</b>{{ previewData.preview?.length || 0 }}</span>
          <span><b>列数：</b>{{ previewData.columns?.length || 0 }}</span>
        </div>
        <el-table :data="previewData.preview || []" size="small" border stripe max-height="320">
          <el-table-column v-for="(col, ci) in (previewData.columns || [])" :key="ci" :prop="col" :label="col" min-width="100" show-overflow-tooltip />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showPreviewDialog = false; previewData = null">取消上传</el-button>
        <el-button type="primary" @click="confirmUpload">确认上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { Upload, Promotion, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  fileName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['send-message', 'file-upload', 'database-connect', 'preview-file'])

const inputText = ref('')
const messagesAreaRef = ref(null)
const uploadRef = ref(null)

const handleFileChange = (uploadFile) => {
  if (!uploadFile || !uploadFile.raw) {
    return
  }

  const file = uploadFile.raw
  const validTypes = ['.csv', '.xlsx', '.xls', '.sql']
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()

  if (!validTypes.includes(ext)) {
    ElMessage.error('只支持 CSV、Excel、SQL 文件')
    return
  }

  emit('preview-file', file, (result) => {
    if (result && result.preview) {
      showPreviewDialog.value = true
      previewData.value = result
    } else {
      emit('file-upload', file)
    }
  })

  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const showPreviewDialog = ref(false)
const previewData = ref(null)

const confirmUpload = () => {
  emit('file-upload', previewData.value?._file)
  showPreviewDialog.value = false
  previewData.value = null
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesAreaRef.value) {
      messagesAreaRef.value.scrollTop = messagesAreaRef.value.scrollHeight
    }
  })
}

watch(() => props.messages, () => {
  scrollToBottom()
}, { deep: true })

const handleKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}

const handleSend = () => {
  if (!inputText.value.trim() || props.loading) return
  emit('send-message', inputText.value)
  inputText.value = ''
}
</script>

<style lang="less" scoped>
.chat-panel {
  height: 100%;
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  .panel-header {
    padding: 20px 24px 16px;
    border-bottom: 1px solid #E5E6EB;
    background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%);
    
    .panel-title {
      font-size: 16px;
      font-weight: 600;
      color: #1D2129;
      letter-spacing: 0.3px;
    }
    
    .file-badge {
      font-size: 12px;
      color: #6B5CE8;
      background: #F9F0FF;
      padding: 3px 12px;
      border-radius: 12px;
      border: 1px solid #E5D7F5;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 200px;
    }
  }
  
  .messages-area {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    background: #F8F9FA;
    
    .welcome-area {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #869099;
      
      .welcome-icon {
        margin-bottom: 20px;
      }
      
      h3 {
        margin: 0 0 10px;
        font-size: 18px;
        color: #1D2129;
        font-weight: 600;
      }
      
      p {
        margin: 0 0 24px;
        font-size: 14px;
        color: #869099;
      }
    }
    
    .message-list {
      .message-item {
        display: flex;
        gap: 14px;
        margin-bottom: 24px;
        
        &.user {
          flex-direction: row-reverse;
          
          .message-content {
            background: linear-gradient(135deg, #6B5CE8 0%, #8B7DF2 100%);
            color: #FFFFFF;
            border-radius: 12px 12px 4px 12px;
            box-shadow: 0 4px 12px rgba(107, 92, 232, 0.25);
          }
        }
        
        .avatar {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          flex-shrink: 0;
          overflow: hidden;
        }
        
        .message-content {
          max-width: 75%;
          padding: 14px 18px;
          background: #F5F7FA;
          border-radius: 12px 12px 12px 4px;
          border: 1px solid #E5E6EB;
          
          .text-content {
            font-size: 14px;
            line-height: 1.7;
            color: #1D2129;
            white-space: pre-wrap;
          }
          
          .code-block {
            .code-lang {
              font-size: 12px;
              color: #869099;
              margin-bottom: 10px;
              text-transform: uppercase;
              font-weight: 600;
              letter-spacing: 1px;
            }
            
            pre {
              margin: 0;
              background: #1D2129;
              padding: 14px 16px;
              border-radius: 8px;
              overflow-x: auto;
              
              code {
                color: #F5F7FA;
                font-size: 13px;
                font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
                line-height: 1.6;
              }
            }
          }
        }
        
        .typing-indicator {
          display: flex;
          gap: 6px;
          padding: 10px 0;
          
          span {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: #6B5CE8;
            animation: typing 1.4s infinite;
            
            &:nth-child(2) {
              animation-delay: 0.2s;
            }
            
            &:nth-child(3) {
              animation-delay: 0.4s;
            }
          }
        }
      }
    }
  }
  
  .input-area {
    padding: 16px 24px 24px;
    border-top: 1px solid #E5E6EB;
    background: #FFFFFF;
    
    .input-tools {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      
      .upload-btn {
        :deep(.el-button) {
          background: linear-gradient(90deg, #6B5CE8, #8B7DF2);
          border: none;
          color: #FFFFFF;
          font-weight: 500;
          padding: 8px 18px;
          border-radius: 8px;
          transition: all 0.2s ease;
          
          &:hover {
            background: linear-gradient(90deg, #5A4BD9, #6B5CE8);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(107, 92, 232, 0.35);
          }
          
          &:active {
            transform: translateY(0);
          }
        }
      }
    }
    
    .format-hint {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      
      .hint-icon {
        font-size: 16px;
      }
      
      .hint-text {
        font-size: 14px;
        color: #869099;
      }
    }
    
    .input-box {
      display: flex;
      gap: 14px;
      align-items: flex-end;
      
      .message-input {
        flex: 1;
        
        :deep(.el-textarea__inner) {
          border-radius: 8px;
          border: 1px solid #E5E6EB;
          transition: all 0.2s ease;
          font-size: 14px;
          line-height: 1.6;
          padding: 12px 16px;
          
          &:hover {
            border-color: #869099;
          }
          
          &:focus {
            border-color: #6B5CE8;
            box-shadow: 0 0 0 3px rgba(107, 92, 232, 0.1);
          }
          
          &::placeholder {
            color: #869099;
          }
        }
      }
      
      .send-btn {
        background: linear-gradient(90deg, #6B5CE8, #8B7DF2);
        border: none;
        color: #FFFFFF;
        font-weight: 600;
        padding: 12px 24px;
        height: auto;
        min-height: 48px;
        transition: all 0.2s ease;
        border-radius: 8px;
        
        &:hover {
          background: linear-gradient(90deg, #5A4BD9, #6B5CE8);
          transform: translateY(-1px);
          box-shadow: 0 6px 16px rgba(107, 92, 232, 0.4);
        }
        
        &:active {
          transform: translateY(0);
        }
      }
    }
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 1;
  }
  30% {
    transform: translateY(-8px);
    opacity: 0.7;
  }
}
</style>