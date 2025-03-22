// Application principale du dashboard Polyad

new Vue({
    el: '#app',
    router,
    vuetify: new Vuetify({
        theme: {
            dark: false,
            themes: {
                light: {
                    primary: '#1976D2',
                    secondary: '#424242',
                    accent: '#82B1FF',
                    error: '#FF5252',
                    info: '#2196F3',
                    success: '#4CAF50',
                    warning: '#FFC107'
                },
                dark: {
                    primary: '#2196F3',
                    secondary: '#757575',
                    accent: '#FF4081',
                    error: '#FF5252',
                    info: '#2196F3',
                    success: '#4CAF50',
                    warning: '#FFC107'
                }
            }
        }
    }),
    data: {
        drawer: true,
        menuItems: [
            { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/' },
            { title: 'Vision', icon: 'mdi-eye', to: '/vision' },
            { title: 'Audio', icon: 'mdi-microphone', to: '/audio' },
            { title: 'Apprentissage', icon: 'mdi-school', to: '/learning' },
            { title: 'Paramètres', icon: 'mdi-cog', to: '/settings' }
        ],
        darkMode: false,
        refreshInterval: 5000,
        refreshIntervals: [
            { text: '1 seconde', value: 1000 },
            { text: '5 secondes', value: 5000 },
            { text: '10 secondes', value: 10000 },
            { text: '30 secondes', value: 30000 },
            { text: '1 minute', value: 60000 }
        ],
        settingsDialog: false,
        snackbar: {
            show: false,
            text: '',
            color: 'info',
            timeout: 3000
        },
        isAuthenticated: !!localStorage.getItem('auth_token')
    },
    created() {
        // Vérifier l'authentification
        if (!this.isAuthenticated && window.location.pathname !== '/login') {
            // Rediriger vers la page de login
            // window.location.href = '/login';
        }
        
        // Charger les préférences utilisateur
        this.loadUserPreferences();
    },
    methods: {
        refreshData() {
            // Émettre un événement global pour rafraîchir les données
            this.$root.$emit('refresh-data');
        },
        showSettings() {
            this.settingsDialog = true;
        },
        saveSettings() {
            this.settingsDialog = false;
            
            // Appliquer le thème
            this.$vuetify.theme.dark = this.darkMode;
            
            // Sauvegarder les préférences
            localStorage.setItem('darkMode', this.darkMode);
            localStorage.setItem('refreshInterval', this.refreshInterval);
            
            this.showSnackbar('Paramètres enregistrés', 'success');
        },
        loadUserPreferences() {
            // Charger les préférences depuis le stockage local
            const darkMode = localStorage.getItem('darkMode');
            if (darkMode !== null) {
                this.darkMode = darkMode === 'true';
                this.$vuetify.theme.dark = this.darkMode;
            }
            
            const refreshInterval = localStorage.getItem('refreshInterval');
            if (refreshInterval !== null) {
                this.refreshInterval = parseInt(refreshInterval);
            }
        },
        showSnackbar(text, color = 'info', timeout = 3000) {
            this.snackbar = {
                show: true,
                text,
                color,
                timeout
            };
        },
        logout() {
            // Déconnexion
            api.logout()
                .then(() => {
                    this.isAuthenticated = false;
                    this.showSnackbar('Déconnexion réussie', 'success');
                    // Rediriger vers la page de login
                    // window.location.href = '/login';
                })
                .catch(error => {
                    console.error('Erreur lors de la déconnexion:', error);
                    this.showSnackbar('Erreur lors de la déconnexion', 'error');
                });
        }
    }
});
