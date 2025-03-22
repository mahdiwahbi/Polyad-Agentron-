// API client pour Polyad
const api = {
    // Configuration
    baseUrl: '/api',
    token: localStorage.getItem('auth_token'),
    
    // Méthodes d'authentification
    login(username, password) {
        return axios.post(`${this.baseUrl}/auth/login`, { username, password })
            .then(response => {
                this.token = response.data.access_token;
                localStorage.setItem('auth_token', this.token);
                return response;
            });
    },
    
    logout() {
        this.token = null;
        localStorage.removeItem('auth_token');
        return Promise.resolve();
    },
    
    // Méthodes utilitaires
    getAuthHeaders() {
        return {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        };
    },
    
    // Méthodes API
    getSystemStatus() {
        return axios.get(`${this.baseUrl}/system/status`, this.getAuthHeaders());
    },
    
    getActivityLog() {
        return axios.get(`${this.baseUrl}/system/activity`, this.getAuthHeaders());
    },
    
    startAgent() {
        return axios.post(`${this.baseUrl}/agent/start`, {}, this.getAuthHeaders());
    },
    
    stopAgent() {
        return axios.post(`${this.baseUrl}/agent/stop`, {}, this.getAuthHeaders());
    },
    
    getAgentCapabilities() {
        return axios.get(`${this.baseUrl}/agent/capabilities`, this.getAuthHeaders());
    },
    
    getAgentPerformance() {
        return axios.get(`${this.baseUrl}/agent/performance`, this.getAuthHeaders());
    },
    
    // Vision API
    processImage(imageData) {
        const formData = new FormData();
        formData.append('image', imageData);
        
        return axios.post(`${this.baseUrl}/vision/process`, formData, {
            ...this.getAuthHeaders(),
            headers: {
                ...this.getAuthHeaders().headers,
                'Content-Type': 'multipart/form-data'
            }
        });
    },
    
    getVisionHistory() {
        return axios.get(`${this.baseUrl}/vision/history`, this.getAuthHeaders());
    },
    
    // Audio API
    processAudio(audioData) {
        const formData = new FormData();
        formData.append('audio', audioData);
        
        return axios.post(`${this.baseUrl}/audio/process`, formData, {
            ...this.getAuthHeaders(),
            headers: {
                ...this.getAuthHeaders().headers,
                'Content-Type': 'multipart/form-data'
            }
        });
    },
    
    getAudioHistory() {
        return axios.get(`${this.baseUrl}/audio/history`, this.getAuthHeaders());
    },
    
    // Learning API
    learnFromExperience(data) {
        return axios.post(`${this.baseUrl}/learning/experience`, data, this.getAuthHeaders());
    },
    
    getLearningStatus() {
        return axios.get(`${this.baseUrl}/learning/status`, this.getAuthHeaders());
    },
    
    // Actions API
    executeAction(action) {
        return axios.post(`${this.baseUrl}/action/execute`, action, this.getAuthHeaders());
    },
    
    getActionHistory() {
        return axios.get(`${this.baseUrl}/action/history`, this.getAuthHeaders());
    },
    
    // Simuler des données pour le développement
    simulateData: {
        getSystemStatus() {
            return Promise.resolve({
                data: {
                    status: 'ok',
                    system: {
                        cpu: {
                            usage: 45.2,
                            cores: 8
                        },
                        memory: {
                            total: 16384,
                            used: 8192,
                            percent: 50
                        },
                        disk: {
                            total: 512000,
                            used: 256000,
                            percent: 50
                        },
                        temperature: 42,
                        history: {
                            cpu: [30, 35, 40, 45, 50, 48, 45, 42, 40, 45],
                            memory: [45, 48, 50, 52, 55, 53, 50, 48, 50, 50]
                        }
                    },
                    agent: {
                        initialized: true,
                        capabilities: {
                            'Vision': true,
                            'Audio': true,
                            'Apprentissage': true,
                            'Actions': true
                        },
                        performance: {
                            accuracy: 85,
                            speed: 78,
                            efficiency: 82,
                            learning: 90,
                            adaptation: 75
                        }
                    },
                    timestamp: new Date().toISOString()
                }
            });
        },
        
        getActivityLog() {
            const activities = [];
            for (let i = 0; i < 10; i++) {
                activities.push({
                    id: i,
                    timestamp: new Date(Date.now() - i * 600000).toISOString(),
                    title: `Activité ${i + 1}`,
                    text: `Description de l'activité ${i + 1}`,
                    level: i % 3 === 0 ? 'info' : (i % 3 === 1 ? 'warning' : 'error')
                });
            }
            
            return Promise.resolve({
                data: {
                    activities
                }
            });
        },
        
        getVisionHistory() {
            const history = [];
            for (let i = 0; i < 5; i++) {
                history.push({
                    id: i,
                    timestamp: new Date(Date.now() - i * 3600000).toISOString(),
                    image: '/static/img/sample_capture.jpg',
                    description: `Description de l'image ${i + 1}`,
                    items: [
                        { label: "Personne", confidence: 0.98 - (i * 0.02) },
                        { label: "Bâtiment", confidence: 0.95 - (i * 0.02) }
                    ]
                });
            }
            
            return Promise.resolve({
                data: {
                    history
                }
            });
        },
        
        getAudioHistory() {
            const history = [];
            for (let i = 0; i < 5; i++) {
                history.push({
                    id: i,
                    timestamp: new Date(Date.now() - i * 3600000).toISOString(),
                    audio: '/static/audio/sample_recording.mp3',
                    transcription: `Exemple de transcription ${i + 1}. Ceci est un texte généré pour simuler une transcription audio.`
                });
            }
            
            return Promise.resolve({
                data: {
                    history
                }
            });
        }
    }
};

// En mode développement, utiliser les données simulées
const isDev = true;
if (isDev) {
    api.getSystemStatus = api.simulateData.getSystemStatus;
    api.getActivityLog = api.simulateData.getActivityLog;
    api.getVisionHistory = api.simulateData.getVisionHistory;
    api.getAudioHistory = api.simulateData.getAudioHistory;
}
