<template>
  <div class="polyad-app">
    <!-- Barre latérale -->
    <aside class="sidebar">
      <div class="logo">
        <img src="/assets/logo.svg" alt="Polyad" />
        <span>Polyad</span>
      </div>
      
      <nav class="navigation">
        <router-link to="/" class="nav-item">
          <i class="fas fa-home"></i>
          <span>Accueil</span>
        </router-link>
        
        <router-link to="/chat" class="nav-item">
          <i class="fas fa-comments"></i>
          <span>Chat</span>
        </router-link>
        
        <router-link to="/tasks" class="nav-item">
          <i class="fas fa-tasks"></i>
          <span>Tâches</span>
        </router-link>
        
        <router-link to="/monitoring" class="nav-item">
          <i class="fas fa-chart-line"></i>
          <span>Monitoring</span>
        </router-link>
        
        <router-link to="/settings" class="nav-item">
          <i class="fas fa-cog"></i>
          <span>Paramètres</span>
        </router-link>
      </nav>
    </aside>

    <!-- Contenu principal -->
    <main class="main-content">
      <!-- Barre de navigation supérieure -->
      <header class="topbar">
        <div class="search-bar">
          <input type="text" v-model="searchQuery" placeholder="Rechercher..." />
          <i class="fas fa-search"></i>
        </div>
        
        <div class="user-menu">
          <div class="notifications">
            <i class="fas fa-bell"></i>
            <span v-if="notificationsCount > 0" class="badge">{{ notificationsCount }}</span>
          </div>
          <div class="profile">
            <img :src="userAvatar" alt="Profil" class="avatar" />
            <span>{{ userName }}</span>
          </div>
        </div>
      </header>

      <!-- Contenu de la page -->
      <div class="page-content">
        <CommunicationUI />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CommunicationUI from './components/CommunicationUI.vue'

// États réactifs
const searchQuery = ref('')
const notificationsCount = ref(0)
const userAvatar = ref('/assets/default-avatar.png')
const userName = ref('Utilisateur')

// Fonction pour mettre à jour le nombre de notifications
const updateNotifications = (count) => {
  notificationsCount.value = count
}

// Fonction pour gérer la recherche
const handleSearch = () => {
  // Logique de recherche
}
</script>

<style scoped>
.polyad-app {
  display: flex;
  height: 100vh;
  background-color: #f5f7fa;
}

/* Barre latérale */
.sidebar {
  width: 250px;
  background: #ffffff;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: bold;
  font-size: 1.2rem;
}

.logo img {
  height: 32px;
}

.navigation {
  flex: 1;
  padding: 20px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: #333;
  text-decoration: none;
  transition: background-color 0.2s;
  gap: 10px;
}

.nav-item:hover {
  background-color: #f8f9fa;
}

.nav-item.router-link-active {
  background-color: #e9ecef;
  color: #007bff;
}

/* Contenu principal */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.topbar {
  height: 60px;
  background: #ffffff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.search-bar {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  border-radius: 20px;
  padding: 8px 12px;
  width: 300px;
}

.search-bar input {
  border: none;
  background: none;
  outline: none;
  width: 100%;
  padding: 0 8px;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 20px;
}

.notifications {
  position: relative;
}

.badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #dc3545;
  color: white;
  border-radius: 50%;
  padding: 2px 6px;
  font-size: 0.75rem;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.page-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>
