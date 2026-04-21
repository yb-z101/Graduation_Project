<template>
  <div class="bi-workbench">
    <el-container class="workbench-container">
      <el-header height="64px" class="top-header">
        <div class="header-left">
          <div class="logo-wrapper">
            <div class="logo-icon">
              <svg viewBox="0 0 40 40" width="40" height="40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="40" height="40" rx="8" fill="white"/>
                <path d="M12 28V16L20 12L28 16V28" stroke="#8B7DF2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M16 24V20M24 24V20M20 24V18" stroke="#8B7DF2" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <h1 class="workbench-title">智析</h1>
          </div>
          <span class="session-info" v-if="currentFileName">
            <el-icon><Document /></el-icon>
            {{ currentFileName }}
          </span>
        </div>
        <div class="header-right">
          <el-select 
            v-model="currentModel" 
            placeholder="选择模型" 
            size="default" 
            class="model-select"
            popper-class="model-dropdown"
          >
            <template #prefix>
              <svg viewBox="0 0 16 16" width="16" height="16" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 6px;">
                <circle cx="8" cy="8" r="6" stroke="white" stroke-width="1.5"/>
                <path d="M5 8H11M8 5V11" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </template>
            <el-option
              v-for="model in modelList"
              :key="model.id"
              :label="model.name"
              :value="model.id"
            />
          </el-select>
          <el-button
            type="primary"
            size="default"
            :icon="List"
            class="process-btn"
            @click="showProcessPanel = !showProcessPanel"
          >
            查看执行日志
          </el-button>
          <el-button
            type="primary"
            size="default"
            :icon="Download"
            class="export-btn"
            @click="handleExportReport"
            :disabled="!sessionStore.currentSessionId"
          >
            导出报告
          </el-button>
          <el-button
            type="primary"
            size="default"
            :icon="DataBoard"
            class="dashboard-btn"
            @click="$router.push('/dashboard')"
          >
            📌 我的看板
            <el-badge v-if="pinnedCount > 0" :value="pinnedCount" class="pinned-badge" />
          </el-button>
        </div>
      </el-header>
      
      <el-container class="main-container">
        <el-aside width="240px" class="left-sidebar">
          <DataResourceTree
            :database-tables="databaseTables"
            :saved-connections="savedConnections"
            :sessions-list="sessionStore.sessions"
            :current-session-id="sessionStore.currentSessionId"
            @connect-database="showDatabaseConnectionDialog = true"
            @quick-connect="handleQuickConnect"
            @delete-connection="handleDeleteConnection"
            @table-click="handleTableClick"
            @disconnect-database="handleDisconnectDatabase"
            @new-session="handleNewSession"
            @session-select="handleSessionSelect"
            @session-delete="handleSessionDelete"
          />
        </el-aside>
        
        <el-main class="content-area">
          <el-row :gutter="16" class="content-row">
            <el-col :span="showProcessPanel ? 11 : 12" class="chat-panel-col">
              <ChatPanel
                ref="chatPanelRef"
                :messages="messages"
                :loading="chatStore.isLoading"
                @send-message="handleSendMessage"
                @file-upload="handleFileUpload"
                @database-connect="showDatabaseConnectionDialog = true"
              />
            </el-col>
            
            <el-col :span="showProcessPanel ? 13 : 12" class="workspace-col">
              <WorkspacePanel
                ref="workspacePanelRef"
                :tabs="workspaceTabs"
                :active-tab="activeWorkspaceTab"
                @tab-change="handleTabChange"
                @tab-close="handleTabClose"
              />
            </el-col>
          </el-row>
        </el-main>
      </el-container>
    </el-container>
    
    <el-drawer
      v-model="showProcessPanel"
      title="执行过程"
      size="420px"
      direction="btt"
      class="process-drawer"
    >
      <ExecutionProcessPanel
        :process-log="executionProcessLog"
        :loading="chatStore.isLoading"
      />
    </el-drawer>
    
    <DatabaseConnection
      :visible="showDatabaseConnectionDialog"
      :preset-connection="presetConnection"
      @connection-success="handleDatabaseConnection"
      @query-result="handleDatabaseQueryResult"
      @close="showDatabaseConnectionDialog = false; presetConnection = null"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, List, Download, DataBoard } from '@element-plus/icons-vue'

import { useChatStore } from '../store/chatStore'
import { useSessionStore } from '../store'

import DataResourceTree from '../components/bi/DataResourceTree.vue'
import ChatPanel from '../components/bi/ChatPanel.vue'
import WorkspacePanel from '../components/bi/WorkspacePanel.vue'
import ExecutionProcessPanel from '../components/bi/ExecutionProcessPanel.vue'
import DatabaseConnection from '../components/DatabaseConnection.vue'

import { sessionService, uploadService, databaseService } from '../api/services'

const chatStore = useChatStore()
const sessionStore = useSessionStore()

const showProcessPanel = ref(false)
const showDatabaseConnectionDialog = ref(false)
const currentModel = ref('ali-qwen')
const modelList = ref([
  { id: 'ali-qwen', name: '阿里云 Qwen Turbo' },
  { id: 'deepseek', name: 'DeepSeek R1' },
  { id: 'volcengine', name: '火山引擎 Doubao' },
  { id: 'spark', name: '星火大模型' }
])

const messages = ref([])
const workspaceTabs = ref([])
const activeWorkspaceTab = ref('')
const executionProcessLog = ref([])
const databaseTables = ref([])
const savedConnections = ref([])
const presetConnection = ref(null)
let currentDatabaseConnectionId = null

const chatPanelRef = ref(null)
const workspacePanelRef = ref(null)

const currentFileName = computed(() => sessionStore.fileName)

const pinnedCount = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('pinnedCharts') || '[]').length
  } catch {
    return 0
  }
})

const SESSION_STORAGE_PREFIX = 'zhixi_session_'
const SESSION_TTL = 24 * 60 * 60 * 1000

function saveSessionState() {
  const sid = sessionStore.currentSessionId
  if (!sid) return
  try {
    localStorage.setItem(SESSION_STORAGE_PREFIX + sid, JSON.stringify({
      messages: messages.value,
      workspaceTabs: workspaceTabs.value,
      activeWorkspaceTab: activeWorkspaceTab.value,
      timestamp: Date.now()
    }))
  } catch (e) {
    console.warn('保存会话状态失败:', e)
  }
}

function restoreSessionState() {
  const sid = sessionStore.currentSessionId
  if (!sid) return
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_PREFIX + sid)
    if (!raw) return
    const state = JSON.parse(raw)
    if (Date.now() - state.timestamp > SESSION_TTL) {
      localStorage.removeItem(SESSION_STORAGE_PREFIX + sid)
      return
    }
    messages.value = state.messages || []
    workspaceTabs.value = state.workspaceTabs || []
    activeWorkspaceTab.value = state.activeWorkspaceTab || ''
  } catch (e) {
    console.warn('恢复会话状态失败:', e)
  }
}

function cleanupExpiredSessions() {
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(SESSION_STORAGE_PREFIX)) {
        try {
          const state = JSON.parse(localStorage.getItem(key))
          if (state && Date.now() - state.timestamp > SESSION_TTL) {
            localStorage.removeItem(key)
          }
        } catch { /* ignore */ }
      }
    }
  } catch { /* ignore */ }
}

watch([messages, workspaceTabs, activeWorkspaceTab], () => {
  saveSessionState()
}, { deep: true })

const handleSendMessage = async (text) => {
  if (!text.trim()) return
  
  const findExistingTab = (title, type) => {
    return workspaceTabs.value.findIndex(tab => {
      if (tab.type !== type) return false
      if (tab.title === title) return true
      if (title === '分析结果' && tab.title === '分析结果') return true
      if (type === 'table' && (
        tab.title.startsWith(title + ' (') ||
        tab.title.startsWith(title + '(')
      )) return true
      return false
    })
  }
  
  const upsertTab = (title, type, data, chartOption = null) => {
    const existingIndex = findExistingTab(title, type)
    if (existingIndex > -1) {
      workspaceTabs.value[existingIndex].data = data
      if (chartOption) workspaceTabs.value[existingIndex].chartOption = chartOption
      activeWorkspaceTab.value = workspaceTabs.value[existingIndex].id
    } else {
      const tabId = `${type}-${Date.now()}`
      const tab = { id: tabId, title, type, data }
      if (chartOption) tab.chartOption = chartOption
      workspaceTabs.value.push(tab)
      activeWorkspaceTab.value = tabId
    }
  }
  
  messages.value.push({ role: 'user', content: text })
  chatStore.setLoading(true)
  executionProcessLog.value = []
  
  try {
    const currentSession = sessionStore.sessions.find(s => s.id === sessionStore.currentSessionId)
    const isDatabaseSession = currentSession?.isDatabase
    
    const chartKeywords = ["图表", "画图", "可视化", "折线图", "柱状图", "饼图"]
    
    if (isDatabaseSession && currentSession?.connectionId) {
      const chatToSqlResponse = await databaseService.chatToSql(currentSession.connectionId, text)
      if (chatToSqlResponse.status === 'ok' && chatToSqlResponse.sql) {
        messages.value.push({
          role: 'ai',
          type: 'code',
          content: chatToSqlResponse.sql,
          language: 'sql'
        })
        
        const queryResult = await databaseService.executeQuery(
          currentSession.connectionId,
          chatToSqlResponse.sql,
          100
        )
        
        if (queryResult.status === 'ok') {
          upsertTab('查询结果', 'table', queryResult.data)
          
          let analysisSummary = `查询成功，共 ${queryResult.row_count} 条数据`
          
          const wantsChart = chartKeywords.some(k => text.includes(k))
          if (wantsChart) {
            try {
              import('@/utils/chartGenerator').then(module => {
                const chartData = module.generate_chart_config(queryResult.data, text)
                if (chartData) {
                  upsertTab(`图表-${text.slice(0, 10)}`, 'chart', null, chartData)
                  analysisSummary += "（已生成图表）"
                }
              })
            } catch (err) {
              console.error('生成图表失败:', err)
            }
          }
          
          messages.value.push({
            role: 'ai',
            type: 'text',
            content: analysisSummary
          })
        }
      }
    } else {
      const response = await sessionService.sendMessage(
        sessionStore.currentSessionId,
        text,
        currentModel.value
      )
      
      if (response.status === 'ok') {
        if (response.execution_log) {
          executionProcessLog.value = response.execution_log
        }
        
        if (response.generated_sql) {
          messages.value.push({
            role: 'ai',
            type: 'code',
            content: response.generated_sql,
            language: 'sql'
          })
        }
        
        messages.value.push({
          role: 'ai',
          type: 'text',
          content: response.analysis_summary || '分析完成'
        })
        
        if (response.is_multi_table_response && response.multi_table_data) {
          const tableNames = Object.keys(response.multi_table_data)
          tableNames.forEach((tableName, index) => {
            const tableData = response.multi_table_data[tableName]
            upsertTab(tableName, 'table', tableData.data)
          })
        }
        else if (response.result) {
          let title = response.current_table_name || '分析结果'
          upsertTab(title, 'table', response.result)
        }
        
        if (response.chart_option) {
          upsertTab(`图表-${text.slice(0, 10)}`, 'chart', null, response.chart_option)
        }
      }
    }
  } catch (error) {
    ElMessage.error('消息发送失败')
  } finally {
    chatStore.setLoading(false)
  }
}

const handleFileUpload = async (file) => {
  try {
    const response = await uploadService.uploadFile(file)
    if (response.status === 'ok') {
      sessionStore.setCurrentSession(
        response.session_id,
        response.filename,
        response.data,
        response.columns
      )

      sessionStore.addSession({
        id: response.session_id,
        fileName: response.filename,
        displayName: `${response.filename} 文件分析`,
        timestamp: new Date().toISOString(),
        previewData: response.data,
        columns: response.columns,
        tableCount: response.table_count || 1,
        allTablesInfo: response.all_tables_info || null
      })

      ElMessage.success(response.message || '文件上传成功')
      
      if (response.all_tables_info && Object.keys(response.all_tables_info).length > 1) {
        const tableNames = Object.keys(response.all_tables_info)
        
        tableNames.forEach((tableName, index) => {
          const tableInfo = response.all_tables_info[tableName]
          const tabId = `table-${Date.now()}-${index}`
          
          workspaceTabs.value.push({
            id: tabId,
            title: `${tableName} (${tableInfo.row_count}行)`,
            type: 'table',
            data: tableInfo.preview_data
          })
          
          if (index === 0) {
            activeWorkspaceTab.value = tabId
            
            sessionStore.previewData = tableInfo.preview_data
            sessionStore.columns = tableInfo.columns
          }
        })
      } else {
        workspaceTabs.value.push({
          id: `preview-${Date.now()}`,
          title: response.filename,
          type: 'table',
          data: response.data
        })
        if (workspaceTabs.value.length === 1) {
          activeWorkspaceTab.value = workspaceTabs.value[0].id
        }
      }
    }
  } catch (error) {
    ElMessage.error('文件上传失败')
  }
}

const handleTabChange = (tabId) => {
  activeWorkspaceTab.value = tabId
}

const handleTabClose = (tabId) => {
  const index = workspaceTabs.value.findIndex(t => t.id === tabId)
  if (index > -1) {
    workspaceTabs.value.splice(index, 1)
    if (activeWorkspaceTab.value === tabId && workspaceTabs.value.length > 0) {
      activeWorkspaceTab.value = workspaceTabs.value[Math.max(0, index - 1)].id
    }
  }
}

const handleDatabaseConnection = async (connection) => {
  try {
    const connectionId = connection.connectionId
    const dbName = connection.connectionInfo.database
    
    currentDatabaseConnectionId = connectionId
    
    const connectionExists = savedConnections.value.some(
      conn => conn.database === connection.connectionInfo.database && 
              conn.host === connection.connectionInfo.host &&
              conn.port === connection.connectionInfo.port
    )
    
    if (!connectionExists) {
      savedConnections.value.push(connection.connectionInfo)
      localStorage.setItem('savedDatabaseConnections', JSON.stringify(savedConnections.value))
    }
    
    const response = await databaseService.getTables(connectionId)
    if (response.status === 'ok') {
      databaseTables.value = response.tables
      
      const dbFileName = `${dbName}数据库`
      
      sessionStore.addSession({
        id: `db-${connectionId}`,
        fileName: dbFileName,
        displayName: `${dbName}数据库数据分析`,
        timestamp: new Date().toISOString(),
        connectionId: connectionId,
        connectionInfo: connection.connectionInfo,
        isDatabase: true,
        tables: response.tables
      })
      
      sessionStore.setCurrentSession(
        `db-${connectionId}`,
        dbFileName,
        [],
        [],
        null
      )
      
      if (response.tables.length > 0) {
        const firstTable = response.tables[0]
        try {
          const queryResult = await databaseService.executeQuery(
            connectionId,
            `SELECT * FROM \`${firstTable.name}\``,
            50
          )
          if (queryResult.status === 'ok') {
            workspaceTabs.value.push({
              id: `table-${Date.now()}`,
              title: firstTable.name,
              type: 'table',
              data: queryResult.data
            })
            activeWorkspaceTab.value = workspaceTabs.value[0].id
            
            sessionStore.previewData = queryResult.data
            sessionStore.columns = firstTable.columns
          }
        } catch (err) {
          console.error('获取表数据失败:', err)
        }
      }
    }
  } catch (error) {
    ElMessage.error('获取数据库表失败')
  }
}

const handleQuickConnect = async (connectionInfo) => {
  try {
    presetConnection.value = connectionInfo
    showDatabaseConnectionDialog.value = true
  } catch (error) {
    ElMessage.error('快速连接失败')
  }
}

const handleDeleteConnection = (index) => {
  savedConnections.value.splice(index, 1)
  localStorage.setItem('savedDatabaseConnections', JSON.stringify(savedConnections.value))
  ElMessage.success('已删除连接')
}

const handleTableClick = async (table) => {
  try {
    const currentSession = sessionStore.sessions.find(s => s.id === sessionStore.currentSessionId)
    if (!currentSession?.connectionId) {
      ElMessage.warning('请先连接数据库')
      return
    }
    
    const queryResult = await databaseService.executeQuery(
      currentSession.connectionId,
      `SELECT * FROM \`${table.name}\``,
      50
    )
    
    if (queryResult.status === 'ok') {
      sessionStore.previewData = queryResult.data
      sessionStore.columns = table.columns
      
      let existingTab = null
      if (workspaceTabs.value.length > 0) {
        existingTab = workspaceTabs.value.find(t => t.type === 'table')
      }
      
      if (existingTab) {
        existingTab.title = table.name
        existingTab.data = queryResult.data
        activeWorkspaceTab.value = existingTab.id
      } else {
        const tabId = `table-${Date.now()}`
        workspaceTabs.value.push({
          id: tabId,
          title: table.name,
          type: 'table',
          data: queryResult.data
        })
        activeWorkspaceTab.value = tabId
      }
    }
  } catch (error) {
    ElMessage.error('查询表数据失败')
  }
}

const handleDatabaseQueryResult = (result) => {
  if (result && result.data && result.data.length > 0) {
    workspaceTabs.value.push({
      id: `table-${Date.now()}`,
      title: '查询结果',
      type: 'table',
      data: result.data
    })
    activeWorkspaceTab.value = workspaceTabs.value[workspaceTabs.value.length - 1].id
  }
}

const handleDisconnectDatabase = async () => {
  try {
    const currentSession = sessionStore.sessions.find(s => s.id === sessionStore.currentSessionId)
    if (currentSession?.connectionId) {
      await databaseService.disconnectDatabase(currentSession.connectionId)
      
      databaseTables.value = []
      workspaceTabs.value = []
      activeWorkspaceTab.value = ''
      currentDatabaseConnectionId = null
      
      sessionStore.previewData = []
      sessionStore.columns = []
      
      sessionStore.sessions = sessionStore.sessions.filter(s => s.id !== currentSession.id)
      sessionStore.currentSessionId = null
      sessionStore.fileName = ''
      
      ElMessage.success('数据库连接已断开')
    }
  } catch (error) {
    ElMessage.error('断开连接失败')
  }
}

const handleExportReport = async () => {
  if (!sessionStore.currentSessionId) {
    ElMessage.warning('请先选择一个会话')
    return
  }
  
  const currentSession = sessionStore.sessions.find(s => s.id === sessionStore.currentSessionId)
  if (!currentSession) {
    ElMessage.error('会话信息不存在')
    return
  }
  
  const now = new Date().toLocaleString('zh-CN')
  
  let htmlContent = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智析分析报告 - ${currentSession.fileName || '未命名会话'}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #333; padding: 40px; background: #f5f7fa; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #6B5CE8; margin-bottom: 10px; font-size: 28px; }
        .subtitle { text-align: center; color: #869099; margin-bottom: 30px; font-size: 14px; }
        .section { margin-bottom: 30px; padding: 20px; border: 1px solid #E5E6EB; border-radius: 8px; }
        .section-title { font-size: 18px; font-weight: 600; color: #1D2129; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #F9F0FF; }
        .info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .info-item { padding: 10px; background: #F9F0FF; border-radius: 6px; }
        .info-label { font-size: 12px; color: #869099; margin-bottom: 4px; }
        .info-value { font-size: 14px; color: #1D2129; font-weight: 500; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th { background: linear-gradient(135deg, #6B5CE8, #8B7DF2); color: white; padding: 10px; text-align: left; font-weight: 600; }
        td { padding: 10px; border-bottom: 1px solid #E5E6EB; }
        tr:hover { background: #F9F0FF; }
        .message { margin-bottom: 15px; padding: 15px; border-radius: 8px; }
        .message.user { background: #E8F3FF; border-left: 4px solid #1890ff; }
        .message.ai { background: #F9F0FF; border-left: 4px solid #6B5CE8; }
        .message-role { font-size: 12px; font-weight: 600; margin-bottom: 5px; }
        .message-content { font-size: 14px; white-space: pre-wrap; word-break: break-word; }
        pre { background: #1D2129; color: #F5F7FA; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; }
        code { font-family: 'JetBrains Mono', Consolas, monospace; }
        .chart-img { max-width: 100%; border-radius: 8px; border: 1px solid #E5E6EB; margin: 10px 0; }
        .stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }
        .stat-item { padding: 8px 12px; background: #F0F5FF; border-radius: 6px; text-align: center; }
        .stat-label { font-size: 11px; color: #869099; }
        .stat-value { font-size: 16px; font-weight: 600; color: #6B5CE8; }
        .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E5E6EB; color: #869099; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 智析分析报告</h1>
        <p class="subtitle">生成时间：${now}</p>
        
        <div class="section">
            <div class="section-title">📋 会话信息</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">文件/数据源名称</div>
                    <div class="info-value">${currentSession.fileName || '未命名'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">会话类型</div>
                    <div class="info-value">${currentSession.isDatabase ? '数据库连接' : '文件分析'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">创建时间</div>
                    <div class="info-value">${new Date(currentSession.timestamp).toLocaleString('zh-CN')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">数据表数量</div>
                    <div class="info-value">${currentSession.tableCount || 1} 个</div>
                </div>
            </div>
        </div>
  `

  // 数据统计摘要
  const tableTabs = workspaceTabs.value.filter(t => t.type === 'table' && t.data && t.data.length > 0)
  if (tableTabs.length > 0) {
    htmlContent += `
        <div class="section">
            <div class="section-title">📊 数据统计摘要</div>
    `
    const seenTitles = new Set()
    tableTabs.forEach(tab => {
      if (seenTitles.has(tab.title)) return
      seenTitles.add(tab.title)
      const cols = Object.keys(tab.data[0])
      const numericCols = cols.filter(col => tab.data.some(row => typeof row[col] === 'number' && !isNaN(row[col])))
      htmlContent += `<h3 style="margin: 10px 0; color: #6B5CE8;">${tab.title}（${tab.data.length}行 × ${cols.length}列）</h3>`
      if (numericCols.length > 0) {
        htmlContent += `<div class="stat-grid">`
        numericCols.slice(0, 8).forEach(col => {
          const values = tab.data.map(row => Number(row[col])).filter(v => !isNaN(v))
          if (values.length > 0) {
            const min = Math.min(...values)
            const max = Math.max(...values)
            const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1)
            htmlContent += `
              <div class="stat-item">
                <div class="stat-label">${col}</div>
                <div class="stat-value">${avg}</div>
                <div class="stat-label">min:${min} max:${max}</div>
              </div>
            `
          }
        })
        htmlContent += `</div>`
      }
    })
    htmlContent += `</div>`
  }

  // 智能洞察
  try {
    const insightsRes = await sessionService.getInsights(sessionStore.currentSessionId, currentModel.value)
    if (insightsRes.status === 'ok' && insightsRes.insights && insightsRes.insights.length > 0) {
      htmlContent += `
        <div class="section">
            <div class="section-title">💡 智能洞察</div>
            <ul style="padding-left: 20px; line-height: 2;">
      `
      insightsRes.insights.forEach(insight => {
        htmlContent += `<li style="margin-bottom: 8px; color: #1D2129;">${insight.replace(/\n/g, '<br>')}</li>`
      })
      htmlContent += `</ul></div>`
    }
  } catch (e) {
    console.warn('获取智能洞察失败:', e)
  }

  // SQL语句
  const sqlMessages = messages.value.filter(m => m.type === 'code' && m.language === 'sql')
  if (sqlMessages.length > 0) {
    htmlContent += `
        <div class="section">
            <div class="section-title">🔧 生成的SQL语句</div>
    `
    sqlMessages.forEach((msg, i) => {
      htmlContent += `<h3 style="margin: 10px 0; color: #6B5CE8;">SQL ${i + 1}</h3><pre><code>${msg.content}</code></pre>`
    })
    htmlContent += `</div>`
  }

  // 对话记录
  htmlContent += `
        <div class="section">
            <div class="section-title">💬 对话记录</div>
  `

  messages.value.forEach(msg => {
    const role = msg.role === 'user' ? '用户' : 'AI助手'
    const roleClass = msg.role
    let content = msg.content
    
    if (msg.type === 'code') {
      content = `<pre><code>${content}</code></pre>`
    } else {
      content = `<div class="message-content">${content.replace(/\n/g, '<br>')}</div>`
    }
    
    htmlContent += `
            <div class="message ${roleClass}">
                <div class="message-role">${role}</div>
                ${content}
            </div>
    `
  })

  htmlContent += `</div>`

  // 数据预览（去重，每表只出现一次，展示前5行）
  if (tableTabs.length > 0) {
    htmlContent += `
        <div class="section">
            <div class="section-title">📈 数据预览</div>
    `

    const seenTableTitles = new Set()
    tableTabs.forEach(tab => {
      if (seenTableTitles.has(tab.title)) return
      seenTableTitles.add(tab.title)
      
      const columns = Object.keys(tab.data[0])
      
      htmlContent += `
            <h3 style="margin: 15px 0 10px; color: #6B5CE8;">${tab.title}</h3>
            <table>
                <thead>
                    <tr>
                        ${columns.map(col => `<th>${col}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
        `
      
      tab.data.slice(0, 5).forEach(row => {
        htmlContent += `<tr>${columns.map(col => `<td>${row[col] !== undefined && row[col] !== null ? row[col] : '-'}</td>`).join('')}</tr>`
      })
      
      if (tab.data.length > 5) {
        htmlContent += `<tr><td colspan="${columns.length}" style="text-align: center; color: #869099;">... 共 ${tab.data.length} 条数据，仅展示前5条</td></tr>`
      }
      
      htmlContent += `
                </tbody>
            </table>
        `
    })
    htmlContent += `</div>`
  }

  // 图表截图
  const chartTabs = workspaceTabs.value.filter(t => t.type === 'chart' && t.chartOption)
  if (chartTabs.length > 0) {
    htmlContent += `
        <div class="section">
            <div class="section-title">📉 分析图表</div>
    `
    chartTabs.forEach(tab => {
      const chartTitle = tab.chartOption?.title?.text || tab.title
      htmlContent += `<h3 style="margin: 10px 0; color: #6B5CE8;">${chartTitle}</h3>`
      htmlContent += `<div id="chart-${tab.id}" style="width:100%; height:400px; margin: 10px 0;"></div>`
    })
    htmlContent += `
        </div>
        <scr` + `ipt src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></scr` + `ipt>
        <scr` + `ipt>
    `
    chartTabs.forEach(tab => {
      const optionJson = JSON.stringify(tab.chartOption).replace(/</g, '\\u003c').replace(/<\/script/g, '\\u003c/script')
      htmlContent += `
        (function() {
          var el = document.getElementById('chart-${tab.id}');
          if (el && window.echarts) {
            var chart = echarts.init(el);
            chart.setOption(${optionJson});
            window.addEventListener('resize', function() { chart.resize(); });
          }
        })();
      `
    })
    htmlContent += `</scr` + `ipt>`
  }

  htmlContent += `
        <div class="footer">
            <p>本报告由 智析（Intelligent Data Analysis）自动生成</p>
            <p>&copy; ${new Date().getFullYear()} 智析数据分析平台</p>
        </div>
    </div>
</body>
</html>
  `

  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `智析分析报告_${currentSession.fileName || '未命名'}_${new Date().toISOString().slice(0, 10)}.html`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('报告导出成功！')
}

const handleNewSession = () => {
  messages.value = []
  workspaceTabs.value = []
  activeWorkspaceTab.value = ''
  executionProcessLog.value = []
  
  sessionStore.clearSession()
  sessionStore.currentSessionId = null
  
  ElMessage.success('已创建新会话')
}

const handleSessionSelect = async (session) => {
  try {
    executionProcessLog.value = []
    
    sessionStore.setCurrentSession(
      session.id,
      session.fileName || '',
      [],
      session.columns || []
    )

    restoreSessionState()
    
    if (session.isDatabase && session.connectionId) {
      currentDatabaseConnectionId = session.connectionId
      databaseTables.value = session.tables || []
      
      const response = await databaseService.getTables(session.connectionId)
      if (response.status === 'ok') {
        databaseTables.value = response.tables
        
        if (response.tables.length > 0) {
          const firstTable = response.tables[0]
          try {
            const queryResult = await databaseService.executeQuery(
              session.connectionId,
              `SELECT * FROM \`${firstTable.name}\``,
              50
            )
            if (queryResult.status === 'ok') {
              workspaceTabs.value.push({
                id: `table-${Date.now()}`,
                title: firstTable.name,
                type: 'table',
                data: queryResult.data
              })
              activeWorkspaceTab.value = workspaceTabs.value[0].id
              
              sessionStore.previewData = queryResult.data
              sessionStore.columns = firstTable.columns
            }
          } catch (err) {
            console.error('获取表数据失败:', err)
          }
        }
      }
    } else {
      try {
        const response = await sessionService.getSessionMessages(session.id, 50)
        if (response.status === 'ok' && response.messages) {
          response.messages.forEach(msg => {
            if (msg.role === 'user' || msg.role === 'assistant') {
              messages.value.push({
                role: msg.role === 'assistant' ? 'ai' : 'user',
                type: 'text',
                content: msg.content
              })
            }
          })
          
          // 恢复预览数据到工作区
          if (session.allTablesInfo && Object.keys(session.allTablesInfo).length > 1) {
            // 多表情况：为每个表创建Tab
            const tableNames = Object.keys(session.allTablesInfo)
            
            tableNames.forEach((tableName, index) => {
              const tableInfo = session.allTablesInfo[tableName]
              const tabId = `table-${Date.now()}-${index}`
              
              workspaceTabs.value.push({
                id: tabId,
                title: `${tableName} (${tableInfo.row_count}行)`,
                type: 'table',
                data: tableInfo.preview_data
              })
              
              if (index === 0) {
                activeWorkspaceTab.value = tabId
                sessionStore.previewData = tableInfo.preview_data
                sessionStore.columns = tableInfo.columns
              }
            })
          } else if (session.previewData && session.previewData.length > 0) {
            // 单表情况：创建一个预览Tab
            workspaceTabs.value.push({
              id: `preview-${Date.now()}`,
              title: session.fileName || '数据预览',
              type: 'table',
              data: session.previewData
            })
            activeWorkspaceTab.value = workspaceTabs.value[0].id
            
            sessionStore.previewData = session.previewData
            sessionStore.columns = session.columns || []
          }
        }
      } catch (error) {
        console.error('加载会话消息失败:', error)
        ElMessage.warning('会话数据加载不完整')
      }
    }
    
    ElMessage.success(`已切换到会话：${session.displayName || session.fileName}`)
  } catch (error) {
    ElMessage.error('切换会话失败')
    console.error('切换会话错误:', error)
  }
}

const handleSessionDelete = async (sessionId) => {
  try {
    await sessionService.deleteSession(sessionId)
    sessionStore.deleteSession(sessionId)
    
    if (sessionStore.currentSessionId === sessionId) {
      handleNewSession()
    }
    
    ElMessage.success('会话已删除')
  } catch (error) {
    ElMessage.error('删除会话失败')
    console.error('删除会话错误:', error)
  }
}

onMounted(() => {
  console.log('智析工作台已加载')
  
  sessionStore.init()
  
  cleanupExpiredSessions()
  restoreSessionState()
  
  const saved = localStorage.getItem('savedDatabaseConnections')
  if (saved) {
    try {
      savedConnections.value = JSON.parse(saved)
    } catch (e) {
      console.error('加载保存的连接失败:', e)
    }
  }
})
</script>

<style lang="less" scoped>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.bi-workbench {
  width: 100%;
  height: 100vh;
  min-width: 1200px;
  background: #F5F7FA;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  overflow: hidden;
  
  .workbench-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    
    .top-header {
      height: 64px !important;
      background: linear-gradient(90deg, #8B7DF2, #9E8FF5);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      flex-shrink: 0;
      
      .header-left {
        display: flex;
        align-items: center;
        gap: 20px;
        
        .logo-wrapper {
          display: flex;
          align-items: center;
          gap: 12px;
          
          .logo-icon {
            width: 40px;
            height: 40px;
            flex-shrink: 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
          }
          
          .workbench-title {
            font-size: 20px;
            font-weight: 600;
            color: #FFFFFF;
            margin: 0;
            line-height: 1.2;
          }
        }
        
        .session-info {
          display: flex;
          align-items: center;
          gap: 6px;
          color: rgba(255, 255, 255, 0.9);
          font-size: 14px;
          padding: 6px 14px;
          background: rgba(255, 255, 255, 0.18);
          border-radius: 8px;
          transition: all 0.2s ease;
          
          &:hover {
            background: rgba(255, 255, 255, 0.25);
          }
        }
      }
      
      .header-right {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .model-select {
          width: 200px;
          
          :deep(.el-input__wrapper) {
            background: rgba(255, 255, 255, 0.15);
            box-shadow: none;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            padding: 8px 12px;
            transition: all 0.2s ease;
            
            &:hover {
              background: rgba(255, 255, 255, 0.3);
              box-shadow: 0 2px 8px rgba(255, 255, 255, 0.1);
            }
            
            &.is-focus {
              background: rgba(255, 255, 255, 0.35);
              box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
            }
          }
          
          :deep(.el-input__inner) {
            color: #FFFFFF;
            font-weight: 500;
            
            &::placeholder {
              color: rgba(255, 255, 255, 0.75);
            }
          }
          
          :deep(.el-input__suffix) {
            .el-select__caret {
              color: #FFFFFF;
            }
          }
        }
        
        .process-btn {
          width: 140px;
          background: rgba(255, 255, 255, 0.15);
          border: 1px solid rgba(255, 255, 255, 0.3);
          color: #FFFFFF;
          font-weight: 500;
          border-radius: 8px;
          padding: 10px 16px;
          transition: all 0.2s ease;
          
          &:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          }
          
          &:active {
            transform: translateY(0);
          }
        }
        
        .export-btn {
          width: 120px;
          background: linear-gradient(135deg, #52C41A, #73D13D);
          border: none;
          color: #FFFFFF;
          font-weight: 600;
          border-radius: 8px;
          padding: 10px 16px;
          transition: all 0.2s ease;
          
          &:hover:not(:disabled) {
            background: linear-gradient(135deg, #3DA114, #52C41A);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(82, 196, 26, 0.35);
          }
          
          &:active:not(:disabled) {
            transform: translateY(0);
          }
          
          &:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
        }
        
        .dashboard-btn {
          position: relative;
          width: 130px;
          background: linear-gradient(135deg, #E8A0BF, #F093FB);
          border: none;
          color: #FFFFFF;
          font-weight: 600;
          border-radius: 8px;
          padding: 10px 16px;
          transition: all 0.2s ease;
          
          &:hover {
            background: linear-gradient(135deg, #D48BB0, #E084EB);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(224, 132, 235, 0.35);
          }
          
          &:active {
            transform: translateY(0);
          }
          
          .pinned-badge {
            position: absolute;
            top: -6px;
            right: -6px;
          }
        }
      }
    }
    
    .main-container {
      flex: 1;
      display: flex;
      flex-direction: row;
      overflow: hidden;
      
      .left-sidebar {
        width: 240px !important;
        background: #FFFFFF;
        border-right: 1px solid #E5E6EB;
        overflow-y: auto;
        flex-shrink: 0;
      }
      
      .content-area {
        flex: 1;
        padding: 0;
        overflow: hidden;
        background: #F5F7FA;
        
        .content-row {
          height: 100%;
          
          .chat-panel-col,
          .workspace-col {
            height: 100%;
            display: flex;
            flex-direction: column;
            padding: 16px 0;
            
            &:first-child {
              padding-left: 16px;
            }
            
            &:last-child {
              padding-right: 16px;
            }
          }
        }
      }
    }
  }
  
  :deep(.process-drawer .el-drawer__header) {
    background: linear-gradient(90deg, #8B7DF2, #9E8FF5);
    color: #FFFFFF;
    margin-bottom: 0;
    padding: 16px 24px;
  }
  
  :deep(.process-drawer .el-drawer__body) {
    background: #F5F7FA;
    padding: 16px;
  }
}
</style>