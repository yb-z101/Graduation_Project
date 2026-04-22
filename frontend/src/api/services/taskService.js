import apiClient from './apiClient'

const taskService = {
  createAndExecute: (data) => {
    return apiClient({ url: '/v1/analysis-task/create-and-execute', method: 'post', data })
  },
  list: (sourceId, taskStatus) => {
    const params = {}
    if (sourceId !== undefined) params.source_id = sourceId
    if (taskStatus !== undefined) params.task_status = taskStatus
    return apiClient({ url: '/v1/analysis-task/list', method: 'get', params })
  },
  getDetail: (taskId) => {
    return apiClient({ url: `/v1/analysis-task/detail/${taskId}`, method: 'get' })
  },
  executeSessionTask: (sessionId, userPrompt, taskName) => {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('user_prompt', userPrompt)
    if (taskName) formData.append('task_name', taskName)
    return apiClient({ url: '/v1/analysis-task/session/execute', method: 'post', data: formData, headers: { 'Content-Type': 'multipart/form-data' } })
  },
  getDecision: (sessionId) => {
    return apiClient({ url: '/v1/analysis-task/decision', method: 'get', params: { session_id: sessionId } })
  }
}

export default taskService
