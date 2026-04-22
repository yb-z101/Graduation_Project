import apiClient from './apiClient'

const datasourceService = {
  create: (data) => {
    return apiClient({ url: '/v1/datasource/create', method: 'post', data })
  },
  list: (sourceType) => {
    const params = {}
    if (sourceType !== undefined) params.source_type = sourceType
    return apiClient({ url: '/v1/datasource/list', method: 'get', params })
  },
  getDetail: (dsId) => {
    return apiClient({ url: `/v1/datasource/detail/${dsId}`, method: 'get' })
  },
  testConnect: (dsId, plainPassword) => {
    const data = {}
    if (plainPassword) data.plain_password = plainPassword
    return apiClient({ url: `/v1/datasource/test-connect/${dsId}`, method: 'post', data })
  }
}

export default datasourceService
