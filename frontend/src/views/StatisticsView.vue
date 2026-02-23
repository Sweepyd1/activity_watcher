<template>
  <div class="statistics-view">
    <!-- Навигация (без изменений) -->
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
      <!-- Заголовок и фильтры (добавлен выбор формата экспорта) -->
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
          <div class="export-dropdown">
            <button class="export-btn" @click="toggleExportMenu">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              Экспорт
            </button>
            <div v-if="showExportMenu" class="export-menu">
              <button @click="exportData('json')">JSON</button>
              <button @click="exportData('csv')">CSV</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Быстрые фильтры (без изменений) -->
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

      <!-- Карточки статистики (с реальными трендами) -->
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

      <!-- Графики: активность по дням + устройства -->
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
              @click="showDayDetail(day)"
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

      <!-- Тепловая карта активности (новая секция) -->
      <div class="heatmap-container" v-if="heatmapData.length">
        <div class="heatmap-header">
          <h3>Тепловая карта активности</h3>
          <div class="heatmap-legend">
            <span class="legend-item"><span class="legend-color low"></span> Мало</span>
            <span class="legend-item"><span class="legend-color medium"></span> Средне</span>
            <span class="legend-item"><span class="legend-color high"></span> Много</span>
            <span class="legend-item"><span class="legend-color very-high"></span> Очень много</span>
          </div>
        </div>
        <div class="heatmap">
          <div class="heatmap-grid">
            <!-- Заголовки дней (по вертикали слева) -->
            <div class="time-labels">
              <div v-for="hour in 24" :key="hour" class="time-label">{{ hour-1 }}:00</div>
            </div>
            <!-- Сама сетка -->
            <div class="heatmap-cells-wrapper">
              <div class="day-labels">
                <div v-for="day in dayNames" :key="day">{{ day }}</div>
              </div>
              <div class="heatmap-rows">
                <div v-for="(row, dayIdx) in heatmapData" :key="dayIdx" class="heatmap-row">
                  <div
                    v-for="(value, hourIdx) in row"
                    :key="hourIdx"
                    class="heatmap-cell"
                    :class="getHeatClass(value)"
                    :title="`${dayNames[dayIdx]} ${hourIdx}:00 – ${Math.round(value)} мин`"
                    @click="showHourDetail(dayIdx, hourIdx, value)"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Распределение по категориям (новая секция) -->
      <div class="categories-container" v-if="categoriesData.length">
        <h3>Распределение по категориям</h3>
        <div class="categories-list">
          <div v-for="cat in categoriesData" :key="cat.category" class="category-item">
            <span class="category-name">{{ getCategoryName(cat.category) }}</span>
            <div class="category-bar">
              <div class="progress-bar" :style="{ width: cat.percentage + '%' }"></div>
            </div>
            <span class="category-percent">{{ cat.percentage }}%</span>
            <span class="category-time">{{ formatTime(cat.minutes) }}</span>
          </div>
        </div>
      </div>

      <!-- Топ приложений (без изменений) -->
      <div class="top-apps">
        <div class="top-apps-header">
          <h3>Топ приложений</h3>
          <button class="view-all" @click="viewAllApps">Посмотреть все →</button>
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

      <!-- Модальное окно детализации дня -->
      <Teleport to="body">
        <div v-if="showDayModal" class="modal-overlay" @click.self="closeModal">
          <div class="modal-content">
            <div class="modal-header">
              <h3>Детали за {{ selectedDayLabel }}</h3>
              <button class="close-btn" @click="closeModal">×</button>
            </div>
            <div class="modal-body">
              <div v-if="loading.dayBreakdown" class="loading-spinner">Загрузка...</div>
              <div v-else-if="dayActivities.length === 0" class="no-data">Нет данных за этот день</div>
              <div v-else class="activities-list">
                <div v-for="act in dayActivities" :key="act.id" class="activity-item">
                  <div class="activity-icon" :class="act.category">
                    <!-- иконка категории -->
                  </div>
                  <div class="activity-info">
                    <div class="activity-name">{{ act.app_name }}</div>
                    <div class="activity-time">{{ formatTime(act.duration) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'

// Состояние
const selectedPeriod = ref('week')
const activeFilter = ref('all')
const showExportMenu = ref(false)
const showDayModal = ref(false)
const selectedDayLabel = ref('')
const dayActivities = ref([])
const loading = ref({
  overview: true,
  chart: true,
  devices: true,
  apps: true,
  heatmap: true,
  categories: true,
  dayBreakdown: false
})

// Данные
const statsCards = ref([])
const dailyData = ref([])
const deviceData = ref([])
const topApps = ref([])
const heatmapData = ref([])
const categoriesData = ref([])
const trendsData = ref({})

// Константы
const filters = ref([
  { id: 'all', label: 'Все устройства' },
  { id: 'pc', label: 'Только ПК' },
  { id: 'mobile', label: 'Только мобильные' },
  { id: 'productive', label: 'Продуктивность' },
  { id: 'entertainment', label: 'Развлечения' }
])

const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

// API клиент
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true
})

// Загрузка всех данных
const loadAllData = async () => {
  try {
    Object.keys(loading.value).forEach(key => {
      if (key !== 'dayBreakdown') loading.value[key] = true
    })

    const params = { period: selectedPeriod.value }
    if (activeFilter.value !== 'all') params.filter = activeFilter.value

    const response = await apiClient.get('/api/statistics/summary', { params })

    if (response.data.success) {
      const data = response.data

      // Карточки с трендами
      trendsData.value = data.trends || {}
      statsCards.value = [
        {
          id: 'total',
          label: 'Общее время',
          value: data.overview.total_time,
          trend: trendsData.value.total_time?.change || 0,
          color: 'blue',
          icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
        },
        {
          id: 'average',
          label: 'Среднее в день',
          value: data.overview.average_daily,
          trend: trendsData.value.average_daily?.change || 0,
          color: 'purple',
          icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
        },
        {
          id: 'productive',
          label: 'Продуктивное время',
          value: data.overview.productive_time,
          trend: trendsData.value.productive_time?.change || 0,
          color: 'green',
          icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z'
        },
        {
          id: 'devices',
          label: 'Активных устройств',
          value: data.overview.active_devices.toString(),
          trend: trendsData.value.active_devices?.change || 0,
          color: 'orange',
          icon: 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z'
        }
      ]

      // График по дням
      dailyData.value = data.chart_data.map(day => ({
        label: day.label,
        hours: day.hours,
        value: day.value,
        date: day.date
      }))

      // Устройства
      deviceData.value = data.platform_distribution.map((platform, index) => ({
        id: index + 1,
        name: platform.platform.toUpperCase(),
        percentage: platform.percentage,
        color: platform.color,
        hours: platform.hours
      }))

      // Топ приложений
      topApps.value = data.top_apps.map(app => ({
        id: app.id,
        name: app.name,
        category: app.category,
        time: app.time,
        percentage: app.percentage,
        original_name: app.original_name,
        platforms: app.platforms
      }))

      // Новые данные
      heatmapData.value = data.heatmap || []
      categoriesData.value = data.categories || []
    }
  } catch (error) {
    console.error('Error loading statistics:', error)
    if (error.response?.status === 401) window.location.href = '/auth'
    else loadFallbackData()
  } finally {
    Object.keys(loading.value).forEach(key => {
      if (key !== 'dayBreakdown') loading.value[key] = false
    })
  }
}

// Fallback данные (дополнены новыми полями)
const loadFallbackData = () => {
  statsCards.value = [ /* ... как в исходном коде ... */ ]
  dailyData.value = [ /* ... как в исходном ... */ ]
  deviceData.value = [ /* ... */ ]
  topApps.value = [ /* ... */ ]
  
  // Демо данные для новых секций
  heatmapData.value = Array(7).fill().map(() => 
    Array(24).fill().map(() => Math.floor(Math.random() * 180))
  )
  categoriesData.value = [
    { category: 'development', minutes: 2540, percentage: 42 },
    { category: 'browser', minutes: 1320, percentage: 22 },
    { category: 'communication', minutes: 840, percentage: 14 },
    { category: 'entertainment', minutes: 720, percentage: 12 },
    { category: 'other', minutes: 600, percentage: 10 }
  ]
}

// Вспомогательные функции
const getBarHeightClass = (value) => {
  if (value > 80) return 'high'
  if (value > 50) return 'medium'
  return 'low'
}

const getHeatClass = (minutes) => {
  if (minutes === 0) return 'none'
  if (minutes < 30) return 'low'
  if (minutes < 60) return 'medium'
  if (minutes < 120) return 'high'
  return 'very-high'
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

const formatTime = (minutes) => {
  const h = Math.floor(minutes / 60)
  const m = Math.floor(minutes % 60)
  return h > 0 ? `${h}ч ${m}м` : `${m}м`
}

// Применить фильтр
const applyFilter = (filterId) => {
  activeFilter.value = filterId
  loadAllData()
}

// Экспорт
const toggleExportMenu = () => {
  showExportMenu.value = !showExportMenu.value
}

const exportData = async (format) => {
  showExportMenu.value = false
  try {
    const response = await apiClient.get(`/api/statistics/detailed-daily?period=${selectedPeriod.value}`, {
      responseType: 'blob'
    })
    
    let blob, filename
    if (format === 'json') {
      blob = new Blob([response.data], { type: 'application/json' })
      filename = `statistics-${selectedPeriod.value}-${new Date().toISOString().split('T')[0]}.json`
    } else {
      // Предполагаем, что бэкенд может вернуть CSV по тому же URL (нужен отдельный эндпоинт)
      // Пока заглушка
      alert('CSV экспорт пока не реализован')
      return
    }
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.error('Error exporting data:', error)
    alert('Ошибка при экспорте')
  }
}

// Детализация дня
const showDayDetail = async (day) => {
  selectedDayLabel.value = day.label
  showDayModal.value = true
  loading.value.dayBreakdown = true
  try {
    const response = await apiClient.get(`/api/statistics/daily-breakdown/${day.date}`)
    dayActivities.value = response.data.activities || []
  } catch (error) {
    console.error('Error loading day details:', error)
    dayActivities.value = []
  } finally {
    loading.value.dayBreakdown = false
  }
}

const showHourDetail = (dayIdx, hourIdx, minutes) => {
  if (minutes === 0) return
  alert(`Активность ${dayNames[dayIdx]} ${hourIdx}:00 – ${formatTime(minutes)}`)
  // Здесь можно открыть модалку с активностями за этот час, если нужно
}

const closeModal = () => {
  showDayModal.value = false
  dayActivities.value = []
}

const viewAllApps = () => {
  // Переход на отдельную страницу со всеми приложениями
  // router.push('/apps')
}

// Загрузка при монтировании и изменении периода
onMounted(loadAllData)
watch(selectedPeriod, loadAllData)
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

.export-dropdown {
  position: relative;
}

.export-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-top: 4px;
  overflow: hidden;
  z-index: 10;
}

.export-menu button {
  display: block;
  width: 100%;
  padding: 8px 16px;
  background: none;
  border: none;
  color: var(--text-secondary);
  text-align: left;
  cursor: pointer;
  transition: background 0.2s;
}

.export-menu button:hover {
  background: rgba(255,255,255,0.05);
  color: white;
}

/* Тепловая карта */
.heatmap-container {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 40px;
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

.legend-color.low { background: rgba(99, 102, 241, 0.2); }
.legend-color.medium { background: rgba(99, 102, 241, 0.4); }
.legend-color.high { background: rgba(99, 102, 241, 0.6); }
.legend-color.very-high { background: var(--primary-color); }

.heatmap {
  overflow-x: auto;
}

.heatmap-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
}

.time-labels {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 24px; /* чтобы совпадало с началом строк */
}

.time-label {
  font-size: 10px;
  color: var(--text-muted);
  height: 20px;
  line-height: 20px;
  text-align: right;
  padding-right: 8px;
}

.heatmap-cells-wrapper {
  flex: 1;
}

.day-labels {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 8px;
}

.day-labels div {
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}

.heatmap-rows {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.heatmap-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.heatmap-cell {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 4px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.heatmap-cell.none { background: rgba(255,255,255,0.05); }
.heatmap-cell.low { background: rgba(99, 102, 241, 0.2); }
.heatmap-cell.medium { background: rgba(99, 102, 241, 0.4); }
.heatmap-cell.high { background: rgba(99, 102, 241, 0.6); }
.heatmap-cell.very-high { background: var(--primary-color); }

.heatmap-cell:hover {
  transform: scale(1.1);
  box-shadow: 0 0 0 2px rgba(99,102,241,0.5);
  z-index: 2;
}

/* Категории */
.categories-container {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 40px;
}

.categories-container h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-item {
  display: grid;
  grid-template-columns: 150px 1fr 80px 80px;
  align-items: center;
  gap: 16px;
}

.category-name {
  font-size: 14px;
  color: var(--text-secondary);
}

.category-bar {
  height: 8px;
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
  overflow: hidden;
}

.category-bar .progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-dark));
  border-radius: 4px;
}

.category-percent {
  font-size: 14px;
  font-weight: 500;
  color: white;
  text-align: right;
}

.category-time {
  font-size: 12px;
  color: var(--text-muted);
  text-align: right;
}

/* Модальное окно */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0,0,0,0.4);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 24px;
  cursor: pointer;
  padding: 0 8px;
}

.close-btn:hover {
  color: white;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(80vh - 80px);
}

.loading-spinner {
  text-align: center;
  color: var(--text-muted);
  padding: 40px 0;
}

.no-data {
  text-align: center;
  color: var(--text-muted);
  padding: 40px 0;
}

.activities-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(99,102,241,0.2);
}

.activity-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-name {
  font-size: 14px;
  font-weight: 500;
}

.activity-time {
  font-size: 14px;
  color: var(--text-muted);
}

/* Адаптивность для новых блоков */
@media (max-width: 768px) {
  .category-item {
    grid-template-columns: 120px 1fr 60px 60px;
    gap: 8px;
  }
  
  .heatmap-legend {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>