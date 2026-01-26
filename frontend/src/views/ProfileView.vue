<template>
  <div class="profile-view">
    <!-- Навигация -->
    <nav class="navbar">
      <div class="nav-container">
        <div class="nav-left">
          <router-link to="/" class="logo">
            <div class="logo-icon">⏱️</div>
            <span class="logo-text">TimeTracker</span>
          </router-link>
        </div>
        <div class="nav-right">
          <router-link to="/statistics" class="nav-link">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
            Статистика
          </router-link>
          <router-link to="/auth" class="nav-link logout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
            Выйти
          </router-link>
        </div>
      </div>
    </nav>

    <div class="profile-container animate-fade-in">
      <!-- Заголовок -->
      <div class="profile-header">
        <h1>Профиль</h1>
        <p class="subtitle">Управление аккаунтом и устройствами</p>
      </div>

      <div class="profile-content">
        <!-- Карточка пользователя -->
        <div class="profile-card user-card">
          <div class="user-info">
            <div class="avatar">
              <span class="avatar-text">AI</span>
            </div>
            <div class="user-details">
              <h2>Александр Иванов</h2>
              <p class="email">alex@example.com</p>
              <div class="user-stats">
                <div class="stat">
                  <span class="stat-label">На платформе с</span>
                  <span class="stat-value">15 янв 2024</span>
                </div>
                <div class="stat">
                  <span class="stat-label">Всего времени</span>
                  <span class="stat-value">142 ч 30 м</span>
                </div>
              </div>
            </div>
          </div>
          <button class="edit-btn">Редактировать</button>
        </div>

        <!-- Устройства -->
        <div class="profile-card devices-card">
          <div class="card-header">
            <h3>Активные устройства</h3>
            <span class="badge">{{ devices.length }} устройств</span>
          </div>

          <div class="devices-list">
            <div 
              v-for="device in devices" 
              :key="device.id"
              class="device-item"
              :class="{ 'active': device.isActive }"
            >
              <div class="device-icon" :class="getDeviceTypeClass(device.type)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path v-if="device.type === 'windows'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                  <path v-else-if="device.type === 'mac'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                  <path v-else-if="device.type === 'android'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                  <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                </svg>
              </div>
              <div class="device-info">
                <h4>{{ device.name }}</h4>
                <div class="device-meta">
                  <span class="device-type">{{ getDeviceTypeName(device.type) }}</span>
                  <span class="device-version">{{ device.osVersion }}</span>
                </div>
              </div>
              <div class="device-status">
                <div class="status-indicator" :class="{ 'online': device.isActive }"></div>
                <span class="status-text">{{ device.isActive ? 'В сети' : 'Не в сети' }}</span>
                <span class="last-seen">{{ formatLastSeen(device.lastSeen) }}</span>
              </div>
              <div class="device-actions">
                <button class="action-btn sync">Синхронизировать</button>
                <button class="action-btn remove">Удалить</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Статистика -->
        <div class="profile-card stats-card">
          <div class="card-header">
            <h3>Статистика за неделю</h3>
          </div>
          <div class="weekly-stats">
            <div v-for="day in weeklyStats" :key="day.day" class="day-stat">
              <span class="day-name">{{ day.day }}</span>
              <div class="day-bar">
                <div 
                  class="bar-fill" 
                  :style="{ height: day.percentage + '%' }"
                  :class="getBarColor(day.percentage)"
                ></div>
              </div>
              <span class="day-hours">{{ day.hours }}ч</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const devices = ref([
  { 
    id: 1, 
    name: 'Рабочий ПК', 
    type: 'windows', 
    osVersion: 'Windows 11 Pro', 
    lastSeen: new Date(), 
    isActive: true 
  },
  { 
    id: 2, 
    name: 'MacBook Pro', 
    type: 'mac', 
    osVersion: 'macOS 14.2', 
    lastSeen: new Date(Date.now() - 3600000), 
    isActive: false 
  },
  { 
    id: 3, 
    name: 'Samsung Galaxy', 
    type: 'android', 
    osVersion: 'Android 14', 
    lastSeen: new Date(), 
    isActive: true 
  },
  { 
    id: 4, 
    name: 'Домашний ПК', 
    type: 'linux', 
    osVersion: 'Ubuntu 22.04', 
    lastSeen: new Date(Date.now() - 86400000), 
    isActive: false 
  }
])

const weeklyStats = ref([
  { day: 'Пн', hours: 8.5, percentage: 85 },
  { day: 'Вт', hours: 7.2, percentage: 72 },
  { day: 'Ср', hours: 9.1, percentage: 91 },
  { day: 'Чт', hours: 6.8, percentage: 68 },
  { day: 'Пт', hours: 7.9, percentage: 79 },
  { day: 'Сб', hours: 3.2, percentage: 32 },
  { day: 'Вс', hours: 2.1, percentage: 21 }
])

onMounted(() => {
  console.log('Profile page loaded')
})

const getDeviceTypeClass = (type) => {
  const classes = {
    windows: 'windows',
    mac: 'mac',
    android: 'android',
    linux: 'linux',
    ios: 'ios'
  }
  return classes[type] || 'default'
}

const getDeviceTypeName = (type) => {
  const names = {
    windows: 'Windows',
    mac: 'macOS',
    android: 'Android',
    linux: 'Linux',
    ios: 'iOS'
  }
  return names[type] || type
}

const formatLastSeen = (date) => {
  const now = new Date()
  const diff = now - new Date(date)
  const hours = Math.floor(diff / 3600000)
  
  if (hours < 1) return 'Только что'
  if (hours < 24) return `${hours}ч назад`
  return `${Math.floor(hours / 24)}д назад`
}

const getBarColor = (percentage) => {
  if (percentage > 80) return 'high'
  if (percentage > 50) return 'medium'
  return 'low'
}
</script>

<style scoped>
.profile-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: white;
}

/* Навигация */
.navbar {
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: white;
  font-weight: 600;
  font-size: 18px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.3s ease;
  padding: 8px 12px;
  border-radius: 8px;
}

.nav-link:hover {
  color: white;
  background: rgba(255, 255, 255, 0.05);
}

.nav-link svg {
  width: 18px;
  height: 18px;
}

.logout {
  color: var(--danger-color);
}

.logout:hover {
  background: rgba(239, 68, 68, 0.1);
}

/* Контент профиля */
.profile-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.profile-header {
  margin-bottom: 40px;
}

.profile-header h1 {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 8px;
  background: linear-gradient(135deg, white, var(--text-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: var(--text-muted);
  font-size: 16px;
}

.profile-content {
  display: grid;
  gap: 24px;
}

.profile-card {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
}

.user-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.user-info {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.avatar {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 600;
}

.avatar-text {
  color: white;
}

.user-details h2 {
  font-size: 24px;
  margin-bottom: 4px;
}

.email {
  color: var(--text-muted);
  margin-bottom: 16px;
}

.user-stats {
  display: flex;
  gap: 32px;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
}

.edit-btn {
  padding: 10px 24px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--primary-color);
  border-radius: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.edit-btn:hover {
  background: var(--primary-color);
  color: white;
}

/* Устройства */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.card-header h3 {
  font-size: 20px;
  font-weight: 600;
}

.badge {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.devices-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.device-item {
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  gap: 20px;
  align-items: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.device-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--primary-color);
}

.device-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.device-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.device-icon.windows {
  background: linear-gradient(135deg, #0078d7, #00bcf2);
}

.device-icon.mac {
  background: linear-gradient(135deg, #999999, #666666);
}

.device-icon.android {
  background: linear-gradient(135deg, #3ddc84, #0f9d58);
}

.device-icon.linux {
  background: linear-gradient(135deg, #f1502f, #dd4814);
}

.device-icon.ios {
  background: linear-gradient(135deg, #999999, #333333);
}

.device-info h4 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.device-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.device-type {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.device-version {
  color: var(--text-muted);
}

.device-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}

.status-indicator.online {
  background: var(--success-color);
  animation: pulse 2s infinite;
}

.status-text {
  font-size: 12px;
  color: var(--text-muted);
}

.last-seen {
  font-size: 11px;
  color: var(--text-muted);
}

.device-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.device-item:hover .device-actions {
  opacity: 1;
}

.action-btn {
  padding: 6px 12px;
  font-size: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn.sync {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
}

.action-btn.sync:hover {
  background: var(--primary-color);
  color: white;
}

.action-btn.remove {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
}

.action-btn.remove:hover {
  background: var(--danger-color);
  color: white;
}

/* Статистика за неделю */
.weekly-stats {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 200px;
  padding: 20px 0;
}

.day-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.day-name {
  font-size: 12px;
  color: var(--text-muted);
}

.day-bar {
  width: 40px;
  height: 150px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.bar-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  border-radius: 8px;
  transition: height 0.3s ease;
}

.bar-fill.high {
  background: linear-gradient(to top, var(--primary-color), var(--primary-dark));
}

.bar-fill.medium {
  background: linear-gradient(to top, #8b5cf6, #6366f1);
}

.bar-fill.low {
  background: linear-gradient(to top, #a855f7, #8b5cf6);
}

.day-hours {
  font-size: 12px;
  font-weight: 500;
}

/* Анимации */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-fade-in {
  animation: fadeIn 0.6s ease-out;
}

/* Переменные */
:root {
  --primary-color: #6366f1;
  --primary-dark: #4f46e5;
  --secondary-color: #10b981;
  --background-dark: #0f172a;
  --surface-dark: #1e293b;
  --text-primary: #ffffff;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --border-color: #475569;
  --success-color: #22c55e;
  --warning-color: #f59e0b;
  --danger-color: #ef4444;
}
</style>