<template>
  <div class="ai-chat-container" :class="themeClass">
    <!-- 左侧侧边栏 -->
    <Sidebar 
      :collapsed="sidebarCollapsed"
      :sessions="sessionStore.sessions || []"
      :current-session-id="sessionStore.currentSessionId"
      :theme="theme"
      @toggle="sidebarCollapsed = !sidebarCollapsed"
      @new-chat="startNewChat"
      @load-session="loadSession"
      @delete-session="handleDeleteSession"
      @clear-all-sessions="handleClearAllSessions"
      @change-theme="(newTheme) => { theme = newTheme }"
    />

    <!-- 右侧主区域 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <TopBar 
        :model-list="modelList"
        :current-model="currentModel"
        @select-model="selectModel"
      />

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
            <div class="message-body">
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
                    <p v-if="msg.content" class="text-part">{{ msg.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="chatStore.isLoading" class="message-row ai">
            <div class="message-body">
              <div class="message-content loading">
                <el-skeleton animated :rows="3" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部输入区 -->
      <ChatInput 
        :loading="chatStore.isLoading"
        @send-message="handleSendMessage"
        @file-select="handleFileSelect"
        @quick-ask="quickAsk"
        ref="chatInputRef"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted, watch } from 'vue'
import { DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import DataTable from '../components/DataTable.vue'
import DataChart from '../components/DataChart.vue'
import Sidebar from '../components/Sidebar.vue'
import TopBar from '../components/TopBar.vue'
import ChatInput from '../components/ChatInput.vue'

import { useSessionStore } from '../store/index'
import { useChatStore } from '../store/chatStore'

// 导入 API 模块
import { sessionService, uploadService, chatService } from '../api/services'

const sessionStore = useSessionStore()
const chatStore = useChatStore()
const chatInputRef = ref(null)

// 将后端 DataFrame.to_dict() 结果转换为 records 数组
// - orient="columns": {col: {index: value}}
// - orient="records": [{...}, ...]
const dfDictToRecords = (result) => {
  if (!result) return { records: [], columns: [] }

  // 已经是 records
  if (Array.isArray(result)) {
    const columns = result.length ? Object.keys(result[0]) : []
    return { records: result, columns }
  }

  // pandas to_dict() 常见结构：{col: {0: v, 1: v}}
  if (typeof result === 'object') {
    const columns = Object.keys(result)
    if (columns.length === 0) return { records: [], columns: [] }

    const indexSet = new Set()
    for (const col of columns) {
      const colObj = result[col]
      if (colObj && typeof colObj === 'object') {
        Object.keys(colObj).forEach((k) => indexSet.add(k))
      }
    }

    const indices = Array.from(indexSet).sort((a, b) => Number(a) - Number(b))
    const records = indices.map((idx) => {
      const row = {}
      for (const col of columns) {
        row[col] = result[col]?.[idx]
      }
      return row
    })
    return { records, columns }
  }

  return { records: [], columns: [] }
}

const messages = ref([])
const chatWindowRef = ref(null)
const sidebarCollapsed = ref(false)

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
  { id: 'ali-qwen', name: '阿里云 Qwen Turbo', description: '阿里云开发的大语言模型，适合数据分析和对话' },
  { id: 'deepseek', name: 'DeepSeek R1', description: 'DeepSeek开发的大语言模型，擅长代码和数学推理' },
  { id: 'volcengine', name: '火山引擎 Doubao', description: '火山引擎开发的大语言模型，多语言支持' }
])

const currentModel = ref(modelList.value[0])

const selectModel = (model) => {
  currentModel.value = model
  showMessage(`已切换到 ${model.name}`, 'success')
}

const startNewChat = () => {
  messages.value = []
  sessionStore.currentSessionId = null
  if (chatInputRef.value) {
    chatInputRef.value.clearInput()
  }
}

const refreshSessionHistory = async () => {
  try {
    const response = await sessionService.getSessionHistory()
    if (response.status === 'ok' && response.sessions) {
      sessionStore.sessions = []
      response.sessions.forEach(session => {
        sessionStore.addSession({
          id: session.id,
          fileName: session.fileName,
          displayName: session.displayName,
          timestamp: session.timestamp
        })
      })
    }
  } catch (error) {
    console.error('获取历史会话失败:', error)
  }
}

const handleDeleteSession = async (session) => {
  if (!confirm('确定删除该会话吗？')) return
  try {
    const resp = await sessionService.deleteSession(session.id)
    if (resp.status === 'ok') {
      // 如果删的是当前会话，回到空白
      if (sessionStore.currentSessionId === session.id) {
        startNewChat()
      }
      await refreshSessionHistory()
      showMessage('会话已删除', 'success')
    } else {
      showMessage(resp.message || '删除失败', 'error')
    }
  } catch (e) {
    // 兼容：本地缓存/列表可能存在“已被清空/已被删除”的会话，后端会返回 404
    if (e?.response?.status === 404) {
      if (sessionStore.currentSessionId === session.id) {
        startNewChat()
      }
      await refreshSessionHistory()
      showMessage('该会话已不存在，已刷新列表', 'info')
      return
    }
    showMessage('删除失败', 'error')
  }
}

const handleClearAllSessions = async () => {
  if (!confirm('确定清空全部会话吗？此操作不可恢复。')) return
  try {
    const resp = await sessionService.clearAllSessions()
    if (resp.status === 'ok') {
      startNewChat()
      sessionStore.sessions = []
      sessionStore.saveSessions && sessionStore.saveSessions()
      // 以防其它端/旧数据影响，再从后端刷新一次
      await refreshSessionHistory()
      showMessage('已清空全部会话', 'success')
    } else {
      showMessage(resp.message || '清空失败', 'error')
    }
  } catch (e) {
    showMessage('清空失败', 'error')
  }
}

const loadSession = (session) => {
  sessionStore.setCurrentSession(session.id, session.fileName, [], [])
  messages.value = []

  // 从后端恢复该会话的完整消息
  sessionService.getSessionMessages(session.id).then((resp) => {
    if (resp.status === 'ok' && Array.isArray(resp.messages)) {
      const rebuilt = []
      resp.messages.forEach((m) => {
        if (m.role === 1) {
          rebuilt.push({ role: 'user', content: m.content })
          return
        }
        if (m.role === 2) {
          // 助手：先放文本，再根据 extra 放表格/图表
          rebuilt.push({ role: 'ai', type: 'text', content: m.content })
          const extra = m.extra
          if (extra?.result) {
            const { records, columns } = dfDictToRecords(extra.result)
            if (records.length && columns.length) {
              rebuilt.push({
                role: 'ai',
                type: 'table',
                title: '分析结果表格',
                data: records,
                columns
              })
            }
          }
          if (extra?.chart_option) {
            rebuilt.push({
              role: 'ai',
              type: 'chart',
              title: '分析结果图表',
              chartOption: extra.chart_option
            })
          }
          return
        }
        // 系统消息
        rebuilt.push({ role: 'ai', type: 'text', content: m.content })
      })
      messages.value = rebuilt
      scrollToBottom()
    } else {
      messages.value = [{ role: 'ai', type: 'text', content: '会话加载失败：未获取到消息' }]
      scrollToBottom()
    }
  }).catch(() => {
    messages.value = [{ role: 'ai', type: 'text', content: '会话加载失败：网络错误' }]
    scrollToBottom()
  })
}

const quickAsk = (text) => {
  if (chatInputRef.value) {
    chatInputRef.value.userInput = text
    handleSendMessage(text)
  }
}

// 修改后的文件选择与上传逻辑
const handleFileSelect = (type) => {
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
        const response = await uploadService.uploadFile(file)
        
        if (response.status === 'ok') {
          handleFileUploaded(response)
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
  // 注意：这里应该使用上传接口返回的 sessionId
  const sessionId = responseData.session_id;
  const fileName = responseData.filename;
  
  sessionStore.setCurrentSession(sessionId, fileName, responseData.data || [], responseData.columns || []);
  sessionStore.addSession({ id: sessionId, fileName, timestamp: new Date() });

  messages.value.push({
    role: 'ai',
    type: 'text',
    content: `文件《${fileName}》已上传。共 ${responseData.row_count} 条数据。`
  });
  scrollToBottom();
  showMessage('文件上传成功', 'success');
};

// 修改后的发送消息逻辑
const handleSendMessage = async (text) => {
  const trimmedText = text.trim()
  if (!trimmedText) return

  // 添加用户消息到列表
  messages.value.push({ role: 'user', content: trimmedText })
  if (chatInputRef.value) {
    chatInputRef.value.clearInput()
  }
  chatStore.setLoading(true)
  scrollToBottom()

  try {
    if (!sessionStore.currentSessionId && messages.value.length === 1) {
      // 第一次发送消息且没有上传文件，提示用户上传文件
      const aiMessage = {
        role: 'ai',
        type: 'text',
        content: '本系统旨在进行智能数据分析，请您先上传文件。'
      }
      messages.value.push(aiMessage)
    } else if (sessionStore.currentSessionId) {
      // 有会话ID，调用分析API
      const response = await sessionService.sendMessage(sessionStore.currentSessionId, trimmedText)
      
      if (response.status === 'ok') {
        // 1) 先展示文本总结（优先 summary，其次 error）
        messages.value.push({
          role: 'ai',
          type: 'text',
          content: response.analysis_summary || response.error || '分析完成'
        })

        // 2) 有结果就展示表格
        if (response.result) {
          const { records, columns } = dfDictToRecords(response.result)
          if (records.length && columns.length) {
            messages.value.push({
              role: 'ai',
              type: 'table',
              title: '分析结果表格',
              data: records,
              columns
            })
          }
        }

        // 3) 有图表配置就展示图表
        if (response.chart_option) {
          messages.value.push({
            role: 'ai',
            type: 'chart',
            title: '分析结果图表',
            chartOption: response.chart_option
          })
        }
    } else {
      messages.value.push({
        role: 'ai',
        type: 'text',
        content: `错误：${response.message || '处理失败'}`
      })
    }
    } else {
      // 没有会话ID但不是第一次发送消息，调用普通聊天API
      const response = await chatService.sendChatMessage(trimmedText)
      
      if (response.status === 'ok') {
        const aiMessage = {
          role: 'ai',
          type: 'text',
          content: response.response
        }
        messages.value.push(aiMessage)
      } else {
        messages.value.push({
          role: 'ai',
          type: 'text',
          content: `错误：${response.message || '处理失败'}`
        })
      }
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

onMounted(async () => {
  const savedTheme = localStorage.getItem('chat-theme')
  if (savedTheme) {
    theme.value = savedTheme
  }
  
  // 初始化会话存储，加载历史会话
  sessionStore.init()
  
  // 从后端获取历史会话
  await refreshSessionHistory()
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

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--bg-primary);
  transition: all 0.3s ease;
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

/* 去掉头像后收紧间距 */
.message-row {
  gap: 0;
}

/* 用户消息靠右（头像/内容反向） */
.message-row.user {
  flex-direction: row-reverse;
}

.message-row.user .message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  text-align: right;
}

.message-row.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

/* AI 消息靠左（默认） */
.message-row.ai .message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}

.message-row.ai .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-body {
  flex: 1;
  min-width: 0;
}

.message-content {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.message-content p {
  margin: 0;
}

.user-text {
  background-color: var(--message-user-bg);
  padding: 12px 16px;
  border-radius: 18px;
  display: inline-block;
  color: #ffffff;
  max-width: 620px;
  word-break: break-word;
}

/* AI 文本消息也使用气泡（避免看起来像纯段落） */
.ai-content > p {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  padding: 12px 16px;
  border-radius: 18px;
  color: var(--text-primary);
  display: inline-block;
  max-width: 620px;
  word-break: break-word;
}

.content-block {
  margin-top: 12px;
  background-color: var(--bg-secondary);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border-color);
  max-width: 720px;
  width: 100%;
}

.block-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
  font-size: 14px;
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