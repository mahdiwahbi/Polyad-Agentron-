<template>
  <div :class="[theme, { 'dark': isDarkMode }]" class="app">
    <header class="app-header">
      <div class="header-content">
        <img src="@/assets/logo.svg" alt="Polyad Logo" class="logo" />
        <div class="header-actions">
          <button @click="toggleTheme" class="theme-toggle">
            <i :class="[isDarkMode ? 'fas fa-sun' : 'fas fa-moon']"></i>
          </button>
          <button @click="toggleLanguage" class="language-toggle">
            <i class="fas fa-globe"></i>
            <span>{{ currentLanguage }}</span>
          </button>
          <button @click="toggleMobileMenu" class="menu-toggle" v-if="isMobile">
            <i class="fas fa-bars"></i>
          </button>
        </div>
      </div>
    </header>

    <nav :class="['app-nav', { 'mobile': isMobile, 'open': isMobileMenuOpen }]">
      <ul class="nav-list">
        <li v-for="(item, index) in navigation" :key="index" class="nav-item">
          <router-link :to="item.path" class="nav-link">
            <i :class="item.icon"></i>
            <span>{{ $t(item.label) }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <main class="app-main">
      <router-view></router-view>
    </main>

    <footer class="app-footer">
      <div class="footer-content">
        <span>{{ $t('footer.copyright') }}</span>
        <div class="footer-links">
          <a href="https://github.com/polyad" target="_blank" rel="noopener">
            <i class="fab fa-github"></i>
          </a>
          <a href="https://twitter.com/polyad" target="_blank" rel="noopener">
            <i class="fab fa-twitter"></i>
          </a>
        </div>
      </div>
    </footer>

    <notifications position="top right" class="notification-container" />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { useLanguageStore } from '@/stores/language'

export default {
  name: 'App',
  setup() {
    const { t, locale } = useI18n()
    const router = useRouter()
    const themeStore = useThemeStore()
    const languageStore = useLanguageStore()

    const isMobile = ref(false)
    const isMobileMenuOpen = ref(false)
    const theme = computed(() => themeStore.currentTheme)
    const isDarkMode = computed(() => themeStore.isDarkMode)
    const currentLanguage = computed(() => languageStore.currentLanguage)

    const navigation = [
      { path: '/', label: 'navigation.dashboard', icon: 'fas fa-home' },
      { path: '/metrics', label: 'navigation.metrics', icon: 'fas fa-chart-line' },
      { path: '/resources', label: 'navigation.resources', icon: 'fas fa-server' },
      { path: '/security', label: 'navigation.security', icon: 'fas fa-shield-alt' },
      { path: '/settings', label: 'navigation.settings', icon: 'fas fa-cog' }
    ]

    const toggleTheme = () => {
      themeStore.toggleTheme()
    }

    const toggleLanguage = () => {
      const languages = ['en', 'fr', 'es', 'de']
      const currentIndex = languages.indexOf(locale.value)
      const nextIndex = (currentIndex + 1) % languages.length
      locale.value = languages[nextIndex]
      languageStore.setLanguage(languages[nextIndex])
    }

    const toggleMobileMenu = () => {
      isMobileMenuOpen.value = !isMobileMenuOpen.value
    }

    const checkMobile = () => {
      isMobile.value = window.innerWidth <= 768
    }

    onMounted(() => {
      checkMobile()
      window.addEventListener('resize', checkMobile)
    })

    return {
      isMobile,
      isMobileMenuOpen,
      theme,
      isDarkMode,
      currentLanguage,
      navigation,
      toggleTheme,
      toggleLanguage,
      toggleMobileMenu
    }
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: var(--background);
  color: var(--text);
  font-family: 'Inter', sans-serif;
}

.app-header {
  background: var(--header-bg);
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  height: 40px;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.theme-toggle,
.language-toggle,
.menu-toggle {
  background: transparent;
  border: none;
  color: var(--text);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.theme-toggle:hover,
.language-toggle:hover,
.menu-toggle:hover {
  background-color: var(--hover);
}

.app-nav {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 250px;
  background: var(--nav-bg);
  padding: 1rem;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.1);
  transform: translateX(0);
  transition: transform 0.3s ease-in-out;
}

.app-nav.mobile {
  transform: translateX(-100%);
}

.app-nav.mobile.open {
  transform: translateX(0);
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item {
  margin-bottom: 0.5rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  text-decoration: none;
  color: var(--text);
  border-radius: 4px;
  transition: background-color 0.2s;
}

.nav-link:hover {
  background-color: var(--hover);
}

.app-main {
  margin-left: 250px;
  padding: 2rem;
  min-height: calc(100vh - 200px);
}

.app-main.mobile {
  margin-left: 0;
}

.app-footer {
  background: var(--footer-bg);
  padding: 1rem;
  text-align: center;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-links {
  display: flex;
  gap: 1rem;
}

.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
}

/* Thème clair */
.light {
  --background: #ffffff;
  --text: #333333;
  --header-bg: #f8f9fa;
  --nav-bg: #ffffff;
  --footer-bg: #f8f9fa;
  --hover: #f0f0f0;
}

/* Thème sombre */
.dark {
  --background: #1a1a1a;
  --text: #ffffff;
  --header-bg: #2d2d2d;
  --nav-bg: #1a1a1a;
  --footer-bg: #2d2d2d;
  --hover: #2d2d2d;
}

/* Responsive */
@media (max-width: 768px) {
  .app-main {
    margin-left: 0;
  }

  .app-nav {
    width: 100%;
  }

  .nav-link {
    justify-content: center;
  }
}
</style>
