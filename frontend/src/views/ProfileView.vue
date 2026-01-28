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
          <button @click="handleLogout" class="nav-link logout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
            Выйти
          </button>
        </div>
      </div>
    </nav>

    <div class="profile-container animate-fade-in">
      <!-- Заголовок -->
      <div class="profile-header">
        <h1>Профиль</h1>
        <p class="subtitle">Управление аккаунтом и устройствами</p>
      </div>

      <div v-if="loading" class="loading-spinner">
        <div class="spinner"></div>
        <p>Загрузка данных...</p>
      </div>

      <div v-else-if="error" class="error-message">
        <p>{{ error }}</p>
        <button @click="fetchUserData" class="retry-btn">Повторить</button>
      </div>

      <div v-else class="profile-content">
        <!-- Карточка пользователя -->
        <div class="profile-card user-card" v-if="userData">
          <div class="user-info">
            <div class="avatar">
              <span class="avatar-text">{{ getInitials(userData.username || userData.email) }}</span>
            </div>
            <div class="user-details">
              <h2>{{ userData.username || userData.email }}</h2>
              <p class="email">{{ userData.email }}</p>
              <div class="user-stats">
                <div class="stat">
                  <span class="stat-label">На платформе с</span>
                  <span class="stat-value">{{ formatDate(userData.created_at) }}</span>
                </div>
                <div class="stat">
                  <span class="stat-label">Устройств</span>
                  <span class="stat-value">{{ userData.devices_count || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
          <button class="edit-btn" @click="editProfile">Редактировать</button>
        </div>

        <!-- Устройства -->
        <div class="profile-card devices-card">
          <div class="card-header">
            <div class="header-left">
              <h3>Активные устройства</h3>
              <span class="badge">{{ devices.length }} устройств</span>
            </div>
            <button class="add-device-btn" @click="showAddDeviceModal = true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
              </svg>
              Добавить устройство
            </button>
          </div>

          <div v-if="devices.length === 0" class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
            <p>У вас пока нет устройств</p>
            <button class="empty-state-btn" @click="showAddDeviceModal = true">Добавить первое устройство</button>
          </div>

          <div v-else class="devices-list">
            <div 
              v-for="device in devices" 
              :key="device.id"
              class="device-item"
              :class="{ 
                'active': device.is_active,
                'pending': !device.device_id
              }"
            >
              <div class="device-icon" :class="getDeviceTypeClass(device.platform)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path v-if="device.platform === 'windows'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                  <path v-else-if="device.platform === 'mac' || device.platform === 'macos'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                  <path v-else-if="device.platform === 'android'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                  <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                </svg>
              </div>
              <div class="device-info">
                <div class="device-header">
                  <h4>{{ device.device_name }}</h4>
                  <span v-if="!device.device_id" class="status-badge pending">Ожидает регистрации</span>
                  <span v-else-if="device.is_active" class="status-badge active">В сети</span>
                  <span v-else class="status-badge inactive">Не в сети</span>
                </div>
                <div class="device-meta">
                  <span class="device-type">{{ getDeviceTypeName(device.platform) }}</span>
                  <span v-if="device.platform_version" class="device-version">{{ device.platform_version }}</span>
                  <span v-if="device.client_version" class="client-version">v{{ device.client_version }}</span>
                </div>
                <div v-if="device.last_seen" class="last-seen-info">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  <span>Последняя активность: {{ formatLastSeen(device.last_seen) }}</span>
                </div>
                <div v-if="!device.device_id" class="registration-info">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                  </svg>
                  <span>Для подключения создайте токен</span>
                </div>
              </div>
              <div class="device-actions">
  <button 
    class="action-btn token" 
    @click="openTokenModal(device)"
    :disabled="creatingToken"
  >
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
    </svg>
    {{ device.tokens?.length > 0 ? 'Управление токенами' : 'Создать токен' }}
  </button>
  
  <button 
    class="action-btn sync" 
    @click="syncDevice(device.id)" 
    :disabled="!device.device_id || device.device_id.startsWith('pending_')"
  >
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
    </svg>
    Синхронизировать
  </button>
  
  <button class="action-btn remove" @click="removeDevice(device.id)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
    </svg>
    Удалить
  </button>
</div>
            </div>
          </div>
        </div>

        <!-- Статистика -->
        <div class="profile-card stats-card">
          <div class="card-header">
            <h3>Статистика за неделю</h3>
            <button class="refresh-btn" @click="fetchWeeklyStats" :disabled="statsLoading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
            </button>
          </div>
          <div v-if="weeklyStats.length > 0" class="weekly-stats">
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
          <div v-else class="empty-stats">
            <p>Нет данных о статистике</p>
            <button @click="fetchWeeklyStats" class="load-stats-btn">Загрузить статистику</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно добавления устройства -->
    <div v-if="showAddDeviceModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Добавить новое устройство</h3>
          <button class="modal-close" @click="showAddDeviceModal = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="deviceName">Название устройства *</label>
            <input
              type="text"
              id="deviceName"
              v-model="newDevice.device_name"
              placeholder="Например: Рабочий ноутбук"
              class="form-input"
              :class="{ 'error': addDeviceError.device_name }"
              @keyup.enter="addDevice"
            />
            <span v-if="addDeviceError.device_name" class="error-text">{{ addDeviceError.device_name }}</span>
          </div>
          <div class="form-group">
            <label for="deviceType">Платформа</label>
            <select id="deviceType" v-model="newDevice.platform" class="form-select">
              <option value="windows">Windows</option>
              <option value="macos">macOS</option>
              <option value="linux">Linux</option>
              <option value="android">Android</option>
              <option value="ios">iOS</option>
              <option value="other">Другое</option>
            </select>
          </div>
          <div class="form-group">
            <label for="osVersion">Версия ОС</label>
            <input
              type="text"
              id="osVersion"
              v-model="newDevice.platform_version"
              placeholder="Например: Windows 11, macOS 14.2"
              class="form-input"
              @keyup.enter="addDevice"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-btn cancel" @click="showAddDeviceModal = false">
            Отмена
          </button>
          <button 
            class="modal-btn submit" 
            @click="addDevice" 
            :disabled="!newDevice.device_name.trim() || addingDevice"
          >
            <span v-if="addingDevice">Добавление...</span>
            <span v-else>Добавить устройство</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Модальное окно токена устройства -->
    <div v-if="showTokenModal && selectedDevice" class="modal-overlay" @click="closeModal">
      <div class="modal-content token-modal" @click.stop>
        <div class="modal-header">
          <h3>
            <span v-if="selectedDevice.device_id">Токен устройства "{{ selectedDevice.device_name }}"</span>
            <span v-else>Токен для регистрации "{{ selectedDevice.device_name }}"</span>
          </h3>
          <button class="modal-close" @click="showTokenModal = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="token-info">
            <div class="token-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
              </svg>
            </div>
            <p class="token-description">
              <span v-if="selectedDevice.device_id">
                Этот токен используется для аутентификации устройства при синхронизации.
              </span>
              <span v-else>
                Используйте этот токен для регистрации устройства в клиенте ActivityWatch Sync.
              </span>
              Сохраните токен в безопасном месте.
            </p>
          </div>

          <div class="token-display-container">
            <!-- Существующие токены -->
            <div v-if="deviceTokens.length > 0" class="existing-tokens">
              <h4>Активные токены:</h4>
              <div v-for="token in deviceTokens" :key="token.id" class="token-item">
                <div class="token-item-info">
                  <span class="token-name">{{ token.name }}</span>
                  <span class="token-date">Создан: {{ formatDate(token.created_at) }}</span>
                  <span v-if="token.expires_at" class="token-expiry">
                    Истекает: {{ formatDate(token.expires_at) }}
                  </span>
                </div>
                <button class="token-revoke-btn" @click="revokeToken(token.id)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Создание нового токена -->
            <div class="create-token-section">
              <h4>Создать новый токен</h4>
              <div class="form-group">
                <label for="tokenName">Название токена</label>
                <input
                  type="text"
                  id="tokenName"
                  v-model="newToken.name"
                  placeholder="Например: Основной токен"
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label for="expiryDays">Срок действия (дней)</label>
                <input
                  type="number"
                  id="expiryDays"
                  v-model="newToken.expires_in_days"
                  min="1"
                  max="365"
                  class="form-input"
                  placeholder="30"
                />
              </div>
              <button 
                class="create-token-btn" 
                @click="createToken"
                :disabled="!newToken.name.trim() || creatingToken"
              >
                <span v-if="creatingToken">Создание...</span>
                <span v-else>Создать токен</span>
              </button>
            </div>

            <!-- Отображение нового токена -->
            <div v-if="newlyCreatedToken" class="new-token-display">
              <div class="new-token-header">
                <h4>Новый токен создан!</h4>
                <button class="close-new-token" @click="newlyCreatedToken = null">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
              
              <div class="new-token-value">
                <div class="token-value-display">
                  <span class="token-segment">{{ maskedToken(newlyCreatedToken.token) }}</span>
                </div>
                
                <button 
                  class="copy-token-btn" 
                  @click="copyToken(newlyCreatedToken.token)"
                  :class="{ 'copied': tokenCopied }"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                  </svg>
                  {{ tokenCopied ? 'Скопировано!' : 'Копировать токен' }}
                </button>
              </div>
              
              <div class="token-warnings">
                <div class="warning-item">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.408 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                  </svg>
                  <span>Токен будет показан только один раз. Сохраните его в безопасном месте.</span>
                </div>
                <div v-if="!selectedDevice.device_id" class="warning-item">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  <span>После копирования токена, используйте его в клиенте ActivityWatch Sync для регистрации устройства.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-btn cancel" @click="showTokenModal = false">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/auth'
import { devicesApi } from '@/api/devices' // Предполагаем, что этот API существует
import Swal from 'sweetalert2'

const router = useRouter()

// Данные пользователя
const userData = ref(null)
const loading = ref(true)
const error = ref('')
const statsLoading = ref(false)

// Устройства
const devices = ref([])
const deviceTokens = ref([])

// Модальные окна
const showAddDeviceModal = ref(false)
const showTokenModal = ref(false)
const selectedDevice = ref(null)

// Новое устройство
const newDevice = ref({
  device_name: '',
  platform: 'windows',
  platform_version: ''
})
const addingDevice = ref(false)
const addDeviceError = ref({})

// Токены
const newToken = ref({
  name: 'Основной токен',
  expires_in_days: 30
})
const newlyCreatedToken = ref(null)
const creatingToken = ref(false)
const tokenCopied = ref(false)

// Статистика
const weeklyStats = ref([
  { day: 'Пн', hours: 8.5, percentage: 85 },
  { day: 'Вт', hours: 7.2, percentage: 72 },
  { day: 'Ср', hours: 9.1, percentage: 91 },
  { day: 'Чт', hours: 6.8, percentage: 68 },
  { day: 'Пт', hours: 7.9, percentage: 79 },
  { day: 'Сб', hours: 3.2, percentage: 32 },
  { day: 'Вс', hours: 2.1, percentage: 21 }
])

// Получение данных пользователя и устройств
const fetchUserData = async () => {
  try {
    loading.value = true
    error.value = ''
    
    // Получаем данные пользователя
    const userResponse = await authApi.getMe()
    userData.value = userResponse
    
    // Получаем устройства пользователя
    await fetchDevices()
    
  } catch (err) {
    console.error('Ошибка при получении данных:', err)
    
    // Добавим детальную отладку
    if (err.response) {
      console.error('Ответ сервера:', err.response)
      console.error('Статус:', err.response.status)
      console.error('Данные:', err.response.data)
      console.error('Заголовки:', err.response.headers)
    }
    
    if (err.response?.status === 401) {
      error.value = 'Требуется авторизация'
      setTimeout(() => {
        router.push('/auth')
      }, 1500)
    } else if (err.response?.status === 404) {
      error.value = 'Пользователь не найден'
    } else if (err.message?.includes('Network Error')) {
      error.value = 'Проблема соединения с сервером'
    } else {
      error.value = 'Ошибка при загрузке данных: ' + (err.message || 'Неизвестная ошибка')
      
      // Проверяем, если сервер вернул HTML вместо JSON
      if (err.response?.data && typeof err.response.data === 'string' && 
          err.response.data.includes('<!DOCTYPE')) {
        error.value = 'Сервер вернул HTML вместо JSON. Проверьте API эндпоинты.'
      }
    }
    
  } finally {
    loading.value = false
  }
}

// Получение устройств
const fetchDevices = async () => {
  try {
    // Предполагаем, что devicesApi.getAll() возвращает список устройств
    const response = await devicesApi.getAll()
    devices.value = response.map(device => ({
      ...device,
      // Добавляем поле tokens если его нет в ответе
      tokens: device.tokens || []
    }))
  } catch (err) {
    console.error('Ошибка при получении устройств:', err)
    throw err
  }
}

// Получение токенов устройства
const fetchDeviceTokens = async (deviceId) => {
  try {
    // Предполагаем, что devicesApi.getTokens(deviceId) возвращает токены устройства
    const response = await devicesApi.getTokens(deviceId)
    deviceTokens.value = response
  } catch (err) {
    console.error('Ошибка при получении токенов устройства:', err)
    throw err
  }
}

// Получение статистики
const fetchWeeklyStats = async () => {
  try {
    statsLoading.value = true
    // TODO: Реализовать API для статистики
    // const response = await devicesApi.getWeeklyStats()
    // weeklyStats.value = response
  } catch (err) {
    console.error('Ошибка при получении статистики:', err)
  } finally {
    statsLoading.value = false
  }
}

// Добавление устройства
const addDevice = async () => {
  if (!newDevice.value.device_name.trim()) {
    addDeviceError.value = { device_name: 'Введите название устройства' }
    return
  }

  try {
    addingDevice.value = true
    addDeviceError.value = {}
    
    // Предполагаем, что devicesApi.create() создает устройство
    const response = await devicesApi.create(newDevice.value)
    
    // Добавляем устройство в список
    devices.value.unshift({
      ...response,
      tokens: []
    })
    
    // Обновляем счетчик устройств у пользователя
    if (userData.value) {
      userData.value.devices_count = (userData.value.devices_count || 0) + 1
    }
    
    Swal.fire({
      title: 'Успешно!',
      text: `Устройство "${response.device_name}" добавлено`,
      icon: 'success',
      timer: 2000
    })

    // Сброс формы
    newDevice.value = {
      device_name: '',
      platform: 'windows',
      platform_version: ''
    }
    
    showAddDeviceModal.value = false
    
  } catch (err) {
    console.error('Ошибка при добавлении устройства:', err)
    
    if (err.response?.data?.detail) {
      addDeviceError.value = { general: err.response.data.detail }
    } else {
      Swal.fire({
        title: 'Ошибка',
        text: 'Не удалось добавить устройство',
        icon: 'error'
      })
    }
  } finally {
    addingDevice.value = false
  }
}

// Удаление устройства
const removeDevice = async (deviceId) => {
  const device = devices.value.find(d => d.id === deviceId)
  if (!device) return

  const result = await Swal.fire({
    title: 'Удалить устройство?',
    text: `Устройство "${device.device_name}" будет удалено. Это действие нельзя отменить.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Да, удалить',
    cancelButtonText: 'Отмена'
  })

  if (result.isConfirmed) {
    try {
      // Предполагаем, что devicesApi.delete(deviceId) удаляет устройство
      await devicesApi.delete(deviceId)
      
      // Удаляем устройство из списка
      devices.value = devices.value.filter(d => d.id !== deviceId)
      
      // Обновляем счетчик устройств
      if (userData.value) {
        userData.value.devices_count = Math.max(0, (userData.value.devices_count || 0) - 1)
      }
      
      // Закрываем модальное окно токена если оно открыто для этого устройства
      if (selectedDevice.value?.id === deviceId) {
        showTokenModal.value = false
      }
      
      Swal.fire({
        title: 'Удалено!',
        text: 'Устройство удалено',
        icon: 'success',
        timer: 2000
      })
      
    } catch (err) {
      console.error('Ошибка при удалении устройства:', err)
      Swal.fire({
        title: 'Ошибка',
        text: 'Не удалось удалить устройство',
        icon: 'error'
      })
    }
  }
}

// Открытие модального окна токена
const openTokenModal = async (device) => {
  selectedDevice.value = device
  deviceTokens.value = device.tokens || []
  showTokenModal.value = true
  newlyCreatedToken.value = null
  tokenCopied.value = false
  
  // Загружаем токены если их нет
  if (deviceTokens.value.length === 0 && device.id) {
    try {
      await fetchDeviceTokens(device.id)
    } catch (err) {
      console.error('Ошибка загрузки токенов:', err)
    }
  }
}

// Создание токена
const createToken = async () => {
  if (!selectedDevice.value || !newToken.value.name.trim()) return

  try {
    creatingToken.value = true
    
    // Предполагаем, что devicesApi.createToken(deviceId, tokenData) создает токен
    const response = await devicesApi.createToken(selectedDevice.value.id, {
      name: newToken.value.name,
      expires_in_days: newToken.value.expires_in_days
    })
    
    newlyCreatedToken.value = response
    
    // Добавляем токен в список (без самого токена для безопасности)
    deviceTokens.value.push({
      id: response.id,
      name: response.name,
      created_at: response.created_at,
      expires_at: response.expires_at
    })
    
    // Сбрасываем форму
    newToken.value = {
      name: 'Основной токен',
      expires_in_days: 30
    }
    
  } catch (err) {
    console.error('Ошибка при создании токена:', err)
    Swal.fire({
      title: 'Ошибка',
      text: 'Не удалось создать токен',
      icon: 'error'
    })
  } finally {
    creatingToken.value = false
  }
}

// Отзыв токена
const revokeToken = async (tokenId) => {
  const result = await Swal.fire({
    title: 'Отозвать токен?',
    text: 'Токен станет недействительным. Это действие нельзя отменить.',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Да, отозвать',
    cancelButtonText: 'Отмена'
  })

  if (result.isConfirmed && selectedDevice.value) {
    try {
      // Предполагаем, что devicesApi.revokeToken(deviceId, tokenId) отзывает токен
      await devicesApi.revokeToken(selectedDevice.value.id, tokenId)
      
      // Удаляем токен из списка
      deviceTokens.value = deviceTokens.value.filter(t => t.id !== tokenId)
      
      Swal.fire({
        title: 'Отозван!',
        text: 'Токен отозван',
        icon: 'success',
        timer: 2000
      })
      
    } catch (err) {
      console.error('Ошибка при отзыве токена:', err)
      Swal.fire({
        title: 'Ошибка',
        text: 'Не удалось отозвать токен',
        icon: 'error'
      })
    }
  }
}

// Синхронизация устройства
const syncDevice = async (deviceId) => {
  const device = devices.value.find(d => d.id === deviceId)
  if (!device || !device.device_id) return

  try {
    // Предполагаем, что devicesApi.sync(deviceId) запускает синхронизацию
    await devicesApi.sync(deviceId)
    
    // Обновляем время последней активности
    device.last_seen = new Date().toISOString()
    device.is_active = true
    
    Swal.fire({
      title: 'Синхронизировано!',
      text: `Устройство "${device.device_name}" синхронизировано`,
      icon: 'success',
      timer: 1500
    })
    
  } catch (err) {
    console.error('Ошибка при синхронизации:', err)
    Swal.fire({
      title: 'Ошибка',
      text: 'Не удалось синхронизировать устройство',
      icon: 'error'
    })
  }
}

// Копирование токена
const copyToken = (token) => {
  navigator.clipboard.writeText(token)
    .then(() => {
      tokenCopied.value = true
      setTimeout(() => {
        tokenCopied.value = false
      }, 3000)
    })
    .catch(err => {
      console.error('Ошибка копирования:', err)
      Swal.fire({
        title: 'Ошибка',
        text: 'Не удалось скопировать токен',
        icon: 'error'
      })
    })
}

// Маскированный токен для отображения
const maskedToken = (token) => {
  if (!token) return ''
  if (token.length <= 16) return token
  return `${token.substring(0, 8)}...${token.substring(token.length - 8)}`
}

// Выход
const handleLogout = async () => {
  try {
    const result = await Swal.fire({
      title: 'Выйти?',
      text: 'Вы уверены, что хотите выйти из аккаунта?',
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: 'Да, выйти',
      cancelButtonText: 'Отмена'
    })
    
    if (result.isConfirmed) {
      await authApi.logout()
      localStorage.removeItem('user')
      router.push('/auth')
      
      Swal.fire({
        title: 'Успешно!',
        text: 'Вы вышли из аккаунта',
        icon: 'success',
        timer: 2000
      })
    }
    
  } catch (err) {
    console.error('Ошибка при выходе:', err)
  }
}

// Редактирование профиля
const editProfile = () => {
  Swal.fire({
    title: 'Редактирование профиля',
    text: 'Эта функция в разработке',
    icon: 'info',
    confirmButtonText: 'OK'
  })
}

// Вспомогательные функции
const getInitials = (name) => {
  if (!name) return '??'
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

const formatDate = (dateString) => {
  if (!dateString) return 'Н/Д'
  
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch (e) {
    return 'Н/Д'
  }
}

const getDeviceTypeClass = (platform) => {
  const classes = {
    windows: 'windows',
    macos: 'mac',
    mac: 'mac',
    android: 'android',
    linux: 'linux',
    ios: 'ios'
  }
  return classes[platform] || 'default'
}

const getDeviceTypeName = (platform) => {
  const names = {
    windows: 'Windows',
    macos: 'macOS',
    mac: 'macOS',
    android: 'Android',
    linux: 'Linux',
    ios: 'iOS'
  }
  return names[platform] || platform || 'Другое'
}

const formatLastSeen = (dateString) => {
  if (!dateString) return 'Никогда'
  
  try {
    const now = new Date()
    const date = new Date(dateString)
    const diff = now - date
    const hours = Math.floor(diff / 3600000)
    
    if (hours < 1) return 'Только что'
    if (hours < 24) return `${hours}ч назад`
    const days = Math.floor(hours / 24)
    if (days < 7) return `${days}д назад`
    
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short'
    })
  } catch (e) {
    return 'Н/Д'
  }
}

const getBarColor = (percentage) => {
  if (percentage > 80) return 'high'
  if (percentage > 50) return 'medium'
  return 'low'
}

const closeModal = (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    showAddDeviceModal.value = false
    showTokenModal.value = false
  }
}

// Загружаем данные при монтировании компонента
onMounted(() => {
  fetchUserData()
})
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

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
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

.add-device-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.add-device-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
}

.add-device-btn svg {
  width: 18px;
  height: 18px;
}

/* Состояние пустого списка */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--text-muted);
}

.empty-state svg {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  color: var(--text-muted);
  opacity: 0.5;
}

.empty-state p {
  font-size: 16px;
  margin-bottom: 24px;
}

.empty-state-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.empty-state-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
}

/* Список устройств */
.devices-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.device-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
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

.device-item.pending {
  border-style: dashed;
  border-color: var(--warning-color);
  background: rgba(245, 158, 11, 0.05);
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

.device-icon.default {
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
}

.device-info {
  flex: 1;
}

.device-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.device-header h4 {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

.status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.status-badge.pending {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning-color);
}

.status-badge.active {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.status-badge.inactive {
  background: rgba(148, 163, 184, 0.1);
  color: var(--text-muted);
}

.device-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 12px;
}

.device-type {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.device-version, .client-version {
  color: var(--text-muted);
}

.last-seen-info, .registration-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.last-seen-info svg, .registration-info svg {
  width: 14px;
  height: 14px;
}

.registration-info {
  color: var(--warning-color);
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
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 12px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.token {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.action-btn.token:hover:not(:disabled) {
  background: #8b5cf6;
  color: white;
}

.action-btn.sync {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
}

.action-btn.sync:hover:not(:disabled) {
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

.action-btn svg {
  width: 14px;
  height: 14px;
}

/* Статистика за неделю */
.stats-card .card-header {
  margin-bottom: 0;
}

.refresh-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-btn svg {
  width: 18px;
  height: 18px;
}

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

.empty-stats {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--text-muted);
}

.empty-stats p {
  margin-bottom: 16px;
}

.load-stats-btn {
  padding: 10px 20px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.load-stats-btn:hover {
  background: var(--primary-color);
  color: white;
}

/* Модальное окно добавления устройства */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

.modal-content {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  animation: modalSlideIn 0.3s ease;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, white, var(--text-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.modal-close svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}

.form-input,
.form-select {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: white;
  font-size: 14px;
  transition: all 0.3s ease;
}

.form-input.error {
  border-color: var(--danger-color);
}

.error-text {
  color: var(--danger-color);
  font-size: 12px;
  margin-top: 4px;
  display: block;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

.form-input::placeholder {
  color: var(--text-muted);
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid var(--border-color);
}

.modal-btn {
  flex: 1;
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.modal-btn.cancel {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.modal-btn.cancel:hover {
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.modal-btn.submit {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
}

.modal-btn.submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
}

.modal-btn.submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Модальное окно токена */
.token-modal {
  max-width: 600px;
}

.token-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: rgba(99, 102, 241, 0.05);
  border-radius: 12px;
  border-left: 4px solid var(--primary-color);
}

.token-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.token-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.token-description {
  flex: 1;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.token-display-container {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
}

.existing-tokens {
  margin-bottom: 24px;
}

.existing-tokens h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-secondary);
}

.token-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid var(--border-color);
}

.token-item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.token-name {
  font-weight: 500;
  color: white;
}

.token-date, .token-expiry {
  font-size: 11px;
  color: var(--text-muted);
}

.token-revoke-btn {
  background: rgba(239, 68, 68, 0.1);
  border: none;
  color: var(--danger-color);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.token-revoke-btn:hover {
  background: var(--danger-color);
  color: white;
}

.token-revoke-btn svg {
  width: 16px;
  height: 16px;
}

.create-token-section {
  margin-bottom: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.create-token-section h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-secondary);
}

.create-token-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.create-token-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
}

.create-token-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Отображение нового токена */
.new-token-display {
  margin-top: 24px;
  padding: 20px;
  background: rgba(15, 23, 42, 0.9);
  border-radius: 12px;
  border: 2px solid var(--primary-color);
}

.new-token-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.new-token-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-color);
  margin: 0;
}

.close-new-token {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.close-new-token:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.close-new-token svg {
  width: 18px;
  height: 18px;
}

.new-token-value {
  margin-bottom: 16px;
}

.token-value-display {
  width: 100%;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  background: rgba(0, 0, 0, 0.3);
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  margin-bottom: 16px;
  text-align: center;
  color: var(--success-color);
  word-break: break-all;
}

.copy-token-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.copy-token-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
}

.copy-token-btn.copied {
  background: linear-gradient(135deg, var(--success-color), #16a34a);
}

.copy-token-btn svg {
  width: 18px;
  height: 18px;
}

.token-warnings {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.warning-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: rgba(245, 158, 11, 0.05);
  border-radius: 8px;
  border-left: 3px solid var(--warning-color);
}

.warning-item svg {
  width: 16px;
  height: 16px;
  color: var(--warning-color);
  flex-shrink: 0;
  margin-top: 2px;
}

.warning-item span {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* Анимации */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
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
  .profile-container {
    padding: 20px 16px;
  }
  
  .profile-header h1 {
    font-size: 28px;
  }
  
  .user-card {
    flex-direction: column;
    gap: 20px;
  }
  
  .user-info {
    width: 100%;
  }
  
  .edit-btn {
    width: 100%;
  }
  
  .device-item {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .device-actions {
    opacity: 1;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  
  .weekly-stats {
    overflow-x: auto;
    padding-bottom: 10px;
  }
  
  .day-stat {
    min-width: 50px;
  }
  
  .modal-content {
    width: 95%;
    margin: 10px;
  }
  
  .nav-right {
    gap: 10px;
  }
  
  .nav-link span {
    display: none;
  }
  
  .nav-link {
    padding: 8px;
  }
}
</style>