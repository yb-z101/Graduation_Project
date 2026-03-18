import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
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