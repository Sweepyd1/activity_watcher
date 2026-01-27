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

        <!-- Уведомления -->
        <div v-if="message" :class="['alert', message.type]">
          {{ message.text }}
        </div>

        <!-- Форма -->
        <div class="auth-form">
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
                :class="{ 'error': errors.email }"
                @keyup.enter="register"
              >
              <span v-if="errors.email" class="error-text">{{ errors.email }}</span>
            </div>

            <div class="form-group">
              <label for="username">Имя пользователя (опционально)</label>
              <input 
                type="text" 
                id="username"
                v-model="form.username"
                placeholder="Придумайте имя"
                class="form-input"
                :class="{ 'error': errors.username }"
                @keyup.enter="register"
              >
              <span v-if="errors.username" class="error-text">{{ errors.username }}</span>
            </div>

            <div class="form-group">
              <label for="password">Пароль</label>
              <input 
                type="password" 
                id="password"
                v-model="form.password"
                placeholder="Не менее 8 символов"
                class="form-input"
                :class="{ 'error': errors.password }"
                @keyup.enter="register"
              >
              <span v-if="errors.password" class="error-text">{{ errors.password }}</span>
            </div>

            <div class="form-group">
              <label for="confirmPassword">Подтвердите пароль</label>
              <input 
                type="password" 
                id="confirmPassword"
                v-model="form.confirmPassword"
                placeholder="Повторите пароль"
                class="form-input"
                :class="{ 'error': errors.confirmPassword }"
                @keyup.enter="register"
              >
              <span v-if="errors.confirmPassword" class="error-text">{{ errors.confirmPassword }}</span>
            </div>

            <button 
              class="submit-btn" 
              @click="register"
              :disabled="authStore.loading"
              :class="{ 'loading': authStore.loading }"
            >
              <span v-if="authStore.loading">
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
            <button class="google-btn" @click="signInWithGoogle" :disabled="authStore.loading">
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
                :class="{ 'error': loginErrors.email }"
                @keyup.enter="login"
              >
              <span v-if="loginErrors.email" class="error-text">{{ loginErrors.email }}</span>
            </div>

            <div class="form-group">
              <label for="loginPassword">Пароль</label>
              <input 
                type="password" 
                id="loginPassword"
                v-model="loginForm.password"
                placeholder="Ваш пароль"
                class="form-input"
                :class="{ 'error': loginErrors.password }"
                @keyup.enter="login"
              >
              <span v-if="loginErrors.password" class="error-text">{{ loginErrors.password }}</span>
            </div>

            <div class="form-options">
           
              <router-link to="/forgot-password" class="link">Забыли пароль?</router-link>
            </div>

            <button 
              class="submit-btn" 
              @click="login"
              :disabled="authStore.loading"
              :class="{ 'loading': authStore.loading }"
            >
              <span v-if="authStore.loading">
                <span class="spinner"></span> Вход...
              </span>
              <span v-else>Войти</span>
            </button>

            <div class="auth-footer">
              <p>Нет аккаунта? <a href="#" @click.prevent="toggleForm" class="link">Зарегистрироваться</a></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Состояния
const isRegister = ref(false)
const rememberMe = ref(localStorage.getItem('remember_me') === 'true')
const message = ref(null)

// Данные форм
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

// Ошибки
const errors = reactive({})
const loginErrors = reactive({})

// Инициализация
onMounted(() => {
  // Если пользователь уже авторизован, перенаправляем в профиль
  if (authStore.isAuthenticated) {
    router.push('/profile')
  }
  
  // Восстанавливаем сохраненный email
  const savedEmail = localStorage.getItem('saved_email')
  if (savedEmail) {
    loginForm.email = savedEmail
  }
})

// Переключение между формами
const toggleForm = () => {
  isRegister.value = !isRegister.value
  clearMessages()
  clearErrors()
}

// Очистка сообщений
const clearMessages = () => {
  message.value = null
  authStore.clearError()
}

const clearErrors = () => {
  Object.keys(errors).forEach(key => errors[key] = '')
  Object.keys(loginErrors).forEach(key => loginErrors[key] = '')
}

// Валидация формы регистрации
const validateRegister = () => {
  clearErrors()
  let valid = true

  if (!form.email) {
    errors.email = 'Email обязателен'
    valid = false
  } else if (!/\S+@\S+\.\S+/.test(form.email)) {
    errors.email = 'Введите корректный email'
    valid = false
  }

  if (form.username && !/^[a-zA-Z0-9_-]+$/.test(form.username)) {
    errors.username = 'Имя пользователя может содержать только буквы, цифры, дефисы и подчеркивания'
    valid = false
  }

  if (!form.password) {
    errors.password = 'Пароль обязателен'
    valid = false
  } else if (form.password.length < 8) {
    errors.password = 'Пароль должен быть не менее 8 символов'
    valid = false
  } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(form.password)) {
    errors.password = 'Пароль должен содержать буквы верхнего и нижнего регистра и цифры'
    valid = false
  }

  if (form.password !== form.confirmPassword) {
    errors.confirmPassword = 'Пароли не совпадают'
    valid = false
  }

  return valid
}

// Валидация формы входа
const validateLogin = () => {
  clearErrors()
  let valid = true

  if (!loginForm.email) {
    loginErrors.email = 'Email обязателен'
    valid = false
  } else if (!/\S+@\S+\.\S+/.test(loginForm.email)) {
    loginErrors.email = 'Введите корректный email'
    valid = false
  }

  if (!loginForm.password) {
    loginErrors.password = 'Пароль обязателен'
    valid = false
  }

  return valid
}

// Регистрация
const register = async () => {
  if (!validateRegister()) return

  try {
    console.log("НАЖАЛ")
    await authStore.register({
      email: form.email,
      password: form.password,
      confirm_password: form.confirmPassword,
      username: form.username || undefined
    })
    
    message.value = {
      text: '',
      type: 'success'
    }
    
  } catch (error) {
    const errorMsg = error.message || 'Ошибка при регистрации'
    
    // Обработка конкретных ошибок
    if (errorMsg.includes('уже существует')) {
      errors.email = errorMsg
    } else if (errorMsg.includes('пароль')) {
      errors.password = errorMsg
    } else {
      message.value = {
        text: errorMsg,
        type: 'error'
      }
    }
  }
}

// Вход
const login = async () => {
  if (!validateLogin()) return

  try {
    // Сохраняем email если выбрана опция "запомнить меня"
    if (rememberMe.value) {
      localStorage.setItem('saved_email', loginForm.email)
      localStorage.setItem('remember_me', 'true')
    } else {
      localStorage.removeItem('saved_email')
      localStorage.removeItem('remember_me')
    }

    await authStore.login(loginForm.email, loginForm.password)
    
  } catch (error) {
    const errorMsg = error.message || 'Ошибка при входе'
    
    if (errorMsg.includes('email') || errorMsg.includes('Email')) {
      loginErrors.email = errorMsg
    } else if (errorMsg.includes('пароль') || errorMsg.includes('password')) {
      loginErrors.password = errorMsg
    } else if (errorMsg.includes('подтвержден') || errorMsg.includes('verified')) {
      message.value = {
        text: `${errorMsg}. Проверьте вашу почту для подтверждения.`,
        type: 'warning'
      }
    } else {
      message.value = {
        text: errorMsg,
        type: 'error'
      }
    }
  }
}

// Google OAuth
const signInWithGoogle = async () => {
  // Реализация OAuth
  console.log('Google auth clicked')
  // В будущем:
  // window.location.href = '/api/v1/auth/google'
}

// Сброс пароля
const forgotPassword = () => {
  router.push('/forgot-password')
}
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