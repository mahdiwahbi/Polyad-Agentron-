<template>
  <div class="chat-container">
    <!-- Historique des messages -->
    <div class="message-history">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.type]">
        <div class="message-content">
          <div class="message-text">{{ message.text }}</div>
          <div class="message-meta">
            <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
            <span v-if="message.type === 'user'" 
                  class="status">
              {{ message.status }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Zone de saisie -->
    <div class="input-area">
      <div class="input-wrapper">
        <textarea v-model="inputMessage" 
                  @keypress.enter.prevent="sendMessage" 
                  placeholder="Tapez votre message ici..."
                  ref="messageInput"></textarea>
        
        <div class="input-actions">
          <button class="action-button" 
                  @click="attachFile">
            <i class="fas fa-paperclip"></i>
          </button>
          <button class="action-button" 
                  @click="sendMessage" 
                  :disabled="!inputMessage.trim()">
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { format } from 'date-fns'
import fr from 'date-fns/locale/fr'

const messages = ref([
  {
    type: 'assistant',
    text: 'Bonjour ! Comment puis-je vous aider aujourd'hui ?',
    timestamp: new Date()
  }
])

const inputMessage = ref('')
const messageInput = ref(null)

// Fonction pour formater l'heure
const formatTime = (timestamp) => {
  return format(new Date(timestamp), 'HH:mm', { locale: fr })
}

// Fonction pour envoyer un message
const sendMessage = () => {
  if (!inputMessage.value.trim()) return
  
  // Ajouter le message de l'utilisateur
  messages.value.push({
    type: 'user',
    text: inputMessage.value,
    timestamp: new Date(),
    status: 'En cours...'
  })
  
  // Simuler une réponse de l'assistant
  setTimeout(() => {
    messages.value.push({
      type: 'assistant',
      text: 'Je vais traiter votre demande...',
      timestamp: new Date()
    })
    inputMessage.value = ''
    messageInput.value.focus()
  }, 500)
}

// Fonction pour attacher un fichier
const attachFile = () => {
  // À implémenter
}

// Scroller automatiquement vers le bas
const scrollToBottom = () => {
  const container = document.querySelector('.message-history')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

// Scroller vers le bas quand de nouveaux messages arrivent
watch(messages, scrollToBottom)

// Scroller vers le bas au chargement
onMounted(scrollToBottom)
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8f9fa;
}

.message-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  max-width: 80%;
  margin: 0 auto;
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message.user {
  align-self: flex-end;
  background: #007bff;
  color: white;
}

.message.assistant {
  align-self: flex-start;
  background: #ffffff;
  border: 1px solid #e9ecef;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-text {
  font-size: 1rem;
  line-height: 1.5;
}

.message-meta {
  font-size: 0.75rem;
  color: #6c757d;
  display: flex;
  justify-content: space-between;
}

.input-area {
  padding: 20px;
  background: white;
  border-top: 1px solid #e9ecef;
}

.input-wrapper {
  display: flex;
  gap: 10px;
}

textarea {
  flex: 1;
  min-height: 40px;
  max-height: 150px;
  padding: 12px;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  resize: vertical;
  font-family: inherit;
}

.input-actions {
  display: flex;
  gap: 10px;
}

.action-button {
  background: none;
  border: none;
  padding: 8px;
  border-radius: 50%;
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-button:hover {
  background-color: #f8f9fa;
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
