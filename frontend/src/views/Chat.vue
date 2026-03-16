<template>
  <div class="ai-chat-container" :class="themeClass">
    <!-- 左侧侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <!-- 收起按钮 -->
      <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
        <el-icon :class="{ 'flipped': sidebarCollapsed }"><Fold /></el-icon>
      </div>

      <div class="sidebar-top" v-show="!sidebarCollapsed">
        <el-button class="new-chat-btn" @click="startNewChat">
          <el-icon><Plus /></el-icon>
          <span>新建对话</span>
        </el-button>
      </div>

      <div class="sidebar-history" v-show="!sidebarCollapsed">
        <div class="history-group">
          <div class="group-title">最近会话</div>
          <div 
            v-for="session in (sessionStore.sessions || []).slice(0, 5)" 
            :key="session.id"
            class="history-item"
            :class="{ active: session.id === sessionStore.currentSessionId }"
            @click="loadSession(session)"
          >
            <el-icon><ChatLineRound /></el-icon>
            <span class="text-truncate">{{ session.fileName }}</span>
          </div>
        </div>
        
        <div class="history-group" v-if="(sessionStore.sessions || []).length > 5">
          <div class="group-title">历史存档</div>
          <div 
            v-for="session in (sessionStore.sessions || []).slice(5)" 
            :key="session.id"
            class="history-item"
            :class="{ active: session.id === sessionStore.currentSessionId }"
            @click="loadSession(session)"
          >
            <el-icon><Folder /></el-icon>
            <span class="text-truncate">{{ session.fileName }}</span>
          </div>
        </div>

        <div v-if="(sessionStore.sessions || []).length === 0" class="empty-history">
          <span>暂无历史对话</span>
        </div>
      </div>

      <div class="sidebar-bottom" v-show="!sidebarCollapsed">
        <!-- 主题选择器 -->
        <div class="theme-selector" @click="showThemeDropdown = !showThemeDropdown">
          <el-icon><Moon v-if="theme === 'dark'" /><Sunny v-else /></el-icon>
          <span>{{ theme === 'dark' ? '深色' : '浅色' }}</span>
          <el-icon :class="{ 'rotate': showThemeDropdown }"><ArrowDown /></el-icon>
          
          <div v-if="showThemeDropdown" class="theme-dropdown">
            <div 
              class="theme-option"
              :class="{ active: theme === 'dark' }"
              @click="theme = 'dark'; showThemeDropdown = false"
            >
              <el-icon><Moon /></el-icon>
              <span>深色模式</span>
              <el-icon v-if="theme === 'dark'"><Check /></el-icon>
            </div>
            <div 
              class="theme-option"
              :class="{ active: theme === 'light' }"
              @click="theme = 'light'; showThemeDropdown = false"
            >
              <el-icon><Sunny /></el-icon>
              <span>浅色模式</span>
              <el-icon v-if="theme === 'light'"><Check /></el-icon>
            </div>
          </div>
        </div>

        <!-- 用户信息 -->
        <div class="user-profile">
          <div class="avatar">
            <el-avatar :size="32" :style="{ backgroundColor: themeAccent }">JS</el-avatar>
          </div>
          <div class="info">
            <div class="name">数据分析师</div>
            <div class="email">Pro 版本</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="top-bar">
        <!-- 模型选择器 -->
        <div class="model-selector" @click="showModelDropdown = !showModelDropdown">
          <span class="model-icon">
            <el-icon><Cpu /></el-icon>
          </span>
          <span class="model-name">{{ currentModel.name }}</span>
          <el-icon :class="{ 'rotate': showModelDropdown }"><ArrowDown /></el-icon>
          
          <div v-if="showModelDropdown" class="model-dropdown">
            <div 
              v-for="model in modelList" 
              :key="model.id"
              class="model-option"
              :class="{ active: currentModel.id === model.id }"
              @click="selectModel(model)"
            >
              <div class="option-info">
                <div class="option-name">{{ model.name }}</div>
                <div class="option-desc">{{ model.description }}</div>
              </div>
              <el-icon v-if="currentModel.id === model.id"><Check /></el-icon>
            </div>
          </div>
        </div>

        <div class="header-actions">
          <el-button link :icon="Share" title="分享" />
          <el-button link :icon="Delete" title="清空" @click="clearChat" />
        </div>
      </header>

      <!-- 聊天内容区 -->
      <div class="chat-scroll-area" ref="chatWindowRef">
        <!-- 空状态 / 欢迎页 -->
        <div v-if="messages.length === 0" class="welcome-container">
          <div class="welcome-logo">
            <div class="logo-icon" :style="{ background: themeGradient }">
              <el-icon :size="40"><DataAnalysis /></el-icon>
            </div>
          </div>
          <h2 class="welcome-title">今天我能帮您分析什么？</h2>
          <p class="welcome-subtitle">上传数据文件，开始智能分析之旅</p>
        </div>

        <!-- 消息列表 -->
        <div v-else class="message-list">
          <div 
            v-for="(msg, index) in messages" 
            :key="index" 
            class="message-row"
            :class="msg.role"
          >
            <div class="message-avatar">
              <el-avatar :icon="msg.role === 'user' ? UserFilled : Service" :size="36" :class="msg.role" />
            </div>
            <div class="message-body">
              <div class="message-name">{{ msg.role === 'user' ? '您' : 'AI 助手' }}</div>
              <div class="message-content">
                <div v-if="msg.role === 'user'" class="user-text">{{ msg.content }}</div>
                
                <div v-else class="ai-content">
                  <p v-if="msg.type === 'text' || !msg.type">{{ msg.content }}</p>
                  
                  <div v-if="msg.type === 'table'" class="content-block">
                    <div class="block-title">{{ msg.title || '数据表格' }}</div>
                    <DataTable :data="msg.data" :columns="msg.columns" />
                  </div>

                  <div v-if="msg.type === 'chart'" class="content-block">
                    <div class="block-title">{{ msg.title || '数据图表' }}</div>
                    <DataChart :option="msg.chartOption" />
                  </div>
                  
                  <p v-if="msg.textPart" class="text-part">{{ msg.textPart }}</p>
                </div>
              </div>
            </div>
          </div>

          <div v-if="chatStore.isLoading" class="message-row ai">
            <div class="message-avatar">
              <el-avatar :icon="Service" :size="36" class="ai" />
            </div>
            <div class="message-body">
              <div class="message-name">AI 助手</div>
              <div class="message-content loading">
                <el-skeleton animated :rows="3" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部输入区 -->
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
                @keyup.enter="sendMessage"
                class="chat-input"
                :autosize="{ minRows: 1, maxRows: 4 }"
              />
              
              <el-button 
                class="send-btn"
                type="primary" 
                :icon="Position" 
                :loading="chatStore.isLoading"
                :disabled="!userInput.trim()"
                @click="sendMessage"
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
                  <div class="upload-option" @click="handleFileSelect('csv')">
                    <el-icon><Document /></el-icon>
                    <span>CSV 文件</span>
                  </div>
                  <div class="upload-option" @click="handleFileSelect('sql')">
                    <el-icon><Connection /></el-icon>
                    <span>SQL 文件</span>
                  </div>
                  <div class="upload-option" @click="handleFileSelect('excel')">
                    <el-icon><Grid /></el-icon>
                    <span>Excel 文件</span>
                  </div>
                </div>
              </div>

              <div class="divider"></div>

              <div class="action-btn" @click="quickAsk('数据分析')">
                <div class="btn-content">
                  <el-icon><DataAnalysis /></el-icon>
                  <span>数据分析</span>
                </div>
              </div>

              <div class="action-btn" @click="quickAsk('生成图表')">
                <div class="btn-content">
                  <el-icon><Picture /></el-icon>
                  <span>生成图表</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 点击外部关闭下拉 -->
    <div v-if="showModelDropdown || showThemeDropdown || showUploadMenu" class="dropdown-mask" @click="closeAllDropdowns"></div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted, watch } from 'vue'
import { 
  Plus, ChatLineRound, Folder, Share, Delete, ArrowDown, Check,
  DataAnalysis, UserFilled, Service, Paperclip, Picture, Position,
  Cpu, Moon, Sunny, Fold, Document, Connection, Grid
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import DataTable from '../components/DataTable.vue'
import DataChart from '../components/DataChart.vue'

import { useSessionStore } from '../store/sessionStore'
import { useChatStore } from '../store/chatStore'

// 导入 API 模块
import { sendMessage as sendMessageApi } from '../api/session'
import { uploadFile } from '../api/upload'

const sessionStore = useSessionStore()
const chatStore = useChatStore()

const userInput = ref('')
const messages = ref([])
const chatWindowRef = ref(null)
const sidebarCollapsed = ref(false)
const showModelDropdown = ref(false)
const showThemeDropdown = ref(false)
const showUploadMenu = ref(false)

// 单个提示框管理
let messageTimer = null
const showMessage = (message, type = 'info') => {
  if (messageTimer) {
    clearTimeout(messageTimer)
  }
  
  ElMessage.closeAll()
  
  const msgInstance = ElMessage({
    message,
    type,
    duration: 3000,
    offset: 20
  })
  
  messageTimer = setTimeout(() => {
    msgInstance.close()
  }, 3000)
}

const theme = ref('dark')
const themeClass = computed(() => theme.value === 'dark' ? 'theme-dark' : 'theme-light')
const themeAccent = computed(() => theme.value === 'dark' ? '#6366f1' : '#4f46e5')
const themeGradient = computed(() => theme.value === 'dark' 
  ? 'linear-gradient(135deg, #6366f1, #a855f7)' 
  : 'linear-gradient(135deg, #4f46e5, #7c3aed)')

const modelList = ref([
  { id: 'pro', name: 'Data-Analysis-Pro', description: '最强数据分析能力，适合复杂任务' },
  { id: 'plus', name: 'Data-Analysis-Plus', description: '平衡速度与质量，日常推荐' },
  { id: 'lite', name: 'Data-Analysis-Lite', description: '快速响应，适合简单查询' }
])

const currentModel = ref(modelList.value[0])

const closeAllDropdowns = () => {
  showModelDropdown.value = false
  showThemeDropdown.value = false
  showUploadMenu.value = false
}

const selectModel = (model) => {
  currentModel.value = model
  showModelDropdown.value = false
  showMessage(`已切换到 ${model.name}`, 'success')
}

const startNewChat = () => {
  messages.value = []
  sessionStore.currentSessionId = null
  userInput.value = ''
}

const clearChat = () => {
  if(confirm('确定清空当前对话吗？')) {
    startNewChat()
  }
}

const loadSession = (session) => {
  // 注意：实际场景中可能需要从后端加载历史消息
  sessionStore.setCurrentSession(session.id, session.fileName, [], [])
  messages.value = [{
    role: 'ai',
    type: 'text',
    content: `已加载会话：${session.fileName}`
  }]
  scrollToBottom()
}

const quickAsk = (text) => {
  userInput.value = text
  sendMessage()
}

// 修改后的文件选择与上传逻辑
const handleFileSelect = (type) => {
  showUploadMenu.value = false
  
  const fileTypes = {
    csv: '.csv',
    sql: '.sql',
    excel: '.xlsx,.xls'
  }
  
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = fileTypes[type]
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (file) {
      try {
        showMessage('正在上传文件...', 'info')
        // 调用真实上传 API
        const response = await uploadFile(file)
        
        if (response.status === 'ok') {
          handleFileUploaded({
            fileName: file.name,
            previewData: response.data || [],
            columns: response.columns || []
          })
        } else {
          showMessage(`上传失败：${response.message}`, 'error')
        }
      } catch (error) {
        showMessage('文件上传失败', 'error')
        console.error('上传错误：', error)
      }
    }
  }
  input.click()
}

// 处理上传成功后的逻辑
const handleFileUploaded = async (responseData) => {
  // 注意：这里仍然使用生成的 mockSessionId，实际项目中 sessionId 通常由上传接口返回
  const mockSessionId = 'sess_' + Date.now()
  const fileName = responseData.fileName || 'uploaded_data.csv'
  
  sessionStore.setCurrentSession(mockSessionId, fileName, responseData.previewData || [], responseData.columns || [])
  sessionStore.addSession({ id: mockSessionId, fileName, timestamp: new Date() })

  messages.value.push({
    role: 'ai',
    type: 'text',
    content: `文件《${fileName}》已上传。共 ${responseData.previewData?.length || 0} 条数据。`
  })
  scrollToBottom()
  showMessage('文件上传成功', 'success')
}

// 修改后的发送消息逻辑
const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text) return

  if (!sessionStore.currentSessionId && messages.value.length === 0) {
    showMessage('请先上传数据文件', 'warning')
    return
  }

  // 添加用户消息到列表
  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  chatStore.setLoading(true)
  scrollToBottom()

  try {
    // 调用真实发送消息 API
    const response = await sendMessageApi(sessionStore.currentSessionId, text)
    
    if (response.status === 'ok') {
      const aiMessage = {
        role: 'ai',
        type: response.chart_option ? 'chart' : 'text',
        content: response.error || '分析完成',
        chartOption: response.chart_option,
        textPart: response.error || `分析完成，共 ${response.result?.length || 0} 条结果`
      }
      messages.value.push(aiMessage)
    } else {
      messages.value.push({
        role: 'ai',
        type: 'text',
        content: `错误：${response.message || '处理失败'}`
      })
    }
  } catch (error) {
    showMessage('消息发送失败', 'error')
    messages.value.push({
      role: 'ai',
      type: 'text',
      content: `错误：${error.message}`
    })
  } finally {
    chatStore.setLoading(false)
    nextTick(() => scrollToBottom())
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindowRef.value) {
      chatWindowRef.value.scrollTop = chatWindowRef.value.scrollHeight
    }
  })
}

onMounted(() => {
  const savedTheme = localStorage.getItem('chat-theme')
  if (savedTheme) {
    theme.value = savedTheme
  }
})

watch(theme, (newVal) => {
  localStorage.setItem('chat-theme', newVal)
})
</script>

<style scoped>
.theme-dark {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-hover: #334155;
  --bg-input: #1e293b;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --border-color: #334155;
  --accent-color: #6366f1;
  --accent-hover: #4f46e5;
  --message-user-bg: #334155;
  --shadow-color: rgba(0, 0, 0, 0.3);
}

.theme-light {
  --bg-primary: #f8fafc;
  --bg-secondary: #ffffff;
  --bg-hover: #f1f5f9;
  --bg-input: #ffffff;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --border-color: #e2e8f0;
  --accent-color: #4f46e5;
  --accent-hover: #4338ca;
  --message-user-bg: #4f46e5;
  --shadow-color: rgba(0, 0, 0, 0.08);
}

.ai-chat-container {
  display: flex;
  height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  transition: all 0.3s ease;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background-color: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
  flex-shrink: 0;
  transition: width 0.3s ease;
  position: relative;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-toggle {
  position: absolute;
  top: 16px;
  right: -12px;
  width: 24px;
  height: 24px;
  background-color: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s;
  color: var(--text-secondary);
}

.sidebar-toggle:hover {
  background-color: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

.sidebar-toggle .el-icon {
  transition: transform 0.3s;
}

.sidebar-toggle .flipped {
  transform: rotate(180deg);
}

.sidebar-top {
  padding: 16px;
}

.new-chat-btn {
  width: 100%;
  background-color: var(--accent-color);
  color: white;
  border: none;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  background-color: var(--accent-hover);
}

.sidebar-history {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
}

.history-group {
  margin-bottom: 24px;
}

.group-title {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 8px 12px;
  font-weight: 600;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 14px;
  transition: background 0.2s;
}

.history-item:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.history-item.active {
  background-color: var(--bg-hover);
  color: var(--accent-color);
}

.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-history {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 13px;
}

.sidebar-bottom {
  padding: 12px;
  border-top: 1px solid var(--border-color);
}

.theme-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 8px;
  transition: all 0.2s;
  position: relative;
}

.theme-selector:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.theme-dropdown {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 6px;
  min-width: 140px;
  box-shadow: 0 10px 40px var(--shadow-color);
  z-index: 100;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 13px;
}

.theme-option:hover {
  background-color: var(--bg-hover);
}

.theme-option.active {
  background-color: var(--bg-hover);
  color: var(--accent-color);
}

.theme-option .el-icon:last-child {
  margin-left: auto;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.user-profile:hover {
  background-color: var(--bg-hover);
}

.info .name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.info .email {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--bg-primary);
  transition: all 0.3s ease;
}

.top-bar {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color);
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--bg-secondary);
  padding: 8px 14px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  position: relative;
  transition: all 0.2s;
}

.model-selector:hover {
  background-color: var(--bg-hover);
  border-color: var(--accent-color);
}

.model-icon {
  color: var(--accent-color);
}

.model-selector .rotate {
  transform: rotate(180deg);
  transition: transform 0.2s;
}

.model-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 8px;
  min-width: 280px;
  box-shadow: 0 10px 40px var(--shadow-color);
  z-index: 100;
}

.model-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.model-option:hover {
  background-color: var(--bg-hover);
}

.model-option.active {
  background-color: var(--bg-hover);
  color: var(--accent-color);
}

.option-info {
  flex: 1;
}

.option-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 2px;
}

.option-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.header-actions .el-button {
  color: var(--text-secondary);
}

.header-actions .el-button:hover {
  color: var(--text-primary);
}

/* 聊天滚动区 */
.chat-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.welcome-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.welcome-logo {
  margin-bottom: 24px;
}

.logo-icon {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 8px 30px var(--shadow-color);
}

.welcome-title {
  font-size: 26px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.welcome-subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

/* 消息列表 */
.message-list {
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
  padding-bottom: 40px;
}

.message-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar .el-avatar {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.message-avatar .el-avatar.ai {
  background: var(--theme-gradient, linear-gradient(135deg, #6366f1, #a855f7));
}

.message-body {
  flex: 1;
  min-width: 0;
}

.message-name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.message-content {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.user-text {
  background-color: var(--message-user-bg);
  padding: 12px 16px;
  border-radius: 18px;
  display: inline-block;
  color: #ffffff;
}

.content-block {
  margin-top: 12px;
  background-color: var(--bg-secondary);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border-color);
}

.block-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
  font-size: 14px;
}

/* 输入区 */
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

/* 下拉遮罩 */
.dropdown-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>