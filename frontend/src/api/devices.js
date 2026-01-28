import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const devicesApi = {
  // Получить все устройства пользователя (GET запрос)
  async getAll() {
    const response = await apiClient.get('/devices')
    return response.data
  },
  
  // Создать устройство
  async create(deviceData) {
    const response = await apiClient.post('/devices/new', deviceData)
    return response.data
  },
  
  // Создать токен для устройства
  async createToken(deviceId, tokenData) {
    // Отправляем POST на /devices/tokens с device_id в теле
    const response = await apiClient.post('/devices/tokens', {
      device_id: deviceId,
      ...tokenData
    })
    return response.data
  },
  
  // Получить токены устройства
  async getTokens(deviceId) {
    const response = await apiClient.get(`/devices/${deviceId}/tokens`)
    return response.data
  },
  
  // Отозвать токен
  async revokeToken(deviceId, tokenId) {
    const response = await apiClient.delete(`/devices/${deviceId}/tokens/${tokenId}`)
    return response.data
  },
  
  // Удалить устройство
  async delete(deviceId) {
    const response = await apiClient.delete(`/devices/${deviceId}`)
    return response.data
  }
}