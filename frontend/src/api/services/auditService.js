import apiClient from './apiClient'

const auditService = {
  getLogs: (params = {}) => {
    return apiClient({ url: '/v1/audit/logs', method: 'get', params })
  },
  getStats: (days = 7) => {
    return apiClient({ url: '/v1/audit/stats', method: 'get', params: { days } })
  },
  exportLogs: (format = 'csv', startDate, endDate) => {
    const params = { format }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    return apiClient({ url: '/v1/audit/export', method: 'post', params, responseType: format === 'csv' ? 'blob' : 'json' })
  }
}

export default auditService
