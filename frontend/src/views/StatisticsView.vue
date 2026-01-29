<template>
  <div class="statistics-view">
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
          <router-link to="/profile" class="nav-link">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
            </svg>
            Профиль
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

    <div class="statistics-container animate-fade-in">
      <!-- Заголовок и фильтры -->
      <div class="stats-header">
        <div class="header-left">
          <h1>Статистика</h1>
          <p class="subtitle">Анализ вашей продуктивности</p>
        </div>
        <div class="header-right">
          <div class="period-selector">
            <select v-model="selectedPeriod" class="period-select">
              <option value="week">Эта неделя</option>
              <option value="month">Этот месяц</option>
              <option value="quarter">Этот квартал</option>
              <option value="year">Этот год</option>
            </select>
          </div>
          <button class="export-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            Экспорт
          </button>
        </div>
      </div>

      <!-- Быстрые фильтры -->
      <div class="quick-filters">
        <button 
          v-for="filter in filters" 
          :key="filter.id"
          @click="applyFilter(filter.id)"
          :class="['filter-btn', { 'active': activeFilter === filter.id }]"
        >
          {{ filter.label }}
        </button>
      </div>

      <!-- Карточки статистики -->
      <div class="stats-cards">
        <div v-for="card in statsCards" :key="card.id" class="stat-card">
          <div class="card-top">
            <div>
              <span class="card-label">{{ card.label }}</span>
              <h3 class="card-value">{{ card.value }}</h3>
            </div>
            <div class="card-icon" :class="card.color">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path :d="card.icon" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/>
              </svg>
            </div>
          </div>
          <div class="card-trend" :class="{ 'positive': card.trend > 0, 'negative': card.trend < 0 }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path v-if="card.trend > 0" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>
            </svg>
            <span>{{ Math.abs(card.trend) }}% за неделю</span>
          </div>
        </div>
      </div>

      <!-- Графики -->
      <div class="charts-grid">
        <div class="chart-container">
          <div class="chart-header">
            <h3>Активность по дням</h3>
            <span class="chart-unit">часы</span>
          </div>
          <div class="daily-chart">
            <div 
              v-for="(day, index) in dailyData" 
              :key="index"
              class="chart-day"
              @mouseenter="showDayTooltip(day)"
            >
              <div class="day-label">{{ day.label }}</div>
              <div class="day-bar-container">
                <div 
                  class="day-bar" 
                  :style="{ height: day.value + '%' }"
                  :class="getBarHeightClass(day.value)"
                ></div>
              </div>
              <div class="day-value">{{ day.hours }}ч</div>
            </div>
          </div>
        </div>

        <div class="chart-container">
          <div class="chart-header">
            <h3>Распределение по устройствам</h3>
            <span class="chart-unit">%</span>
          </div>
          <div class="device-distribution">
            <div v-for="device in deviceData" :key="device.id" class="device-item">
              <div class="device-row">
                <div class="device-info">
                  <div class="device-color" :style="{ background: device.color }"></div>
                  <span class="device-name">{{ device.name }}</span>
                </div>
                <div class="device-percentage">{{ device.percentage }}%</div>
              </div>
              <div class="device-progress">
                <div 
                  class="progress-bar" 
                  :style="{ width: device.percentage + '%', background: device.color }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Топ приложений -->
      <div class="top-apps">
        <div class="top-apps-header">
          <h3>Топ приложений</h3>
          <button class="view-all">Посмотреть все →</button>
        </div>
        <div class="apps-list">
          <div v-for="app in topApps" :key="app.id" class="app-item">
            <div class="app-left">
              <div class="app-icon" :class="app.category">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path v-if="app.category === 'development'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
                  <path v-else-if="app.category === 'browser'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
                  <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
              </div>
              <div class="app-info">
                <h4>{{ app.name }}</h4>
                <span class="app-category">{{ getCategoryName(app.category) }}</span>
              </div>
            </div>
            <div class="app-right">
              <div class="app-time">{{ app.time }}</div>
              <div class="app-progress">
                <div class="progress-bar" :style="{ width: app.percentage + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>


    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'

const selectedPeriod = ref('week')
const activeFilter = ref('all')
const loading = ref({
  overview: true,
  chart: true,
  devices: true,
  apps: true
})

const statsCards = ref([])
const dailyData = ref([])
const deviceData = ref([])
const topApps = ref([])

const filters = ref([
  { id: 'all', label: 'Все устройства' },
  { id: 'pc', label: 'Только ПК' },
  { id: 'mobile', label: 'Только мобильные' },
  { id: 'productive', label: 'Продуктивность' },
  { id: 'entertainment', label: 'Развлечения' }
])

// Простой API клиент с отправкой кук
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true // Это всё что нужно! Куки отправятся автоматически
})

// Загрузка всех данных
const loadAllData = async () => {
  try {
    loading.value = { overview: true, chart: true, devices: true, apps: true }
    
    // Загружаем полную сводку
    const summaryResponse = await apiClient.get(`/api/statistics/summary?period=${selectedPeriod.value}`)
    
    if (summaryResponse.data.success) {
      const data = summaryResponse.data
      
      // Обновляем карточки
      statsCards.value = [
        { 
          id: 'total', 
          label: 'Общее время', 
          value: data.overview.total_time, 
          trend: 0, 
          color: 'blue',
          icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
        },
        { 
          id: 'average', 
          label: 'Среднее в день', 
          value: data.overview.average_daily, 
          trend: 0, 
          color: 'purple',
          icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
        },
        { 
          id: 'productive', 
          label: 'Продуктивное время', 
          value: data.overview.productive_time, 
          trend: Math.round(data.overview.productive_percentage), 
          color: 'green',
          icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z'
        },
        { 
          id: 'devices', 
          label: 'Активных устройств', 
          value: data.overview.active_devices.toString(), 
          trend: 0, 
          color: 'orange',
          icon: 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z'
        }
      ]
      
      // Обновляем график
      dailyData.value = data.chart_data.map(day => ({
        label: day.label,
        hours: day.hours,
        value: day.value,
        date: day.date
      }))
      
      // Обновляем распределение по устройствам
      deviceData.value = data.platform_distribution.map((platform, index) => ({
        id: index + 1,
        name: platform.platform.toUpperCase(),
        percentage: platform.percentage,
        color: platform.color,
        hours: platform.hours
      }))
      
      // Обновляем топ приложений
      topApps.value = data.top_apps.map(app => ({
        id: app.id,
        name: app.name,
        category: app.category,
        time: app.time,
        percentage: app.percentage,
        original_name: app.original_name,
        platforms: app.platforms
      }))
    }
    
  } catch (error) {
    console.error('Error loading statistics:', error)
    
    // Если ошибка авторизации (401), редирект на страницу логина
    if (error.response?.status === 401) {
      window.location.href = '/auth'
      return
    }
    
    // Fallback на демо данные
    loadFallbackData()
  } finally {
    Object.keys(loading.value).forEach(key => {
      loading.value[key] = false
    })
  }
}

// Fallback данные (если API недоступно)
const loadFallbackData = () => {
  statsCards.value = [
    { 
      id: 'total', 
      label: 'Общее время', 
      value: '142ч 30м', 
      trend: 12, 
      color: 'blue',
      icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
    },
    { 
      id: 'average', 
      label: 'Среднее в день', 
      value: '8ч 12м', 
      trend: 5, 
      color: 'purple',
      icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
    },
    { 
      id: 'productive', 
      label: 'Продуктивное время', 
      value: '86ч 15м', 
      trend: 8, 
      color: 'green',
      icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z'
    },
    { 
      id: 'devices', 
      label: 'Активных устройств', 
      value: '3', 
      trend: 0, 
      color: 'orange',
      icon: 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z'
    }
  ]
  
  dailyData.value = [
    { label: 'Пн', hours: 8.5, value: 85 },
    { label: 'Вт', hours: 7.2, value: 72 },
    { label: 'Ср', hours: 9.1, value: 91 },
    { label: 'Чт', hours: 6.8, value: 68 },
    { label: 'Пт', hours: 7.9, value: 79 },
    { label: 'Сб', hours: 3.2, value: 32 },
    { label: 'Вс', hours: 2.1, value: 21 }
  ]
  
  deviceData.value = [
    { id: 1, name: 'Windows', percentage: 58, color: '#3b82f6' },
    { id: 2, name: 'macOS', percentage: 25, color: '#64748b' },
    { id: 3, name: 'Android', percentage: 12, color: '#22c55e' },
    { id: 4, name: 'iOS', percentage: 5, color: '#94a3b8' }
  ]
  
  topApps.value = [
    { id: 1, name: 'Visual Studio Code', category: 'development', time: '42ч 15м', percentage: 32 },
    { id: 2, name: 'Google Chrome', category: 'browser', time: '38ч 30м', percentage: 29 },
    { id: 3, name: 'Slack', category: 'communication', time: '18ч 45м', percentage: 14 },
    { id: 4, name: 'Figma', category: 'design', time: '12ч 20м', percentage: 9 },
    { id: 5, name: 'Spotify', category: 'music', time: '8ч 15м', percentage: 6 }
  ]
}

onMounted(() => {
  loadAllData()
})

watch(selectedPeriod, () => {
  loadAllData()
})

const applyFilter = (filterId) => {
  activeFilter.value = filterId
  console.log('Applied filter:', filterId)
}

const getBarHeightClass = (value) => {
  if (value > 80) return 'high'
  if (value > 50) return 'medium'
  return 'low'
}

const getCategoryName = (category) => {
  const names = {
    development: 'Разработка',
    browser: 'Браузер',
    communication: 'Общение',
    social: 'Соцсети',
    entertainment: 'Развлечения',
    productivity: 'Продуктивность',
    design: 'Дизайн',
    music: 'Музыка',
    other: 'Другое'
  }
  return names[category] || category
}

const showDayTooltip = (day) => {
  console.log(`${day.label}: ${day.hours} часов, дата: ${day.date}`)
}

const exportData = async () => {
  try {
    const response = await apiClient.get(`/api/statistics/detailed-daily?period=${selectedPeriod.value}`, {
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `statistics-${selectedPeriod.value}-${new Date().toISOString().split('T')[0]}.json`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    
  } catch (error) {
    console.error('Error exporting data:', error)
    alert('Ошибка при экспорте данных')
  }
}
</script>

<style scoped>
.statistics-view {
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
  max-width: 1400px;
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

/* Основной контейнер */
.statistics-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* Заголовок и фильтры */
.stats-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.header-left h1 {
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

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.period-select {
  padding: 10px 16px;
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: white;
  font-size: 14px;
  min-width: 180px;
  cursor: pointer;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.export-btn:hover {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.export-btn svg {
  width: 16px;
  height: 16px;
}

/* Быстрые фильтры */
.quick-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 8px 20px;
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-btn:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: var(--primary-color);
  color: white;
}

.filter-btn.active {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  border-color: transparent;
  color: white;
}

/* Карточки статистики */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.stat-card {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
  border-color: var(--primary-color);
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-label {
  display: block;
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.card-value {
  font-size: 32px;
  font-weight: 700;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-icon.blue {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(99, 102, 241, 0.2));
}

.card-icon.purple {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.2));
}

.card-icon.green {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2));
}

.card-icon.orange {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.2), rgba(245, 158, 11, 0.2));
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.card-trend {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.card-trend.positive {
  color: var(--success-color);
}

.card-trend.negative {
  color: var(--danger-color);
}

.card-trend svg {
  width: 16px;
  height: 16px;
}

/* Графики */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
  gap: 32px;
  margin-bottom: 40px;
}

.chart-container {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.chart-header h3 {
  font-size: 18px;
  font-weight: 600;
}

.chart-unit {
  font-size: 12px;
  color: var(--text-muted);
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
}

/* График по дням */
.daily-chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 200px;
  padding: 20px 0;
}

.chart-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  flex: 1;
  cursor: pointer;
}

.day-label {
  font-size: 12px;
  color: var(--text-muted);
}

.day-bar-container {
  width: 40px;
  height: 150px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.day-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  border-radius: 8px;
  transition: height 0.3s ease;
}

.day-bar.high {
  background: linear-gradient(to top, var(--primary-color), var(--primary-dark));
}

.day-bar.medium {
  background: linear-gradient(to top, #8b5cf6, #6366f1);
}

.day-bar.low {
  background: linear-gradient(to top, #a855f7, #8b5cf6);
}

.day-value {
  font-size: 12px;
  font-weight: 500;
}

/* Распределение по устройствам */
.device-distribution {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.device-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.device-name {
  font-size: 14px;
}

.device-percentage {
  font-size: 14px;
  font-weight: 500;
}

.device-progress {
  height: 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

/* Топ приложений */
.top-apps {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 40px;
}

.top-apps-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.top-apps-header h3 {
  font-size: 18px;
  font-weight: 600;
}

.view-all {
  background: none;
  border: none;
  color: var(--primary-color);
  font-size: 14px;
  cursor: pointer;
  padding: 8px 0;
}

.apps-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.app-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.app-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.app-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.app-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-icon.development {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(99, 102, 241, 0.2));
}

.app-icon.browser {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.2));
}

.app-icon.communication {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.2));
}

.app-icon.design {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(219, 39, 119, 0.2));
}

.app-icon.music {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2));
}

.app-icon svg {
  width: 20px;
  height: 20px;
  color: white;
}

.app-info h4 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.app-category {
  font-size: 12px;
  color: var(--text-muted);
}

.app-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.app-time {
  font-size: 16px;
  font-weight: 500;
  min-width: 80px;
  text-align: right;
}

.app-progress {
  width: 200px;
  height: 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
  overflow: hidden;
}

.app-progress .progress-bar {
  background: linear-gradient(90deg, var(--primary-color), var(--primary-dark));
}

/* Тепловая карта */
.heatmap-container {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
}

.heatmap-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.heatmap-header h3 {
  font-size: 18px;
  font-weight: 600;
}

.heatmap-legend {
  display: flex;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.legend-color.low {
  background: rgba(99, 102, 241, 0.2);
}

.legend-color.medium {
  background: rgba(99, 102, 241, 0.4);
}

.legend-color.high {
  background: rgba(99, 102, 241, 0.8);
}

.heatmap {
  overflow-x: auto;
}

.heatmap-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: 1fr auto;
  gap: 12px;
  min-width: 800px;
}

.time-labels {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-right: 12px;
}

.time-label {
  font-size: 12px;
  color: var(--text-muted);
  height: 24px;
  display: flex;
  align-items: center;
}

.day-labels {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  padding-top: 12px;
}

.day-label {
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  padding: 8px 0;
}

.heatmap-cells {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(8, 1fr);
  gap: 4px;
}

.heatmap-cell {
  width: 100%;
  height: 24px;
  border-radius: 4px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.heatmap-cell.none {
  background: rgba(255, 255, 255, 0.05);
}

.heatmap-cell.low {
  background: rgba(99, 102, 241, 0.2);
}

.heatmap-cell.medium {
  background: rgba(99, 102, 241, 0.4);
}

.heatmap-cell.high {
  background: rgba(99, 102, 241, 0.8);
}

.heatmap-cell.very-high {
  background: var(--primary-color);
}

.heatmap-cell:hover {
  transform: scale(1.1);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
}

/* Анимации */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
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

/* Адаптивность */
@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .stats-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-right {
    flex-direction: column;
    width: 100%;
  }
  
  .period-select,
  .export-btn {
    width: 100%;
  }
}
</style>