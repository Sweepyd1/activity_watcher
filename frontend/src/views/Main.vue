<template>
  <div class="landing-page">
    <!-- Навигация -->
    <nav class="navbar animate-fade-in">
      <div class="container">
        <div class="nav-content">
          <div class="logo">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="var(--primary-color)" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <span class="logo-text">TimeTracker</span>
          </div>
          
          <div class="nav-links">
            <a href="#features" class="nav-link">Возможности</a>
            <a href="#download" class="nav-link">Скачать</a>
         
          </div>
          
          <div class="nav-actions">
            <router-link to="/auth" class="btn btn-outline">Войти</router-link>
            <router-link to="/auth" class="btn btn-primary">Регистрация</router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- Герой-секция -->
    <section class="hero">
      <div class="container">
        <div class="hero-content animate-slide-up">
          <div class="hero-text">
            <h1 class="hero-title">
              Отслеживайте время
              <span class="text-gradient">на всех устройствах</span>
            </h1>
            <p class="hero-subtitle">
              Автоматический трекинг активности на компьютере и телефоне. 
              Простая аналитика и синхронизация между устройствами.
            </p>
            <div class="hero-actions">
              <a href="#download" class="btn btn-primary btn-large">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
                Скачать бесплатно
              </a>
              <router-link to="/register" class="btn btn-outline btn-large">
                Начать онлайн
              </router-link>
            </div>
          </div>
          
          <div class="hero-visual">
            <div class="dashboard-preview">
              <div class="dashboard-content">
                <div class="stats-row">
                  <div class="stat-item">
                    <div class="stat-value">6ч 24м</div>
                    <div class="stat-label">За компьютером</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">2ч 15м</div>
                    <div class="stat-label">На телефоне</div>
                  </div>
                </div>
                <div class="chart-container">
                  <div class="chart-bar" style="height: 80%; background: var(--primary-color);"></div>
                  <div class="chart-bar" style="height: 60%; background: var(--primary-color); opacity: 0.8;"></div>
                  <div class="chart-bar" style="height: 90%; background: var(--primary-color);"></div>
                  <div class="chart-bar" style="height: 70%; background: var(--primary-color); opacity: 0.8;"></div>
                  <div class="chart-bar" style="height: 85%; background: var(--primary-color);"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Возможности -->
    <section id="features" class="features">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">Основные возможности</h2>
          <p class="section-subtitle">Все необходимое для анализа продуктивности</p>
        </div>
        
        <div class="features-grid">
          <div class="feature-card animate-fade-in">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="var(--primary-color)" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
            </div>
            <h3 class="feature-title">Аналитика времени</h3>
            <p class="feature-description">
              Подробные отчеты по приложениям, проектам и категориям
            </p>
          </div>
          
          <div class="feature-card animate-fade-in" style="animation-delay: 0.1s;">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="var(--primary-color)" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <h3 class="feature-title">Автосинхронизация</h3>
            <p class="feature-description">
              Данные автоматически синхронизируются между устройствами
            </p>
          </div>
          
          <div class="feature-card animate-fade-in" style="animation-delay: 0.2s;">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="var(--primary-color)" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
            </div>
            <h3 class="feature-title">Конфиденциальность</h3>
            <p class="feature-description">
              Ваши данные шифруются и остаются под вашим контролем
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Скачать -->
    <section id="download" class="download">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">Доступно на всех платформах</h2>
          <p class="section-subtitle">Установите приложение на ваше устройство</p>
        </div>
        
        <div class="platforms-grid">
          <a href="#" class="platform-card">
            <div class="platform-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
            </div>
            <div class="platform-info">
              <div class="platform-name">Windows</div>
              <div class="platform-desc">Windows 10+</div>
            </div>
          </a>
          
          <a href="#" class="platform-card">
            <div class="platform-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/>
              </svg>
            </div>
            <div class="platform-info">
              <div class="platform-name">macOS</div>
              <div class="platform-desc">macOS 11+</div>
            </div>
          </a>
          
          <a href="#" class="platform-card">
            <div class="platform-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
              </svg>
            </div>
            <div class="platform-info">
              <div class="platform-name">Linux</div>
              <div class="platform-desc">Debian, Ubuntu</div>
            </div>
          </a>
          
          <a href="#" class="platform-card">
            <div class="platform-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/>
              </svg>
            </div>
            <div class="platform-info">
              <div class="platform-name">Android</div>
              <div class="platform-desc">Android 8+</div>
            </div>
          </a>
        </div>
      </div>
    </section>

    <!-- Тарифы -->
    

    <!-- Футер -->
    <footer class="footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-section">
            <div class="footer-logo">
              <div class="logo-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="var(--primary-color)" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <span class="logo-text">TimeTracker</span>
            </div>
            <p class="footer-description">
              Трекинг времени и продуктивности
            </p>
          </div>
          
          <div class="footer-section">
            <h4 class="footer-title">Продукт</h4>
            <a href="#features" class="footer-link">Возможности</a>
          
            <a href="#download" class="footer-link">Скачать</a>
          </div>
          
          <div class="footer-section">
            <h4 class="footer-title">Разработчикам</h4>
            <a href="#" class="footer-link">API</a>
            <a href="#" class="footer-link">Документация</a>
            <a href="#" class="footer-link">GitHub</a>
          </div>
          
          <div class="footer-section">
            <h4 class="footer-title">Поддержка</h4>
            <a href="#" class="footer-link">Помощь</a>
            <a href="#" class="footer-link">Контакты</a>
            <a href="#" class="footer-link">Статус</a>
          </div>
        </div>
        
        <div class="footer-bottom">
          <div class="copyright">
            © 2024 TimeTracker. Все права защищены.
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Плавный скролл к якорям
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      e.preventDefault()
      const targetId = anchor.getAttribute('href')
      if (targetId === '#') return
      
      const targetElement = document.querySelector(targetId)
      if (targetElement) {
        window.scrollTo({
          top: targetElement.offsetTop - 80,
          behavior: 'smooth'
        })
      }
    })
  })
})
</script>

<style scoped>
.landing-page {
  background-color: var(--background-dark);
  color: var(--text-primary);
}

/* Контейнер */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Навигация */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: var(--surface-dark);
  border-bottom: 1px solid var(--border-color);
  backdrop-filter: blur(10px);
  z-index: 1000;
}

.nav-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 70px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
}

.logo-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  color: var(--text-primary);
}

.nav-links {
  display: flex;
  gap: 32px;
}

.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.3s;
}

.nav-link:hover {
  color: var(--primary-color);
}

.nav-actions {
  display: flex;
  gap: 12px;
}

/* Кнопки */
.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-outline {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-outline:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

.btn-large {
  padding: 14px 28px;
  font-size: 16px;
}

.btn-full {
  width: 100%;
}

/* Герой-секция */
.hero {
  padding: 140px 0 100px;
  background: linear-gradient(to bottom, var(--background-dark), var(--surface-dark));
}

.hero-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 80px;
  align-items: center;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 24px;
}

.text-gradient {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 18px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 32px;
  max-width: 500px;
}

.hero-actions {
  display: flex;
  gap: 16px;
}

.icon {
  width: 20px;
  height: 20px;
}

.dashboard-preview {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.stats-row {
  display: flex;
  gap: 32px;
  margin-bottom: 32px;
}

.stat-item {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted);
}

.chart-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  height: 200px;
  padding: 20px 0;
}

.chart-bar {
  flex: 1;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s;
}

/* Секции */
section {
  padding: 100px 0;
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 16px;
}

.section-subtitle {
  font-size: 18px;
  color: var(--text-secondary);
  max-width: 500px;
  margin: 0 auto;
}

/* Возможности */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 32px;
  max-width: 1000px;
  margin: 0 auto;
}

.feature-card {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  transition: transform 0.3s, border-color 0.3s;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: var(--primary-color);
}

.feature-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.1);
}

.feature-icon svg {
  width: 24px;
  height: 24px;
}

.feature-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 12px;
}

.feature-description {
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Скачать */
.platforms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.platform-card {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  text-decoration: none;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s;
}

.platform-card:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
}

.platform-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.platform-icon svg {
  width: 24px;
  height: 24px;
}

.platform-info {
  flex: 1;
}

.platform-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.platform-desc {
  font-size: 14px;
  color: var(--text-muted);
}

/* Тарифы */
.pricing-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 32px;
  max-width: 700px;
  margin: 0 auto;
}

.pricing-card {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 32px;
  position: relative;
}

.pricing-card.featured {
  border-color: var(--primary-color);
}

.pricing-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--primary-color);
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.pricing-header {
  text-align: center;
  margin-bottom: 32px;
}

.pricing-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 16px;
}

.pricing-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
}

.price {
  font-size: 48px;
  font-weight: 700;
}

.period {
  font-size: 16px;
  color: var(--text-muted);
}

.pricing-features {
  list-style: none;
  padding: 0;
  margin: 0 0 32px;
}

.pricing-features li {
  padding: 12px 0;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.pricing-features li:last-child {
  border-bottom: none;
}

/* Футер */
.footer {
  background: var(--surface-dark);
  border-top: 1px solid var(--border-color);
  padding: 60px 0 30px;
}

.footer-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 40px;
  margin-bottom: 40px;
}

.footer-section {
  display: flex;
  flex-direction: column;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  font-size: 20px;
  font-weight: 600;
}

.footer-description {
  color: var(--text-secondary);
  line-height: 1.6;
}

.footer-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--text-primary);
}

.footer-link {
  color: var(--text-secondary);
  text-decoration: none;
  margin-bottom: 12px;
  font-size: 14px;
  transition: color 0.3s;
}

.footer-link:hover {
  color: var(--primary-color);
}

.footer-bottom {
  padding-top: 30px;
  border-top: 1px solid var(--border-color);
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}

/* Адаптивность */
@media (max-width: 768px) {
  .hero-content {
    grid-template-columns: 1fr;
    gap: 40px;
  }
  
  .hero-title {
    font-size: 36px;
  }
  
  .hero-actions {
    flex-direction: column;
  }
  
  .nav-links {
    display: none;
  }
  
  .features-grid,
  .platforms-grid {
    grid-template-columns: 1fr;
  }
  
  section {
    padding: 60px 0;
  }
  
  .section-title {
    font-size: 28px;
  }
  
  .pricing-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .container {
    padding: 0 16px;
  }
  
  .hero {
    padding: 100px 0 60px;
  }
  
  .nav-actions {
    display: none;
  }
  
  .stat-value {
    font-size: 24px;
  }
}
</style>