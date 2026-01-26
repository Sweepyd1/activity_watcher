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
        <div class="auth-form">
          <!-- Кнопка Google -->
          <button class="google-btn" @click="signInWithGoogle">
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

          <!-- Форма входа -->
          <div class="form-group">
            <label for="email">Email</label>
            <input 
              type="email" 
              id="email"
              v-model="email"
              placeholder="Ваш email"
              class="form-input"
            >
          </div>

          <div class="form-group">
            <label for="password">Пароль</label>
            <input 
              type="password" 
              id="password"
              v-model="password"
              placeholder="Ваш пароль"
              class="form-input"
            >
          </div>

          <button class="submit-btn" @click="signIn">
            Войти
          </button>

          <div class="auth-footer">
            <p>Нет аккаунта? <router-link to="/auth" class="link">Зарегистрироваться</router-link></p>
            <router-link to="/profile" class="link">Перейти к профилю →</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const email = ref('')
const password = ref('')

const signInWithGoogle = () => {
  console.log('Google auth clicked')
  // Здесь будет логика OAuth
}

const signIn = () => {
  console.log('Sign in with:', email.value)
  // Здесь будет логика аутентификации
  router.push('/profile')
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