import axios from 'axios'

const agentService = {
  // Configuration de base pour les requêtes
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:5000/api',

  // Vérifier la connexion Internet
  checkInternetConnection: async () => {
    try {
      const response = await axios.get('https://api.ipify.org?format=json')
      return {
        connected: true,
        publicIP: response.data.ip,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      console.error('Erreur de connexion Internet:', error)
      return {
        connected: false,
        error: error.message
      }
    }
  },

  // Envoyer une requête à l'agent
  sendRequest: async (data) => {
    try {
      const response = await axios.post(`${this.baseURL}/agent`, data)
      return response.data
    } catch (error) {
      console.error('Erreur lors de l\'envoi de la requête:', error)
      throw error
    }
  },

  // Obtenir les informations de l'agent
  getAgentInfo: async () => {
    try {
      const response = await axios.get(`${this.baseURL}/agent/info`)
      return response.data
    } catch (error) {
      console.error('Erreur lors de la récupération des informations:', error)
      throw error
    }
  },

  // Mettre à jour les paramètres de l'agent
  updateAgentSettings: async (settings) => {
    try {
      const response = await axios.put(`${this.baseURL}/agent/settings`, settings)
      return response.data
    } catch (error) {
      console.error('Erreur lors de la mise à jour des paramètres:', error)
      throw error
    }
  }
}

export default agentService
