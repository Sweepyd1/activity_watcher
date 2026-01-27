// src/api/auth.js
import axios from 'axios'

// Создаем экземпляр axios с настройками
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Перехватчик для добавления токена
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Перехватчик для обработки ошибок
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Очищаем данные аутентификации при 401 ошибке
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  // Регистрация
  async register(data) {
    const response = await apiClient.post('/auth/register', data)
    return response.data
  },

  // Вход
  async login(email, password) {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // Получение текущего пользователя
  async getMe() {
    const response = await apiClient.get('/api/v1/auth/me')
    return response.data
  },

  // Подтверждение email
  async verifyEmail(token) {
    const response = await apiClient.get(`/api/v1/auth/verify/${token}`)
    return response.data
  },

  // Запрос сброса пароля
  async resetPassword(email) {
    const response = await apiClient.post('/api/v1/auth/reset-password', { email })
    return response.data
  },

  // Подтверждение сброса пароля
  async confirmResetPassword(data) {
    const response = await apiClient.post('/api/v1/auth/reset-password/confirm', data)
    return response.data
  },

  // Выход
  async logout() {
    const response = await apiClient.post('/api/v1/auth/logout')
    return response.data
  }
}

export default apiClient