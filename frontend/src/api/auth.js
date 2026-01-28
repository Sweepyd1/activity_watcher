import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
  withCredentials: true,  // ✅ куки автоматически
  headers: {
    'Content-Type': 'application/json'
  }
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Только user data, токены в куках
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  async register(data) {
    const response = await apiClient.post('/auth/register', data)
    return response.data
  },

  async login(email, password) {
    console.log('Отправка запроса на вход:', { email, password })
    
    const response = await apiClient.post('/auth/login', {
      email: email,
      password: password
    })
    
    console.log('Ответ от сервера:', response.data)
    return response.data
  },

  async getMe() {
    const response = await apiClient.post('/auth/me')
    return response.data
  },

  async logout() {
    await apiClient.post('/auth/logout')
  },
  getGoogleAuthUrl: async () => {
    const response = await apiClient.get('/auth/google');
    return response.data;
  },
  
  googleCallback: async (code) => {
    const response = await apiClient.get('/auth/google/callback', { code });
    return response.data;
  }
}

export default apiClient
