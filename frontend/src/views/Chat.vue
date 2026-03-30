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
    <main class="main-content" :class="{ 'with-preview': showPreview, 'with-database': showDatabaseSidebar }">
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
                <div v-if="msg.role === 'user'" class="user-content">
                  <div v-if="msg.type === 'text' || !msg.type" class="user-text">{{ msg.content }}</div>
                  
                  <div v-if="msg.type === 'file'" class="user-file-message" @click="handleFileClick(msg)">
                    <div class="file-icon" :class="msg.fileType">
                      <el-icon v-if="msg.fileType === 'data'" size="20"><Document /></el-icon>
                      <el-icon v-else-if="msg.fileType === 'sql'" size="20"><Document /></el-icon>
                      <el-icon v-else-if="msg.fileType === 'text'" size="20"><Document /></el-icon>
                      <el-icon v-else-if="msg.fileType === 'code'" size="20"><Document /></el-icon>
                      <el-icon v-else size="20"><Document /></el-icon>
                    </div>
                    <div class="file-info">
                      <div class="file-name">{{ msg.fileName }}</div>
                      <div class="file-description">{{ msg.content }}</div>
                    </div>
                    <el-icon class="file-arrow"><ArrowRight /></el-icon>
                  </div>
                </div>
                
                <div v-else class="ai-content">
                  <p v-if="msg.type === 'text' || !msg.type">{{ msg.content }}</p>
                  
                  <div v-if="msg.type === 'table'" class="content-block">
                    <div class="block-title">{{ msg.title || '数据表格' }}</div>
                    <DataTable :data="msg.data" :columns="msg.columns" />
                  </div>

                  <div v-if="msg.type === 'chart'" class="content-block">
                    <div class="block-title">{{ msg.title || '数据图表' }}</div>
                    <DataChart :option="msg.chartOption" :chart-lib-id="currentChartLib.id" />
                    <p v-if="msg.content" class="text-part">{{ msg.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="chatStore.isLoading" class="message-row ai">
            <div class="message-body">
              <div class="message-content thinking">
                <div class="thinking-wrapper">
                  <div class="thinking-dots">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </div>
                  <div class="thinking-text">{{ thinkingText || '正在思考中...' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>



      <!-- 底部输入区 -->
      <ChatInput 
        :loading="chatStore.isLoading"
        :chart-lib-list="chartLibList"
        :current-chart-lib="currentChartLib"
        @send-message="handleSendMessage"
        @file-select="handleFileSelect"
        @quick-ask="quickAsk"
        @preview-file="handlePreviewFile"
        @send-with-files="handleSendWithFiles"
        @database-connect="showDatabaseSidebar = true"
        @select-chart-lib="selectChartLib"
        ref="chatInputRef"
      />

      <!-- 数据库连接对话框 -->
      <DatabaseConnection 
        :visible="showDatabaseConnectionDialog"
        @connection-success="handleDatabaseConnection"
        @query-result="handleDatabaseQueryResult"
        @close="showDatabaseConnectionDialog = false"
      />
    </main>

    <!-- 文件预览侧边栏 -->
    <div v-if="showPreview" class="preview-sidebar" :class="themeClass">
      <div class="preview-header">
        <h3>{{ previewFile?.name }}</h3>
        <el-button 
          type="text" 
          size="small"
          @click="closePreview"
        >
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      <div class="preview-content">
        <div v-if="previewLoading" class="preview-loading">
          <el-skeleton animated :rows="10" />
        </div>
        <div v-else-if="previewError" class="preview-error">
          {{ previewError }}
        </div>
        <div v-else-if="previewData">
          <div v-if="previewData.file_type === 'data'" class="data-preview">
            <div class="preview-section">
              <h4>文件信息</h4>
              <p>行数：{{ previewData.structure.row_count }}</p>
              <p>列数：{{ previewData.structure.columns.length }}</p>
            </div>
            <div class="preview-section">
              <h4>列信息</h4>
              <ul class="column-list">
                <li v-for="(col, index) in previewData.structure.columns" :key="index">
                  {{ col.name }}
                </li>
              </ul>
            </div>
            <div class="preview-section">
              <h4>前5行数据</h4>
              <div class="preview-table">
                <div class="table-header">
                  <span v-for="(col, index) in previewData.structure.columns" :key="index">{{ col.name }}</span>
                </div>
                <div 
                  v-for="(row, rowIndex) in previewData.structure.preview_data" 
                  :key="rowIndex"
                  class="table-row"
                >
                  <span v-for="(col, colIndex) in previewData.structure.columns" :key="colIndex">
                    {{ row[col.name] }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-else-if="previewData.file_type === 'sql'" class="sql-preview">
            <div class="preview-section">
              <h4>SQL内容</h4>
              <pre class="sql-content">{{ previewData.structure.content }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据库侧边栏 -->
    <div v-if="showDatabaseSidebar" class="database-sidebar" :class="themeClass">
      <div class="database-header">
        <h3>数据库连接</h3>
        <el-button 
          type="text" 
          size="small"
          @click="closeDatabaseSidebar"
        >
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      <div class="database-content">
        <!-- 保存的连接列表 -->
        <div v-if="savedConnections.length > 0" class="saved-connections">
          <h4>快速连接</h4>
          <div class="connection-list">
            <div 
              v-for="(connection, index) in savedConnections" 
              :key="index"
              class="connection-card"
            >
              <div class="connection-header">
                <div class="connection-name">{{ connection.database }}</div>
                <div class="connection-detail">{{ connection.host }}:{{ connection.port }} · {{ connection.username }}</div>
              </div>
              <div class="connection-actions">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="quickConnect(connection)"
                  :disabled="activeDatabaseConnection && activeDatabaseConnection.database === connection.database && activeDatabaseConnection.host === connection.host"
                  class="connect-button"
                >
                  连接
                </el-button>
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="deleteSavedConnection(index)"
                  class="delete-button"
                >
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="activeDatabaseConnection" class="connection-status">
          <div class="connection-info">
            <el-icon><Check /></el-icon>
            <span>已连接到: {{ activeDatabaseConnection.database }}@{{ activeDatabaseConnection.host }}:{{ activeDatabaseConnection.port }}</span>
            <el-button type="text" size="small" @click="disconnectDatabase">断开</el-button>
          </div>

          <!-- 表结构浏览 -->
          <div v-if="databaseTables.length > 0" class="tables-list">
            <h4>数据库表结构</h4>
            <div class="table-list">
              <el-collapse class="table-collapse">
                <el-collapse-item
                  v-for="table in databaseTables"
                  :key="table.name"
                  :title="table.name"
                  class="table-collapse-item"
                >
                  <div class="table-content">
                    <el-table :data="table.columns" style="width: 100%" class="column-table">
                      <el-table-column prop="name" label="列名" width="120">
                        <template #header>
                          <span class="column-header">列名</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="type" label="类型" width="150">
                        <template #header>
                          <span class="column-header">类型</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="nullable" label="可空" width="80">
                        <template #header>
                          <span class="column-header">可空</span>
                        </template>
                        <template #default="scope">
                          <el-tag size="small" :type="scope.row.nullable ? 'warning' : 'success'" class="nullable-tag">
                            {{ scope.row.nullable ? '是' : '否' }}
                          </el-tag>
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </div>
        <div v-else class="no-connection">
          <p>未连接数据库</p>
          <el-button type="primary" @click="showDatabaseConnectionDialog = true">连接数据库</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted, onUnmounted, watch } from 'vue'
import { DataAnalysis, Close, Document, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import DataTable from '../components/DataTable.vue'
import DataChart from '../components/DataChart.vue'
import Sidebar from '../components/Sidebar.vue'
import TopBar from '../components/TopBar.vue'
import ChatInput from '../components/ChatInput.vue'
import DatabaseConnection from '../components/DatabaseConnection.vue'

import { useSessionStore } from '../store/index'
import { useChatStore } from '../store/chatStore'

// 导入 API 模块
import { sessionService, uploadService, chatService, databaseService } from '../api/services'

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

// 为数据库查询结果生成图表配置
const generateChartFromQueryResult = (data, columns, query) => {
  if (!data || data.length === 0 || !columns || columns.length === 0) {
    return null
  }

  // 分析数据类型
  const numericColumns = []
  const categoryColumns = []
  
  // 简单判断列类型
  for (const col of columns) {
    const values = data.map(row => row[col])
    const isNumeric = values.every(val => !isNaN(val) && val !== null && val !== undefined)
    if (isNumeric) {
      numericColumns.push(col)
    } else {
      categoryColumns.push(col)
    }
  }

  // 确定图表类型
  let chartType = 'table' // 默认使用表格
  if (query.includes('折线图')) {
    chartType = 'line'
  } else if (query.includes('柱状图') || query.includes('条形图')) {
    chartType = 'bar'
  } else if (query.includes('饼图')) {
    chartType = 'pie'
  } else if (query.includes('散点图')) {
    chartType = 'scatter'
  }

  // 如果用户没有指定图表类型，默认使用表格
  if (chartType === 'table') {
    return null // 表格由其他逻辑处理
  }

  // 生成图表配置
  if (chartType === 'line') {
    // 折线图
    if (numericColumns.length === 0) return null
    
    const xAxisData = data.map(row => {
      // 优先使用姓名或类别列作为x轴
      const nameCol = categoryColumns.find(col => col.includes('姓名') || col.includes('name') || col.includes('Name'))
      return nameCol ? row[nameCol] : data.indexOf(row)
    })
    
    return {
      title: { text: query.substring(0, 30) },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: xAxisData, name: '姓名' },
      yAxis: { type: 'value', name: numericColumns[0] },
      series: numericColumns.map(col => {
        const seriesData = data.map(row => row[col])
        return {
          name: col,
          type: 'line',
          data: seriesData,
          smooth: true,
          label: {
            show: true,
            position: 'top',
            formatter: (params) => {
              // 尝试显示姓名
              const nameCol = categoryColumns.find(col => col.includes('姓名') || col.includes('name') || col.includes('Name'))
              return nameCol ? data[params.dataIndex][nameCol] : ''
            }
          }
        }
      }),
      grid: { containLabel: true, left: '10%', right: '10%', top: '15%', bottom: '15%' }
    }
  } else if (chartType === 'bar') {
    // 柱状图
    if (numericColumns.length === 0) return null
    
    const xAxisData = data.map(row => {
      const nameCol = categoryColumns.find(col => col.includes('姓名') || col.includes('name') || col.includes('Name'))
      return nameCol ? row[nameCol] : data.indexOf(row)
    })
    
    return {
      title: { text: query.substring(0, 30) },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: xAxisData, name: '姓名' },
      yAxis: { type: 'value', name: numericColumns[0] },
      series: numericColumns.map(col => {
        const seriesData = data.map(row => row[col])
        return {
          name: col,
          type: 'bar',
          data: seriesData,
          label: {
            show: true,
            position: 'top',
            formatter: '{c}'
          }
        }
      }),
      grid: { containLabel: true, left: '10%', right: '10%', top: '15%', bottom: '15%' }
    }
  } else if (chartType === 'pie') {
    // 饼图
    if (numericColumns.length === 0 || categoryColumns.length === 0) return null
    
    const categoryCol = categoryColumns[0]
    const valueCol = numericColumns[0]
    
    const seriesData = data.map(row => ({
      name: row[categoryCol],
      value: row[valueCol]
    }))
    
    return {
      title: { text: query.substring(0, 30) },
      tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', left: 'left', data: data.map(row => row[categoryCol]) },
      series: [{
        name: valueCol,
        type: 'pie',
        radius: '50%',
        data: seriesData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          show: true,
          formatter: '{b}: {c} ({d}%)'
        }
      }]
    }
  }

  return null
}

const messages = ref([])
const chatWindowRef = ref(null)
const sidebarCollapsed = ref(false)

// 思考状态相关
const thinkingText = ref('')
const thinkingTimer = ref(null)
const thinkingMessages = [
  '正在思考中...',
  '让我分析一下...',
  '正在处理数据...',
  '正在生成分析报告...',
  '请稍等片刻...',
  '马上就好...'
]

// 开始思考状态
const startThinking = () => {
  let index = 0
  thinkingText.value = thinkingMessages[0]
  thinkingTimer.value = setInterval(() => {
    index = (index + 1) % thinkingMessages.length
    thinkingText.value = thinkingMessages[index]
  }, 2000)
}

// 停止思考状态
const stopThinking = () => {
  if (thinkingTimer.value) {
    clearInterval(thinkingTimer.value)
    thinkingTimer.value = null
  }
  thinkingText.value = ''
}

// 文件预览相关状态
const showPreview = ref(false)
const previewFile = ref(null)
const previewData = ref(null)
const previewLoading = ref(false)
const previewError = ref('')

// 数据库连接对话框状态
const showDatabaseConnectionDialog = ref(false)
const activeDatabaseConnection = ref(null)
const databaseConnectionId = ref(null)
const showDatabaseSidebar = ref(false)
const databaseTables = ref([])

// 保存的数据库连接
const savedConnections = ref([])

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
  { id: 'volcengine', name: '火山引擎 Doubao', description: '火山引擎开发的大语言模型，多语言支持' },
  { id: 'spark', name: '星火大模型', description: '讯飞开发的大语言模型，多模态能力强' }
])

const currentModel = ref(modelList.value[0])

const selectModel = (model) => {
  currentModel.value = model
  showMessage(`已切换到 ${model.name}`, 'success')
}

const chartLibList = ref([
  { id: 'echarts', name: 'ECharts', description: 'Apache ECharts，功能强大的开源图表库' },
  { id: 'antv-g2', name: 'AntV G2', description: '蚂蚁集团出品，数据驱动的高交互性图表库' }
])

const currentChartLib = ref(chartLibList.value[0])

const selectChartLib = (lib) => {
  currentChartLib.value = lib
  showMessage(`已切换到 ${lib.name}`, 'success')
}

const startNewChat = () => {
  messages.value = []
  sessionStore.currentSessionId = null
  if (chatInputRef.value) {
    chatInputRef.value.clearInput()
  }
  closePreview()
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
  closePreview()

  // 从后端恢复该会话的完整消息
  sessionService.getSessionMessages(session.id).then((resp) => {
    if (resp.status === 'ok' && Array.isArray(resp.messages)) {
      const rebuilt = []
      let loadedSqlContent = null
      
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
        const systemMsg = { role: 'ai', type: 'text', content: m.content, extra: m.extra }
        rebuilt.push(systemMsg)
        
        // 保存SQL内容
        if (m.extra && m.extra.sql_content) {
          loadedSqlContent = m.extra.sql_content
        }
      })
      
      // 更新sessionStore中的SQL内容
      if (loadedSqlContent) {
        sessionStore.sqlContent = loadedSqlContent
      }
      
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

// 处理文件选择
const handleFileSelect = async (type, file) => {
  try {
    // 后台预览文件，不显示给用户，只是为了获取文件结构
    await uploadService.previewFile(file)
  } catch (error) {
    console.error('文件预览失败:', error)
  }
}

// 处理文件预览
const handlePreviewFile = async (file) => {
  previewFile.value = file
  showPreview.value = true
  previewLoading.value = true
  previewError.value = ''
  
  try {
    const previewResponse = await uploadService.previewFile(file)
    
    if (previewResponse.status === 'ok') {
      previewData.value = previewResponse
    } else {
      previewError.value = `预览失败：${previewResponse.message}`
    }
  } catch (error) {
    previewError.value = `预览失败：${error.message}`
  } finally {
    previewLoading.value = false
  }
}

// 关闭预览
const closePreview = () => {
  showPreview.value = false
  previewFile.value = null
  previewData.value = null
  previewLoading.value = false
  previewError.value = ''
}

// 处理发送带文件的消息
const handleSendWithFiles = async (text, files) => {
  const trimmedText = text.trim()
  
  // 先添加文件消息到用户消息处
  for (const file of files) {
    messages.value.push({
      role: 'user',
      type: 'file',
      content: `上传了文件`,
      fileName: file.name,
      fileType: getFileType(file.name)
    })
  }
  
  // 如果有文本消息，也添加到用户消息处
  if (trimmedText) {
    messages.value.push({ role: 'user', content: trimmedText })
  }
  
  chatStore.setLoading(true)
  startThinking()
  scrollToBottom()

  try {
    // 逐个上传文件，确保所有文件上传完成
    let allFilesUploaded = true
    for (const file of files) {
      showMessage(`正在上传文件：${file.name}`, 'info')
      try {
        const uploadResponse = await uploadService.uploadFile(file)
        
        if (uploadResponse.status === 'ok') {
          // 显示上传成功提示（与"正在上传"相同位置）
          showMessage(`✅ 文件上传成功：${file.name}`, 'success');
          
          // 检查是否为SQL文件
          const isSqlFile = file.name.toLowerCase().endsWith('.sql')
          
          // 上传成功后，更新文件消息
          const fileMessageIndex = messages.value.findIndex(msg => 
            msg.role === 'user' && msg.type === 'file' && msg.fileName === file.name
          )
          if (fileMessageIndex !== -1) {
            messages.value[fileMessageIndex].content = isSqlFile 
              ? `文件《${file.name}》已上传。` 
              : `文件《${file.name}》已上传。共 ${uploadResponse.row_count} 条数据。`
            messages.value[fileMessageIndex].sessionId = uploadResponse.session_id
            
            // 如果是SQL文件，保存SQL内容到extra中
            if (isSqlFile && uploadResponse.tables) {
              // 使用后端返回的SQL内容
              messages.value.push({
                role: 'ai',
                type: 'text',
                content: `已上传SQL文件：${file.name}（${uploadResponse.tables.length}个表）`,
                extra: {
                  sql_content: uploadResponse.sql_content || '-- SQL文件内容'
                }
              })
            }
          }
          
          // 更新会话状态
          const sessionId = uploadResponse.session_id
          const fileName = uploadResponse.filename
          sessionStore.setCurrentSession(
            sessionId, 
            fileName, 
            uploadResponse.data || [], 
            uploadResponse.columns || [],
            uploadResponse.sql_content || null  // 传入SQL内容
          )
          sessionStore.addSession({ id: sessionId, fileName, timestamp: new Date() })
        } else {
          showMessage(`上传失败：${uploadResponse.message}`, 'error')
          allFilesUploaded = false
        }
      } catch (uploadError) {
        showMessage(`上传失败：${uploadError.message}`, 'error')
        allFilesUploaded = false
      }
      // 等待一小段时间，确保会话状态更新
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    // 如果有文本消息且所有文件上传完成，再发送消息
    if (trimmedText && allFilesUploaded) {
      // 确保会话ID已经设置
      if (sessionStore.currentSessionId) {
        // 有会话ID，调用分析API
        try {
          const response = await sessionService.sendMessage(sessionStore.currentSessionId, trimmedText, currentModel.value.id)
          
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
        } catch (messageError) {
          messages.value.push({
            role: 'ai',
            type: 'text',
            content: `错误：${messageError.message}`
          })
        }
      } else {
        // 没有会话ID，调用普通聊天API
        try {
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
        } catch (messageError) {
          messages.value.push({
            role: 'ai',
            type: 'text',
            content: `错误：${messageError.message}`
          })
        }
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
    stopThinking()
    nextTick(() => scrollToBottom())
  }
}

// 处理上传成功后的逻辑
const handleFileUploaded = async (responseData) => {
  // 注意：这里应该使用上传接口返回的 sessionId
  const sessionId = responseData.session_id;
  const fileName = responseData.filename;
  
  // 生成会话名称
  let sessionDisplayName = fileName;
  const lowerFileName = fileName.toLowerCase();
  if (lowerFileName.endsWith('.csv')) {
    sessionDisplayName = `${fileName}文件分析`;
  } else if (lowerFileName.endsWith('.sql')) {
    sessionDisplayName = `${fileName}文件分析`;
  } else if (lowerFileName.endsWith('.xlsx') || lowerFileName.endsWith('.xls')) {
    sessionDisplayName = `${fileName}文件分析`;
  }
  
  sessionStore.setCurrentSession(sessionId, fileName, responseData.data || [], responseData.columns || []);
  sessionStore.addSession({ id: sessionId, fileName, displayName: sessionDisplayName, timestamp: new Date() });

  // 检查是否为SQL文件
  const isSqlFile = lowerFileName.endsWith('.sql');
  
  // 添加文件消息到聊天页面
  messages.value.push({
    role: 'ai',
    type: 'file',
    content: isSqlFile ? `文件《${fileName}》已上传。` : `文件《${fileName}》已上传。共 ${responseData.row_count} 条数据。`,
    fileName: fileName,
    fileType: getFileType(fileName),
    sessionId: sessionId
  });
  scrollToBottom();
  showMessage('文件上传成功', 'success');
};

// 获取文件类型
const getFileType = (fileName) => {
  const extension = fileName.toLowerCase().split('.').pop();
  if (['csv', 'xlsx', 'xls'].includes(extension)) {
    return 'data';
  } else if (['sql'].includes(extension)) {
    return 'sql';
  } else if (['txt', 'md', 'markdown'].includes(extension)) {
    return 'text';
  } else if (['py', 'js', 'ts', 'html', 'css', 'json'].includes(extension)) {
    return 'code';
  } else {
    return 'file';
  }
};

// 处理文件点击事件
const handleFileClick = async (fileMessage) => {
  showPreview.value = true
  previewFile.value = { name: fileMessage.fileName }
  previewLoading.value = true
  previewError.value = ''
  
  try {
    // 检查是否为SQL文件
    const isSqlFile = fileMessage.fileName.toLowerCase().endsWith('.sql');
    
    if (isSqlFile) {
      // 优先从sessionStore获取SQL内容
      let sqlContent = sessionStore.sqlContent || "-- SQL文件内容需要重新上传才能预览";
      
      // 如果sessionStore中没有，再从messages中查找
      if (sqlContent === "-- SQL文件内容需要重新上传才能预览") {
        for (const msg of messages.value) {
          if (msg.extra && msg.extra.sql_content) {
            sqlContent = msg.extra.sql_content;
            break;
          }
        }
      }
      
      previewData.value = {
        status: "ok",
        file_type: "sql",
        filename: fileMessage.fileName,
        structure: {
          content: sqlContent
        }
      };
    } else {
      // 对于数据文件，使用会话中的数据
      if (sessionStore.previewData && sessionStore.previewData.length > 0) {
        // 使用会话中的预览数据 - 确保列格式与上传前预览一致
        // 检查columns的格式，确保只包含name字段
        let columns = sessionStore.columns;
        if (columns.length > 0 && columns[0].name !== undefined) {
          // 如果已经是对象格式，提取name字段
          columns = columns.map(col => ({ name: col.name }));
        } else if (columns.length > 0 && typeof columns[0] === 'string') {
          // 如果是字符串格式，转换为对象格式
          columns = columns.map(col => ({ name: col }));
        }
        
        previewData.value = {
          status: "ok",
          file_type: "data",
          filename: fileMessage.fileName,
          structure: {
            columns: columns,
            row_count: sessionStore.previewData.length,
            preview_data: sessionStore.previewData.slice(0, 5)
          }
        };
      } else {
        // 如果没有预览数据，显示错误
        throw new Error("没有可用的文件预览数据");
      }
    }
  } catch (error) {
    previewError.value = `预览失败：${error.message}`;
  } finally {
    previewLoading.value = false;
  }
};

// 获取文件MIME类型
const getFileMimeType = (fileName) => {
  const extension = fileName.toLowerCase().split('.').pop();
  const mimeTypes = {
    csv: 'text/csv',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    xls: 'application/vnd.ms-excel',
    sql: 'text/plain',
    txt: 'text/plain',
    md: 'text/markdown',
    markdown: 'text/markdown',
    py: 'text/x-python',
    js: 'text/javascript',
    ts: 'text/typescript',
    html: 'text/html',
    css: 'text/css',
    json: 'application/json'
  };
  return mimeTypes[extension] || 'application/octet-stream';
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
  startThinking()
  scrollToBottom()

  try {
    if (activeDatabaseConnection.value) {
      // 已连接数据库，使用Chat to SQL功能
      
      // 检查用户是否请求图表
      const wantsChart = trimmedText.includes('图表') || trimmedText.includes('折线图') || trimmedText.includes('柱状图') || trimmedText.includes('饼图') || trimmedText.includes('可视化');
      
      // 优化Chat to SQL提示，明确告诉模型用户可能需要图表
      const chatToSqlResponse = await databaseService.chatToSql(databaseConnectionId.value, trimmedText);
      
      if (chatToSqlResponse.status === 'ok') {
        const sql = chatToSqlResponse.sql;
        
        // 显示生成的SQL语句
        messages.value.push({
          role: 'ai',
          type: 'text',
          content: `生成的SQL语句：\n${sql}`
        });
        
        // 执行SQL查询
        const queryResponse = await databaseService.executeQuery(databaseConnectionId.value, sql);
        
        if (queryResponse.status === 'ok') {
          messages.value.push({
            role: 'ai',
            type: 'text',
            content: `查询执行成功，返回 ${queryResponse.row_count} 行数据`
          });
          
          if (queryResponse.data && queryResponse.data.length > 0) {
            messages.value.push({
              role: 'ai',
              type: 'table',
              title: '查询结果',
              data: queryResponse.data,
              columns: queryResponse.columns
            });
            
            // 如果用户请求了图表，尝试生成
            if (wantsChart) {
              try {
                // 构建图表配置
                const chartOption = generateChartFromQueryResult(queryResponse.data, queryResponse.columns, trimmedText);
                if (chartOption) {
                  messages.value.push({
                    role: 'ai',
                    type: 'chart',
                    title: '分析结果图表',
                    chartOption: chartOption
                  });
                } else {
                  messages.value.push({
                    role: 'ai',
                    type: 'text',
                    content: '无法为当前查询结果生成图表，请确保查询包含数值类型的列。'
                  });
                }
              } catch (error) {
                console.error('生成图表失败:', error);
                messages.value.push({
                  role: 'ai',
                  type: 'text',
                  content: '生成图表时出错，请稍后再试。'
                });
              }
            }
          } else {
            messages.value.push({
              role: 'ai',
              type: 'text',
              content: '查询返回了空结果。'
            });
          }
        } else {
          messages.value.push({
            role: 'ai',
            type: 'text',
            content: `SQL执行失败：${queryResponse.message}`
          });
        }
      } else {
        messages.value.push({
          role: 'ai',
          type: 'text',
          content: `生成SQL失败：${chatToSqlResponse.message}`
        });
      }
    } else if (!sessionStore.currentSessionId && messages.value.length === 1) {
      // 第一次发送消息且没有上传文件，提示用户上传文件
      const aiMessage = {
        role: 'ai',
        type: 'text',
        content: '本系统旨在进行智能数据分析，请您先上传文件或连接数据库。'
      }
      messages.value.push(aiMessage)
    } else if (sessionStore.currentSessionId) {
      // 有会话ID，调用分析API
      const response = await sessionService.sendMessage(sessionStore.currentSessionId, trimmedText, currentModel.value.id)
      
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
      const response = await chatService.sendChatMessage(trimmedText, currentModel.value.id)
      
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
    stopThinking()
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

// 处理数据库连接成功
const handleDatabaseConnection = async (connectionInfo) => {
  activeDatabaseConnection.value = connectionInfo.connectionInfo
  databaseConnectionId.value = connectionInfo.connectionId
  
  // 保存连接信息
  saveConnection(connectionInfo.connectionInfo)
  
  // 生成数据库会话名称
  const databaseName = connectionInfo.connectionInfo.database;
  const sessionDisplayName = `${databaseName}数据库数据分析`;
  
  // 创建数据库会话
  const sessionId = `db_${Date.now()}`;
  sessionStore.setCurrentSession(sessionId, databaseName, [], []);
  sessionStore.addSession({ id: sessionId, fileName: databaseName, displayName: sessionDisplayName, timestamp: new Date() });
  
  // 加载数据库表结构
  try {
    const tablesResponse = await databaseService.getTables(connectionInfo.connectionId)
    if (tablesResponse.status === 'ok') {
      databaseTables.value = tablesResponse.tables
    }
  } catch (error) {
    console.error('获取表结构失败:', error)
  }
  
  // 显示数据库侧边栏
  showDatabaseSidebar.value = true
  
  messages.value.push({
    role: 'ai',
    type: 'text',
    content: `成功连接到数据库：${connectionInfo.connectionInfo.database}@${connectionInfo.connectionInfo.host}:${connectionInfo.connectionInfo.port}`
  })
  scrollToBottom()
}

// 关闭数据库侧边栏
const closeDatabaseSidebar = () => {
  showDatabaseSidebar.value = false
}

// 断开数据库连接
const disconnectDatabase = async () => {
  if (!databaseConnectionId.value) return
  
  try {
    const response = await databaseService.disconnectDatabase(databaseConnectionId.value)
    if (response.status === 'ok') {
      activeDatabaseConnection.value = null
      databaseConnectionId.value = null
      databaseTables.value = []
      showDatabaseSidebar.value = false
      messages.value.push({
        role: 'ai',
        type: 'text',
        content: '数据库连接已断开'
      })
      ElMessage.success('连接已断开')
      scrollToBottom()
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('断开连接失败：' + error.message)
  }
}

// 处理数据库查询结果
const handleDatabaseQueryResult = (result) => {
  messages.value.push({
    role: 'ai',
    type: 'text',
    content: `查询执行成功，返回 ${result.row_count} 行数据`
  })
  
  if (result.data && result.data.length > 0) {
    messages.value.push({
      role: 'ai',
      type: 'table',
      title: '查询结果',
      data: result.data,
      columns: result.columns
    })
  }
  scrollToBottom()
}

onMounted(async () => {
  const savedTheme = localStorage.getItem('chat-theme')
  if (savedTheme) {
    theme.value = savedTheme
  }
  
  // 加载保存的数据库连接
  loadSavedConnections()
  
  // 初始化会话存储，加载历史会话
  sessionStore.init()
  
  // 从后端获取历史会话
  await refreshSessionHistory()
})

// 加载保存的数据库连接
const loadSavedConnections = () => {
  try {
    const saved = localStorage.getItem('savedDatabaseConnections')
    if (saved) {
      const connections = JSON.parse(saved)
      // 确保port字段是数字类型
      savedConnections.value = connections.map(conn => ({
        ...conn,
        port: Number(conn.port)
      }))
    }
  } catch (error) {
    console.error('加载保存的数据库连接失败:', error)
  }
}

// 保存数据库连接
const saveConnection = (connectionInfo) => {
  try {
    // 检查是否已存在相同的连接
    const existingIndex = savedConnections.value.findIndex(conn => 
      conn.host === connectionInfo.host && 
      conn.port === connectionInfo.port && 
      conn.database === connectionInfo.database
    )
    
    if (existingIndex === -1) {
      // 添加新连接
      savedConnections.value.push({
        ...connectionInfo,
        savedAt: new Date().toISOString()
      })
      
      // 保存到localStorage
      localStorage.setItem('savedDatabaseConnections', JSON.stringify(savedConnections.value))
      showMessage('数据库连接已保存', 'success')
    }
  } catch (error) {
    console.error('保存数据库连接失败:', error)
  }
}

// 删除保存的数据库连接
const deleteSavedConnection = (index) => {
  try {
    savedConnections.value.splice(index, 1)
    localStorage.setItem('savedDatabaseConnections', JSON.stringify(savedConnections.value))
    showMessage('数据库连接已删除', 'success')
  } catch (error) {
    console.error('删除数据库连接失败:', error)
  }
}

// 快速连接数据库
const quickConnect = (connection) => {
  showMessage(`正在连接数据库：${connection.database}@${connection.host}:${connection.port}`, 'info')
  
  // 直接使用保存的连接信息连接数据库
  const connectionData = {
    host: connection.host,
    port: connection.port,
    username: connection.username,
    password: connection.password,
    database: connection.database
  };
  
  databaseService.connectDatabase(connectionData).then(response => {
    if (response.status === 'ok') {
      handleDatabaseConnection({
        connectionId: response.connection_id,
        connectionInfo: connectionData
      })
      showMessage('数据库连接成功', 'success')
    } else {
      showMessage(`连接失败：${response.message}`, 'error')
    }
  }).catch(error => {
    console.error('连接失败:', error);
    showMessage(`连接失败：${error.message}`, 'error')
  })
}

watch(theme, (newVal) => {
  localStorage.setItem('chat-theme', newVal)
})

onUnmounted(() => {
  stopThinking()
})
</script>

<style scoped>
.theme-dark {
  --bg-primary: #0a0a0a;
  --bg-secondary: #121212;
  --bg-hover: #1e1e1e;
  --bg-input: #121212;
  --text-primary: #ffffff;
  --text-secondary: #b0b0b0;
  --text-muted: #808080;
  --border-color: #2a2a2a;
  --accent-color: #6366f1;
  --accent-hover: #4f46e5;
  --message-user-bg: #1e1e1e;
  --shadow-color: rgba(0, 0, 0, 0.5);
  --card-bg: #1a1a1a;
  --card-border: #2a2a2a;
  --gradient-primary: linear-gradient(135deg, #6366f1, #8b5cf6);
  --gradient-secondary: linear-gradient(135deg, #4f46e5, #7c3aed);
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

/* 数据库连接状态 */
.database-connection-status {
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: 12px 24px;
}

.database-connection-status .connection-info {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-primary);
  font-size: 14px;
}

.database-connection-status .el-icon {
  color: #10b981;
}

.database-connection-status .el-button {
  margin-left: auto;
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
  margin-bottom: 12px;
}

/* 用户文件消息样式 */
.user-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.user-file-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: rgba(79, 70, 229, 0.1);
  border: 1px solid rgba(79, 70, 229, 0.3);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  max-width: 620px;
  width: 100%;
  margin-bottom: 12px;
}

.user-file-message:hover {
  background-color: rgba(79, 70, 229, 0.15);
  border-color: var(--accent-color);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.2);
  transform: translateY(-1px);
}

.user-file-message .file-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.user-file-message .file-info {
  flex: 1;
  min-width: 0;
}

.user-file-message .file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-file-message .file-description {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.user-file-message .file-arrow {
  color: var(--text-muted);
  transition: color 0.3s ease;
}

.user-file-message:hover .file-arrow {
  color: var(--accent-color);
  transform: translateX(4px);
  transition: all 0.3s ease;
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

/* 文件消息样式 */
.file-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: var(--bg-hover);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
}

.file-message:hover {
  background-color: var(--bg-secondary);
  box-shadow: 0 2px 8px var(--shadow-color);
  transform: translateY(-1px);
}

.file-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.file-icon.data {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.file-icon.sql {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.file-icon.text {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.file-icon.code {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
}

.file-icon.file {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  color: white;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-description {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.file-arrow {
  color: var(--text-muted);
  transition: color 0.3s ease;
}

.file-message:hover .file-arrow {
  color: var(--accent-color);
  transform: translateX(4px);
  transition: all 0.3s ease;
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

/* 主内容区带预览时的样式 */
.main-content.with-preview {
  flex: 1;
  margin-right: 400px;
}

/* 文件预览侧边栏 */
.preview-sidebar {
  position: fixed;
  right: 0;
  top: 0;
  width: 400px;
  height: 100vh;
  background-color: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  box-shadow: -4px 0 12px var(--shadow-color);
  transition: all 0.3s ease;
}

/* 数据库侧边栏 */
.database-sidebar {
  position: fixed;
  right: 0;
  top: 0;
  width: 400px;
  height: 100vh;
  background-color: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  box-shadow: -4px 0 12px var(--shadow-color);
  transition: all 0.3s ease;
}

.preview-header,
.database-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-header h3,
.database-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.preview-content,
.database-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 数据库连接状态 */
.connection-status {
  margin-bottom: 20px;
}

.connection-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 14px;
  flex-wrap: wrap;
}

.connection-info .el-icon {
  color: #10b981;
}

.connection-info .el-button {
  margin-left: auto;
  flex-shrink: 0;
}

/* 保存的连接列表 */
.saved-connections {
  margin-bottom: 20px;
}

.saved-connections h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.saved-connections h4::before {
  content: '';
  width: 4px;
  height: 16px;
  background: var(--accent-color);
  border-radius: 2px;
}

.connection-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.connection-card {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px var(--shadow-color);
  border: 1px solid var(--card-border);
  transition: all 0.3s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.connection-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--gradient-primary);
  border-radius: 12px 0 0 12px;
}

.connection-card:hover {
  box-shadow: 0 8px 20px var(--shadow-color);
  transform: translateY(-2px);
  border-color: var(--accent-color);
  background: linear-gradient(135deg, var(--card-bg), #1e1e2e);
}

.connection-card:hover .connection-name {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.connection-header {
  flex: 1;
  min-width: 0;
}

.connection-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.connection-detail {
  font-size: 14px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.connection-actions {
  display: flex;
  gap: 8px;
}

/* 思考状态样式 */
.thinking-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 0;
}

.thinking-dots {
  display: flex;
  gap: 6px;
  justify-content: flex-start;
}

.thinking-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--accent-color);
  animation: dot-bounce 1.4s infinite ease-in-out;
}

.thinking-dots .dot:nth-child(1) {
  animation-delay: 0s;
}

.thinking-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dot-bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.thinking-text {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
  animation: text-fade 0.3s ease-in-out;
}

@keyframes text-fade {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.connect-button {
  border-radius: 6px;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  border: none !important;
  color: white !important;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.connect-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s ease;
}

.connect-button:hover::before {
  left: 100%;
}

.connect-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}

.delete-button {
  border-radius: 6px;
  transition: all 0.3s ease;
  background: #ef4444 !important;
  border: none !important;
  color: white !important;
  position: relative;
  overflow: hidden;
}

.delete-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s ease;
}

.delete-button:hover::before {
  left: 100%;
}

.delete-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.connect-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  background: var(--border-color) !important;
  color: var(--text-muted) !important;
}

/* 数据库表结构 */
.tables-list {
  margin-bottom: 20px;
}

.tables-list h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.tables-list h4::before {
  content: '';
  width: 4px;
  height: 16px;
  background: var(--accent-color);
  border-radius: 2px;
}

.table-list {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px var(--shadow-color);
  border: 1px solid var(--card-border);
  position: relative;
  overflow: hidden;
}

.table-list::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--gradient-primary);
  border-radius: 12px 12px 0 0;
}

.table-collapse {
  border: none;
}

.table-collapse-item {
  border: 1px solid var(--card-border) !important;
  border-radius: 8px !important;
  margin-bottom: 12px !important;
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative;
}

.table-collapse-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--gradient-secondary);
  border-radius: 8px 0 0 8px;
}

.table-collapse-item:hover {
  border-color: var(--accent-color) !important;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2) !important;
  transform: translateY(-1px);
}

.table-collapse-item .el-collapse-item__header {
  background: var(--bg-hover) !important;
  border: none !important;
  padding: 12px 16px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  color: var(--text-primary) !important;
  transition: all 0.3s ease;
  padding-left: 30px !important;
  position: relative;
  z-index: 1;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  text-align: center !important;
  width: 100% !important;
  height: 44px !important;
  box-sizing: border-box !important;
}

/* 确保表名称不被左侧装饰条遮挡 */
.table-collapse-item .el-collapse-item__header .el-collapse-item__arrow {
  margin-left: auto !important;
  z-index: 2 !important;
}

/* 确保数据库侧边栏在深色模式下背景是黑色 */
.theme-dark .database-sidebar {
  background-color: #0a0a0a !important;
}

.theme-dark .database-content {
  background-color: #0a0a0a !important;
}

.theme-dark .table-list {
  background: #121212 !important;
  border-color: #2a2a2a !important;
}

.theme-dark .table-collapse-item {
  border-color: #2a2a2a !important;
}

.theme-dark .table-collapse-item .el-collapse-item__header {
  background: #1e1e1e !important;
}

.theme-dark .table-content {
  background: #121212 !important;
}

.theme-dark .column-table {
  background: #121212 !important;
}

.theme-dark .column-table th {
  background: #1e1e1e !important;
}

.theme-dark .column-table tr {
  background: #121212 !important;
}

.theme-dark .column-table tr:hover {
  background: #1e1e1e !important;
}

.table-collapse-item .el-collapse-item__header .el-collapse-item__content {
  background: var(--card-bg) !important;
}

/* 确保表格内容区域背景也是黑色 */
.table-content {
  background: var(--card-bg) !important;
}

.column-table {
  background: var(--card-bg) !important;
}

.column-table th {
  background: var(--bg-hover) !important;
}

.column-table tr {
  background: var(--card-bg) !important;
}

.column-table tr:hover {
  background: var(--bg-hover) !important;
}

.table-collapse-item .el-collapse-item__header:hover {
  background: var(--card-bg) !important;
  color: var(--accent-color) !important;
}

.table-collapse-item .el-collapse-item__content {
  padding: 0 !important;
  border-top: 1px solid var(--border-color) !important;
}

.table-content {
  padding: 16px;
}

.column-table {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.column-table th {
  background: var(--bg-hover) !important;
  border-bottom: 1px solid var(--border-color) !important;
  color: var(--text-primary) !important;
  font-weight: 500 !important;
}

.column-table td {
  border-bottom: 1px solid var(--border-color) !important;
  color: var(--text-secondary) !important;
}

.column-table tr:hover {
  background: var(--bg-hover) !important;
}

.column-header {
  font-weight: 500;
  color: var(--text-primary);
}

.nullable-tag {
  border-radius: 12px !important;
  font-size: 12px !important;
  padding: 2px 8px !important;
}

/* 确保表格在侧边栏中正确显示 */
.column-table {
  width: 100% !important;
}

.column-table th {
  white-space: nowrap;
}

.column-table td {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 无连接状态 */
.no-connection {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 16px;
  text-align: center;
  color: var(--text-secondary);
}

.no-connection p {
  margin: 0;
}

/* 主内容区带侧边栏时的样式 */
.main-content.with-preview,
.main-content.with-database {
  flex: 1;
  margin-right: 400px;
}

.preview-loading {
  padding: 20px 0;
}

.preview-error {
  color: #ef4444;
  padding: 20px 0;
}

.preview-section {
  margin-bottom: 24px;
}

.preview-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.preview-section h5 {
  margin: 8px 0 8px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.preview-section p {
  margin: 4px 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.column-list {
  list-style: none;
  padding: 0;
  margin: 8px 0;
}

.column-list li {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  padding-left: 16px;
  position: relative;
}

.column-list li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--accent-color);
}

/* 预览表格 */
.preview-table {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}

.table-header {
  display: flex;
  background-color: var(--bg-hover);
  border-bottom: 1px solid var(--border-color);
}

.table-header span {
  flex: 1;
  padding: 8px;
  font-weight: 600;
  color: var(--text-primary);
  border-right: 1px solid var(--border-color);
}

.table-header span:last-child {
  border-right: none;
}

.table-row {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}

.table-row:last-child {
  border-bottom: none;
}

.table-row span {
  flex: 1;
  padding: 8px;
  color: var(--text-secondary);
  border-right: 1px solid var(--border-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.table-row span:last-child {
  border-right: none;
}

/* SQL内容样式 */
.sql-content {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 500px;
  overflow-y: auto;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .main-content.with-preview {
    margin-right: 300px;
  }
  
  .preview-sidebar {
    width: 300px;
  }
}
</style>