import { defineStore } from 'pinia'

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessionId: null,
    filename: '',
    previewData: [],
    columns: [],
    currentSessionId: null,
    sessions: []
  }),
  actions: {
    // 初始化时从 localStorage 加载会话
    init() {
      const storedSessions = localStorage.getItem('chat_sessions')
      if (storedSessions) {
        try {
          this.sessions = JSON.parse(storedSessions)
        } catch (error) {
          console.error('Failed to parse stored sessions:', error)
          this.sessions = []
        }
      }
    },
    
    // 保存会话到 localStorage
    saveSessions() {
      localStorage.setItem('chat_sessions', JSON.stringify(this.sessions))
    },
    
    setSession(data) {
      this.sessionId = data.session_id
      this.filename = data.filename
      this.previewData = data.preview
      this.columns = data.columns
    },
    
    clearSession() {
      this.sessionId = null
      this.filename = ''
      this.previewData = []
      this.columns = []
    },
    
    setCurrentSession(sessionId, fileName, data, columns) {
      this.currentSessionId = sessionId
      this.sessionId = sessionId
      this.filename = fileName
      this.previewData = data
      this.columns = columns
    },
    
    addSession(session) {
      // 检查是否已存在相同 sessionId 的会话
      const existingIndex = this.sessions.findIndex(s => s.id === session.id)
      
      if (existingIndex >= 0) {
        // 更新现有会话
        this.sessions[existingIndex] = { ...this.sessions[existingIndex], ...session }
      } else {
        // 添加新会话
        this.sessions.push(session)
        
        // 限制会话数量为5个
        if (this.sessions.length > 5) {
          // 按时间戳排序，删除最早的会话
          this.sessions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
          this.sessions = this.sessions.slice(0, 5)
        }
      }
      
      // 保存到 localStorage
      this.saveSessions()
    },
    
    // 清除所有会话
    clearAllSessions() {
      this.sessions = []
      this.currentSessionId = null
      this.clearSession()
      this.saveSessions()
    },
    
    // 删除指定会话
    deleteSession(sessionId) {
      this.sessions = this.sessions.filter(s => s.id !== sessionId)
      if (this.currentSessionId === sessionId) {
        this.currentSessionId = null
        this.clearSession()
      }
      this.saveSessions()
    }
  }
})