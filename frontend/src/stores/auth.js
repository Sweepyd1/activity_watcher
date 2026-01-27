// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // Состояние
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const loading = ref(false)
  const error = ref(null)

  // Геттеры
  const isAuthenticated = computed(() => !!accessToken.value)
  const isVerified = computed(() => user.value?.is_verified || false)

  // Мутации
  const setToken = (token) => {
    accessToken.value = token
    localStorage.setItem('access_token', token)
  }

  const setUser = (userData) => {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const clearAuth = () => {
    accessToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  const setError = (err) => {
    error.value = err
  }

  const clearError = () => {
    error.value = null
  }

  // Действия
  const register = async (userData) => {
    loading.value = true
    clearError()
    
    try {
      const response = await authApi.register(userData)
      
      // Если после регистрации сразу логиним
      if (response.access_token) {
        setToken(response.access_token)
        setUser(response.user)
        router.push('/profile')
      } else {
        // Или показываем сообщение о подтверждении email
        return response
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Ошибка регистрации'
      setError(errorMsg)
      throw new Error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  const login = async (email, password) => {
    loading.value = true
    clearError()
    
    try {
      const response = await authApi.login(email, password)
      
      setToken(response.access_token)
      setUser({
        id: response.user_id,
        email: response.email,
        ...(response.user || {})
      })
      
      router.push('/profile')
      return response
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Ошибка входа'
      setError(errorMsg)
      throw new Error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      clearAuth()
      router.push('/login')
    }
  }

  const checkAuth = async () => {
    if (!isAuthenticated.value) return false
    
    try {
      const userData = await authApi.getMe(accessToken.value)
      setUser(userData)
      return true
    } catch (err) {
      clearAuth()
      return false
    }
  }

  return {
    // Состояние
    accessToken,
    user,
    loading,
    error,
    
    // Геттеры
    isAuthenticated,
    isVerified,
    
    // Действия
    register,
    login,
    logout,
    checkAuth,
    clearError
  }
})