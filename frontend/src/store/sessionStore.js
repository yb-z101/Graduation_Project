import { defineStore } from 'pinia'

export const useSessionStore = defineStore('session', {
  state: () => ({
    token: '',
    userId: null,
    isLoggedIn: false
  }),
  actions: {
    setToken(token) {
      this.token = token
      this.isLoggedIn = true
    },
    logout() {
      this.token = ''
      this.userId = null
      this.isLoggedIn = false
    }
  }
})