import { defineStore } from 'pinia'

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessionId: null,
    filename: '',
    previewData: [],
    columns: []
  }),
  actions: {
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
    }
  }
})