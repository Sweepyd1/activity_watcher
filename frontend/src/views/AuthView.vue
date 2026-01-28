<template>
  <div class="auth-view">
    <div class="auth-container">
      <div class="auth-card animate-fade-in">
        <!-- Логотип -->
        <div class="auth-header">
          <div class="logo">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <h1 class="gradient-text">TimeTracker</h1>
          </div>
          <p class="tagline">Отслеживайте своё время на всех устройствах</p>
        </div>

        <!-- Форма -->
        <div class="auth-form" v-if="!user">
          <div v-if="isRegister">
            <!-- Форма регистрации -->
            <div class="form-group">
              <label for="email">Email</label>
              <input 
                type="email" 
                id="email"
                v-model="form.email"
                placeholder="Ваш email"
                class="form-input"
                @keyup.enter="handleRegister"
              >
            </div>

            <div class="form-group">
              <label for="username">Имя пользователя (опционально)</label>
              <input 
                type="text" 
                id="username"
                v-model="form.username"
                placeholder="Придумайте имя"
                class="form-input"
                @keyup.enter="handleRegister"
              >
            </div>

            <div class="form-group">
              <label for="password">Пароль</label>
              <input 
                type="password" 
                id="password"
                v-model="form.password"
                placeholder="Не менее 8 символов"
                class="form-input"
                @keyup.enter="handleRegister"
              >
            </div>

            <div class="form-group">
              <label for="confirmPassword">Подтвердите пароль</label>
              <input 
                type="password" 
                id="confirmPassword"
                v-model="form.confirmPassword"
                placeholder="Повторите пароль"
                class="form-input"
                @keyup.enter="handleRegister"
              >
            </div>

            <button 
              class="submit-btn" 
              @click="handleRegister"
              :disabled="loading"
              :class="{ 'loading': loading }"
            >
              <span v-if="loading">
                <span class="spinner"></span> Регистрация...
              </span>
              <span v-else>Зарегистрироваться</span>
            </button>

            <div class="auth-footer">
              <p>Уже есть аккаунт? <a href="#" @click.prevent="toggleForm" class="link">Войти</a></p>
            </div>
          </div>

          <div v-else>
            <!-- Форма входа -->
            <button class="google-btn" @click="signInWithGoogle" :disabled="loading">
              <span class="google-icon">
                <svg viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
              </span>
              <span class="btn-text">Продолжить с Google</span>
            </button>

            <div class="divider">
              <span>или</span>
            </div>

            <div class="form-group">
              <label for="loginEmail">Email</label>
              <input 
                type="email" 
                id="loginEmail"
                v-model="loginForm.email"
                placeholder="Ваш email"
                class="form-input"
                @keyup.enter="handleLogin"
              >
            </div>

            <div class="form-group">
              <label for="loginPassword">Пароль</label>
              <input 
                type="password" 
                id="loginPassword"
                v-model="loginForm.password"
                placeholder="Ваш пароль"
                class="form-input"
                @keyup.enter="handleLogin"
              >
            </div>

            <div class="form-options">
              <router-link to="/forgot-password" class="link">Забыли пароль?</router-link>
            </div>

            <button 
              class="submit-btn" 
              @click="handleLogin"
              :disabled="loading"
              :class="{ 'loading': loading }"
            >
              <span v-if="loading">
                <span class="spinner"></span> Вход...
              </span>
              <span v-else>Войти</span>
            </button>

            <div class="auth-footer">
              <p>Нет аккаунта? <a href="#" @click.prevent="toggleForm" class="link">Зарегистрироваться</a></p>
            </div>
          </div>
        </div>

        <!-- Если авторизован -->
        <div v-else class="auth-success">
          <h2>Добро пожаловать!</h2>
          <p>Перенаправление на профиль...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/auth'
import Swal from 'sweetalert2'

const router = useRouter()

// Локальное состояние
const user = ref(null)
const loading = ref(false)
const isRegister = ref(false)

// Формы
const form = reactive({
  email: '',
  username: '',
  password: '',
  confirmPassword: ''
})

const loginForm = reactive({
  email: '',
  password: ''
})

// SweetAlert утилиты
const showErrorAlert = (title, message) => {
  Swal.fire({
    icon: 'error',
    title: title,
    text: message,
    confirmButtonText: 'OK',
    customClass: {
      confirmButton: 'swal2-confirm'
    }
  })
}

const showSuccessAlert = (title, message) => {
  Swal.fire({
    icon: 'success',
    title: title,
    text: message,
    confirmButtonText: 'OK',
    timer: 3000,
    timerProgressBar: true,
    customClass: {
      confirmButton: 'swal2-confirm'
    }
  })
}

const showInfoAlert = (title, message) => {
  Swal.fire({
    icon: 'info',
    title: title,
    text: message,
    confirmButtonText: 'OK',
    customClass: {
      confirmButton: 'swal2-confirm'
    }
  })
}

const showConfirmAlert = (title, message) => {
  return Swal.fire({
    icon: 'question',
    title: title,
    text: message,
    showCancelButton: true,
    confirmButtonText: 'Да',
    cancelButtonText: 'Нет',
    customClass: {
      confirmButton: 'swal2-confirm',
      cancelButton: 'swal2-cancel'
    }
  })
}


// Переключение форм
const toggleForm = () => {
  isRegister.value = !isRegister.value
}

// Валидация регистрации
const validateRegister = () => {
  const errors = []

  if (!form.email) {
    errors.push('Email обязателен')
  } else if (!/\S+@\S+\.\S+/.test(form.email)) {
    errors.push('Введите корректный email')
  }

  if (form.username && !/^[a-zA-Z0-9_-]+$/.test(form.username)) {
    errors.push('Имя пользователя может содержать только буквы, цифры, дефисы и подчеркивания')
  }

  if (!form.password) {
    errors.push('Пароль обязателен')
  } else if (form.password.length < 8) {
    errors.push('Пароль должен быть не менее 8 символов')
  } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(form.password)) {
    errors.push('Пароль должен содержать буквы верхнего и нижнего регистра и цифры')
  }

  if (form.password !== form.confirmPassword) {
    errors.push('Пароли не совпадают')
  }

  if (errors.length > 0) {
    showErrorAlert('Ошибка валидации', errors.join('\n'))
    return false
  }

  return true
}

// Валидация входа
const validateLogin = () => {
  const errors = []

  if (!loginForm.email) {
    errors.push('Email обязателен')
  } else if (!/\S+@\S+\.\S+/.test(loginForm.email)) {
    errors.push('Введите корректный email')
  }

  if (!loginForm.password) {
    errors.push('Пароль обязателен')
  }

  if (errors.length > 0) {
    showErrorAlert('Ошибка валидации', errors.join('\n'))
    return false
  }

  return true
}

// Регистрация
const handleRegister = async () => {
  if (!validateRegister()) return

  loading.value = true

  try {
    const response = await authApi.register({
      email: form.email,
      password: form.password,
      username: form.username || undefined
    })
    
    showSuccessAlert('Успешно!', 'Регистрация прошла успешно. Теперь вы можете войти.')
    
    // Очищаем форму
    Object.keys(form).forEach(key => form[key] = '')
    
    // Переключаем на форму входа
    isRegister.value = false
    
  } catch (err) {
    let errorMessage = 'Ошибка регистрации'
    
    if (err.response?.data?.detail) {
      errorMessage = err.response.data.detail
      if (typeof errorMessage === 'object') {
        errorMessage = errorMessage.error || JSON.stringify(errorMessage)
      }
    } else if (err.message) {
      errorMessage = err.message
    }
    
    // Убираем "Network Error" из сообщения для пользователя
    if (errorMessage.includes('Network Error')) {
      errorMessage = 'Проблема соединения с сервером'
    }
    
    showErrorAlert('Ошибка регистрации', errorMessage)
    
  } finally {
    loading.value = false
  }
}

// Вход
const handleLogin = async () => {
  if (!validateLogin()) return

  loading.value = true

  try {
    await authApi.login(loginForm.email, loginForm.password)
    
    showSuccessAlert('Успешный вход!', 'Перенаправление в профиль...')
    router.push("/profile")
    
    // Обновляем статус авторизации
    setTimeout(async () => {
      await checkAuth()
    }, 1000)
    
  } catch (err) {
    let errorMessage = 'Ошибка входа'
    
    if (err.response?.data?.detail) {
      errorMessage = err.response.data.detail
    } else if (err.message) {
      errorMessage = err.message
    }
    
    // Убираем "Network Error" из сообщения для пользователя
    if (errorMessage.includes('Network Error')) {
      errorMessage = 'Проблема соединения с сервером'
    }
    
    showErrorAlert('Ошибка входа', errorMessage)
    
  } finally {
    loading.value = false
  }
}

// В AuthView.vue, замените метод signInWithGoogle:
const signInWithGoogle = async () => {
   window.location.href = 'http://localhost:8000/auth/google'
  
          
      

};
</script>

<style scoped>
.auth-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-container {
  width: 100%;
  max-width: 400px;
}

.auth-card {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 12px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

h1 {
  font-size: 28px;
  font-weight: 700;
}

.tagline {
  color: var(--text-muted);
  font-size: 14px;
}

.google-btn {
  width: 100%;
  padding: 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
}

.google-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--text-muted);
}

.google-icon svg {
  width: 20px;
  height: 20px;
}

.divider {
  display: flex;
  align-items: center;
  margin: 24px 0;
  color: var(--text-muted);
  font-size: 14px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--border-color);
}

.divider span {
  padding: 0 16px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 16px;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 8px;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3);
}

.auth-footer {
  margin-top: 32px;
  text-align: center;
  font-size: 14px;
}

.auth-footer p {
  color: var(--text-muted);
  margin-bottom: 12px;
}

.link {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.link:hover {
  color: var(--primary-dark);
}
</style>