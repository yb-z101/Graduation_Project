import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],
    isLoading: false
  }),
  actions: {
    addMessage(message) {
      this.messages.push(message);
    },
    clearMessages() {
      this.messages = [];
    },
    setLoading(status) {
      this.isLoading = status;
    }
  }
})