<template>
  <div class="communication-container">
    <!-- Barre de navigation supérieure -->
    <header class="communication-header">
      <div class="header-left">
        <button class="header-button" @click="toggleSidebar">
          <i class="fas fa-bars"></i>
        </button>
        <h1>Polyad</h1>
      </div>
      <div class="header-right">
        <button class="header-button" @click="toggleDarkMode">
          <i :class="darkMode ? 'fas fa-sun' : 'fas fa-moon'"></i>
        </button>
        <button class="header-button" @click="openSettings">
          <i class="fas fa-cog"></i>
        </button>
      </div>
    </header>

    <!-- Contenu principal -->
    <main class="communication-main">
      <!-- Barre latérale -->
      <aside :class="['sidebar', { 'sidebar-collapsed': isSidebarCollapsed }]">
        <div class="sidebar-content">
          <div class="sidebar-section">
            <h3>Conversations</h3>
            <div class="conversations-list">
              <div v-for="(conversation, index) in conversations" 
                   :key="index" 
                   :class="['conversation-item', { 'active': activeConversation === index }]"
                   @click="selectConversation(index)">
                <div class="conversation-icon">
                  <i class="fas fa-comments"></i>
                </div>
                <div class="conversation-info">
                  <span class="conversation-title">{{ conversation.title }}</span>
                  <span class="conversation-preview">{{ conversation.preview }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="sidebar-section">
            <h3>Paramètres</h3>
            <div class="settings-list">
              <div class="setting-item">
                <label>
                  <input type="checkbox" v-model="showTimestamps">
                  Afficher les horodatages
                </label>
              </div>
              <div class="setting-item">
                <label>
                  <input type="checkbox" v-model="showAvatars">
                  Afficher les avatars
                </label>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- Zone de chat -->
      <section class="chat-area">
        <div class="chat-messages">
          <div v-for="(message, index) in currentMessages" 
               :key="index" 
               :class="['message', message.type]">
            <div v-if="showAvatars" class="message-avatar">
              <img :src="message.avatar" alt="Avatar" />
            </div>
            <div class="message-content">
              <div class="message-header">
                <span class="message-author">{{ message.author }}</span>
                <span v-if="showTimestamps" class="message-timestamp">
                  {{ formatTime(message.timestamp) }}
                </span>
              </div>
              <div class="message-text">
                {{ message.text }}
              </div>
              <div v-if="message.attachments.length > 0" class="message-attachments">
                <div v-for="(attachment, index) in message.attachments" 
                     :key="index" 
                     class="attachment-item">
                  <img v-if="isImage(attachment)" 
                       :src="attachment.url" 
                       :alt="attachment.name" />
                  <a v-else :href="attachment.url" 
                     :download="attachment.name">
                    {{ attachment.name }}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-input">
          <div class="input-wrapper">
            <button class="input-button" @click="openFilePicker">
              <i class="fas fa-paperclip"></i>
            </button>
            <input type="file" 
                   ref="fileInput" 
                   @change="handleFileUpload"
                   style="display: none" />
            
            <textarea v-model="inputMessage" 
                      @keypress.enter.prevent="sendMessage"
                      placeholder="Tapez votre message..."
                      ref="messageInput"></textarea>
            
            <button class="input-button" 
                    @click="sendMessage" 
                    :disabled="!inputMessage.trim()">
              <i class="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>
      </section>
    </main>

    <!-- Modal de paramètres -->
    <div v-if="showSettingsModal" class="settings-modal">
      <div class="modal-content">
        <h2>Paramètres</h2>
        <button class="close-button" @click="closeSettings">
          <i class="fas fa-times"></i>
        </button>
        
        <div class="settings-section">
          <h3>Apparence</h3>
          <div class="setting-item">
            <label>
              <input type="checkbox" v-model="darkMode">
              Mode sombre
            </label>
          </div>
        </div>

        <div class="settings-section">
          <h3>Notifications</h3>
          <div class="setting-item">
            <label>
              <input type="checkbox" v-model="notificationsEnabled">
              Activer les notifications
            </label>
          </div>
        </div>

        <button class="save-settings" @click="saveSettings">
          Enregistrer
        </button>
      </div>
    </div>

    <!-- État de la connexion -->
    <div v-if="internetStatus" class="internet-status" :class="internetStatus.connected ? 'connected' : 'disconnected'">
      {{ internetStatus.connected ? 'Connecté' : 'Déconnecté' }} ({{ internetStatus.publicIP }})
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import agentService from '../services/agentService'
import { format } from 'date-fns'
import fr from 'date-fns/locale/fr'

// États réactifs
const isSidebarCollapsed = ref(false)
const darkMode = ref(false)
const showTimestamps = ref(true)
const showAvatars = ref(true)
const notificationsEnabled = ref(true)
const inputMessage = ref('')
const fileInput = ref(null)
const messageInput = ref(null)
const showSettingsModal = ref(false)
const internetStatus = ref({
  connected: false,
  publicIP: null,
  lastCheck: null
})

// Données de démonstration
const conversations = ref([
  {
    title: "Nouvelle conversation",
    preview: "Dernier message..."
  }
])

const activeConversation = ref(0)

const currentMessages = ref([
  {
    type: 'assistant',
    author: 'Polyad',
    avatar: '/assets/assistant-avatar.png',
    text: 'Bonjour ! Comment puis-je vous aider aujourd\'hui ?',
    timestamp: new Date(),
    attachments: []
  }
])

// Fonctions utilitaires
const formatTime = (timestamp) => {
  return format(new Date(timestamp), 'HH:mm', { locale: fr })
}

const isImage = (attachment) => {
  return attachment.type.startsWith('image/')
}

// Vérifier périodiquement la connexion Internet
const checkInternetConnection = async () => {
  try {
    const status = await agentService.checkInternetConnection()
    internetStatus.value = {
      ...status,
      lastCheck: new Date().toISOString()
    }
    
    // Mettre à jour l'interface si la connexion change
    if (status.connected) {
      // Récupérer les informations de l'agent
      const agentInfo = await agentService.getAgentInfo()
      console.log('Informations de l\'agent:', agentInfo)
    }
  } catch (error) {
    console.error('Erreur lors de la vérification de la connexion:', error)
  }
}

// Vérifier la connexion au démarrage
onMounted(() => {
  checkInternetConnection()
  // Vérifier périodiquement
  setInterval(checkInternetConnection, 30000) // Toutes les 30 secondes
})

// Gestion des événements
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

const toggleDarkMode = () => {
  darkMode.value = !darkMode.value
  document.documentElement.classList.toggle('dark', darkMode.value)
}

const openSettings = () => {
  showSettingsModal.value = true
}

const closeSettings = () => {
  showSettingsModal.value = false
}

const selectConversation = (index) => {
  activeConversation.value = index
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  // Ajouter le message utilisateur
  currentMessages.value.push({
    type: 'user',
    author: 'Vous',
    avatar: '/assets/user-avatar.png',
    text: inputMessage.value,
    timestamp: new Date(),
    attachments: []
  })
  
  // Envoyer la requête à l'agent
  try {
    const response = await agentService.sendRequest({
      message: inputMessage.value,
      context: currentMessages.value
    })
    
    // Ajouter la réponse de l'agent
    currentMessages.value.push({
      type: 'assistant',
      author: 'Polyad',
      avatar: '/assets/assistant-avatar.png',
      text: response.message,
      timestamp: new Date(),
      attachments: response.attachments || []
    })
  } catch (error) {
    console.error('Erreur lors de l\'envoi du message:', error)
    currentMessages.value.push({
      type: 'error',
      author: 'Système',
      text: 'Une erreur est survenue lors de l\'envoi du message.',
      timestamp: new Date()
    })
  }
  
  // Réinitialiser le champ
  inputMessage.value = ''
  messageInput.value.focus()
}

const openFilePicker = () => {
  fileInput.value.click()
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (file) {
    try {
      // Envoyer le fichier à l'agent
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await agentService.uploadFile(formData)
      
      // Ajouter le fichier aux messages
      currentMessages.value[currentMessages.value.length - 1].attachments.push({
        name: file.name,
        url: response.data.url,
        type: file.type
      })
    } catch (error) {
      console.error('Erreur lors du téléchargement du fichier:', error)
    }
  }
}

const saveSettings = async () => {
  try {
    await agentService.updateAgentSettings({
      darkMode: darkMode.value,
      showTimestamps: showTimestamps.value,
      showAvatars: showAvatars.value,
      notificationsEnabled: notificationsEnabled.value
    })
    closeSettings()
  } catch (error) {
    console.error('Erreur lors de la sauvegarde des paramètres:', error)
  }
}
</script>

<style scoped>
.communication-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--background-color);
  color: var(--text-color);
}

/* Header */
.communication-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: var(--header-bg);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-button {
  background: none;
  border: none;
  padding: 0.5rem;
  border-radius: 50%;
  cursor: pointer;
  transition: background-color 0.2s;
}

.header-button:hover {
  background-color: var(--hover-color);
}

/* Main content */
.communication-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 250px;
  background-color: var(--sidebar-bg);
  transition: width 0.3s ease;
  overflow-y: auto;
}

.sidebar-collapsed {
  width: 60px;
}

.sidebar-content {
  padding: 1rem;
}

.sidebar-section {
  margin-bottom: 1.5rem;
}

.sidebar-section h3 {
  margin-bottom: 0.5rem;
  color: var(--text-color);
}

/* Conversations list */
.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.conversation-item:hover {
  background-color: var(--hover-color);
}

.conversation-item.active {
  background-color: var(--active-color);
}

.conversation-icon {
  width: 24px;
  height: 24px;
  margin-right: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--primary-color);
  border-radius: 50%;
  color: white;
}

.conversation-info {
  flex: 1;
}

.conversation-title {
  font-weight: 500;
  color: var(--text-color);
}

.conversation-preview {
  font-size: 0.875rem;
  color: var(--text-muted);
}

/* Chat area */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--chat-bg);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  display: flex;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
}

.message-avatar {
  width: 40px;
  height: 40px;
  margin-right: 0.75rem;
}

.message-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.message-content {
  background-color: var(--message-bg);
  padding: 1rem;
  border-radius: 0.75rem;
  max-width: 100%;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.message-author {
  font-weight: 500;
  color: var(--text-color);
}

.message-timestamp {
  color: var(--text-muted);
}

.message-text {
  color: var(--text-color);
  line-height: 1.5;
}

.message-attachments {
  margin-top: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.attachment-item {
  max-width: 200px;
}

.attachment-item img {
  width: 100%;
  border-radius: 0.25rem;
}

.attachment-item a {
  display: block;
  padding: 0.5rem;
  background-color: var(--hover-color);
  border-radius: 0.25rem;
  text-decoration: none;
  color: var(--text-color);
}

/* Chat input */
.chat-input {
  padding: 1rem;
  background-color: var(--chat-input-bg);
  border-top: 1px solid var(--border-color);
}

.input-wrapper {
  display: flex;
  gap: 0.5rem;
  background-color: var(--input-bg);
  border-radius: 0.75rem;
  padding: 0.5rem;
}

.input-button {
  background: none;
  border: none;
  padding: 0.5rem;
  border-radius: 50%;
  cursor: pointer;
  transition: background-color 0.2s;
}

.input-button:hover {
  background-color: var(--hover-color);
}

.input-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

textarea {
  flex: 1;
  min-height: 40px;
  max-height: 150px;
  padding: 0.75rem;
  border: none;
  border-radius: 0.5rem;
  background-color: var(--input-bg);
  color: var(--text-color);
  resize: vertical;
  font-family: inherit;
}

/* Settings modal */
.settings-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: var(--modal-bg);
  padding: 2rem;
  border-radius: 0.75rem;
  width: 90%;
  max-width: 500px;
  position: relative;
}

.close-button {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  padding: 0.5rem;
  border-radius: 50%;
  cursor: pointer;
  transition: background-color 0.2s;
}

.close-button:hover {
  background-color: var(--hover-color);
}

.settings-section {
  margin-bottom: 1.5rem;
}

.setting-item {
  margin-bottom: 1rem;
}

.setting-item label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.setting-item input {
  width: auto;
}

.save-settings {
  display: block;
  width: 100%;
  padding: 0.75rem;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.save-settings:hover {
  background-color: var(--primary-dark);
}

/* Dark mode variables */
:root {
  --background-color: #f5f7fa;
  --text-color: #212529;
  --text-muted: #6c757d;
  --header-bg: #ffffff;
  --sidebar-bg: #ffffff;
  --chat-bg: #f5f7fa;
  --chat-input-bg: #ffffff;
  --input-bg: #f8f9fa;
  --message-bg: #e9ecef;
  --primary-color: #007bff;
  --primary-dark: #0056b3;
  --hover-color: #f8f9fa;
  --active-color: #e9ecef;
  --border-color: #dee2e6;
  --modal-bg: #ffffff;
}

:root.dark {
  --background-color: #1a1a1a;
  --text-color: #ffffff;
  --text-muted: #888888;
  --header-bg: #2a2a2a;
  --sidebar-bg: #2a2a2a;
  --chat-bg: #1a1a1a;
  --chat-input-bg: #2a2a2a;
  --input-bg: #3a3a3a;
  --message-bg: #4a4a4a;
  --primary-color: #007bff;
  --primary-dark: #0056b3;
  --hover-color: #3a3a3a;
  --active-color: #3a3a3a;
  --border-color: #4a4a4a;
  --modal-bg: #2a2a2a;
}

/* Responsive design */
@media (max-width: 768px) {
  .communication-header {
    padding: 0.75rem;
  }

  .sidebar {
    width: 200px;
  }

  .sidebar-collapsed {
    width: 40px;
  }

  .chat-messages {
    padding: 1rem;
  }

  .chat-input {
    padding: 0.75rem;
  }

  .input-wrapper {
    padding: 0.25rem;
  }

  .message-content {
    padding: 0.75rem;
  }

  .message-header {
    font-size: 0.75rem;
  }

  .message-text {
    font-size: 0.875rem;
  }
}

/* Style pour l'état de la connexion */
.internet-status {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  background-color: var(--status-bg);
  color: var(--status-text);
  font-size: 0.875rem;
  z-index: 1000;
}

.internet-status.connected {
  --status-bg: #d4edda;
  --status-text: #155724;
}

.internet-status.disconnected {
  --status-bg: #f8d7da;
  --status-text: #721c24;
}
</style>
