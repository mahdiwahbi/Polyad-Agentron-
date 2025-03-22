// Composants Vue.js pour le dashboard Polyad

// Composant Dashboard principal
Vue.component('dashboard-home', {
    template: `
        <div>
            <v-row>
                <v-col cols="12" md="6" lg="3" v-for="(stat, index) in systemStats" :key="index">
                    <v-card :color="stat.color" dark>
                        <v-card-title class="headline">{{ stat.value }}{{ stat.unit }}</v-card-title>
                        <v-card-subtitle>{{ stat.title }}</v-card-subtitle>
                        <v-card-text>
                            <v-sparkline
                                :value="stat.history"
                                :gradient="stat.gradient"
                                :smooth="16"
                                auto-draw
                            ></v-sparkline>
                        </v-card-text>
                    </v-card>
                </v-col>
            </v-row>

            <v-row>
                <v-col cols="12" md="8">
                    <v-card>
                        <v-card-title>
                            Activité du système
                            <v-spacer></v-spacer>
                            <v-btn icon @click="refreshSystemActivity">
                                <v-icon>mdi-refresh</v-icon>
                            </v-btn>
                        </v-card-title>
                        <v-card-text>
                            <canvas id="systemActivityChart" height="250"></canvas>
                        </v-card-text>
                    </v-card>
                </v-col>
                <v-col cols="12" md="4">
                    <v-card>
                        <v-card-title>
                            Journal d'activité
                            <v-spacer></v-spacer>
                            <v-btn icon @click="refreshActivityLog">
                                <v-icon>mdi-refresh</v-icon>
                            </v-btn>
                        </v-card-title>
                        <v-card-text style="height: 300px; overflow-y: auto;">
                            <v-timeline dense>
                                <v-timeline-item
                                    v-for="(activity, i) in activityLog"
                                    :key="i"
                                    :color="activity.color"
                                    small
                                >
                                    <div>
                                        <div class="font-weight-normal">
                                            <strong>{{ activity.title }}</strong>
                                        </div>
                                        <div>{{ activity.text }}</div>
                                        <div class="text-caption">
                                            {{ formatDate(activity.timestamp) }}
                                        </div>
                                    </div>
                                </v-timeline-item>
                            </v-timeline>
                        </v-card-text>
                    </v-card>
                </v-col>
            </v-row>

            <v-row>
                <v-col cols="12">
                    <v-card>
                        <v-card-title>
                            État de l'agent
                            <v-spacer></v-spacer>
                            <v-btn color="primary" @click="startAgent" :disabled="agentRunning">
                                Démarrer
                            </v-btn>
                            <v-btn color="error" class="ml-2" @click="stopAgent" :disabled="!agentRunning">
                                Arrêter
                            </v-btn>
                        </v-card-title>
                        <v-card-text>
                            <v-alert
                                :type="agentRunning ? 'success' : 'warning'"
                                border="left"
                                colored-border
                                elevation="2"
                                class="mb-4"
                            >
                                L'agent est actuellement {{ agentRunning ? 'actif' : 'inactif' }}
                            </v-alert>
                            
                            <v-row>
                                <v-col cols="12" md="6">
                                    <h3>Capacités</h3>
                                    <v-list>
                                        <v-list-item v-for="(value, key) in agentCapabilities" :key="key">
                                            <v-list-item-icon>
                                                <v-icon :color="value ? 'green' : 'grey'">
                                                    {{ value ? 'mdi-check-circle' : 'mdi-close-circle' }}
                                                </v-icon>
                                            </v-list-item-icon>
                                            <v-list-item-content>
                                                <v-list-item-title>{{ key }}</v-list-item-title>
                                            </v-list-item-content>
                                        </v-list-item>
                                    </v-list>
                                </v-col>
                                <v-col cols="12" md="6">
                                    <h3>Performance</h3>
                                    <canvas id="performanceChart" height="200"></canvas>
                                </v-col>
                            </v-row>
                        </v-card-text>
                    </v-card>
                </v-col>
            </v-row>
        </div>
    `,
    data() {
        return {
            systemStats: [
                {
                    title: 'CPU',
                    value: 0,
                    unit: '%',
                    color: 'indigo',
                    history: [],
                    gradient: ['#1E88E5', '#42A5F5']
                },
                {
                    title: 'Mémoire',
                    value: 0,
                    unit: '%',
                    color: 'teal',
                    history: [],
                    gradient: ['#00897B', '#4DB6AC']
                },
                {
                    title: 'Disque',
                    value: 0,
                    unit: '%',
                    color: 'purple',
                    history: [],
                    gradient: ['#8E24AA', '#BA68C8']
                },
                {
                    title: 'Température',
                    value: 0,
                    unit: '°C',
                    color: 'red',
                    history: [],
                    gradient: ['#E53935', '#EF5350']
                }
            ],
            activityLog: [],
            agentRunning: false,
            agentCapabilities: {
                'Vision': false,
                'Audio': false,
                'Apprentissage': false,
                'Actions': false
            },
            systemActivityChart: null,
            performanceChart: null
        };
    },
    mounted() {
        this.initCharts();
        this.fetchData();
        this.startAutoRefresh();
    },
    beforeDestroy() {
        this.stopAutoRefresh();
    },
    methods: {
        initCharts() {
            // Initialiser le graphique d'activité système
            const systemCtx = document.getElementById('systemActivityChart').getContext('2d');
            this.systemActivityChart = new Chart(systemCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'CPU',
                            data: [],
                            borderColor: '#1E88E5',
                            backgroundColor: 'rgba(30, 136, 229, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Mémoire',
                            data: [],
                            borderColor: '#00897B',
                            backgroundColor: 'rgba(0, 137, 123, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });

            // Initialiser le graphique de performance
            const perfCtx = document.getElementById('performanceChart').getContext('2d');
            this.performanceChart = new Chart(perfCtx, {
                type: 'radar',
                data: {
                    labels: ['Précision', 'Vitesse', 'Efficacité', 'Apprentissage', 'Adaptation'],
                    datasets: [{
                        label: 'Performance',
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderColor: 'rgb(255, 99, 132)',
                        pointBackgroundColor: 'rgb(255, 99, 132)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgb(255, 99, 132)'
                    }]
                },
                options: {
                    elements: {
                        line: {
                            borderWidth: 3
                        }
                    },
                    scales: {
                        r: {
                            angleLines: {
                                display: true
                            },
                            suggestedMin: 0,
                            suggestedMax: 100
                        }
                    }
                }
            });
        },
        fetchData() {
            // Récupérer les données système
            api.getSystemStatus()
                .then(response => {
                    const data = response.data;
                    
                    // Mettre à jour les statistiques système
                    this.systemStats[0].value = Math.round(data.system.cpu.usage);
                    this.systemStats[1].value = Math.round(data.system.memory.percent);
                    this.systemStats[2].value = Math.round(data.system.disk.percent);
                    this.systemStats[3].value = Math.round(data.system.temperature);
                    
                    // Ajouter à l'historique
                    this.systemStats.forEach(stat => {
                        stat.history.push(stat.value);
                        if (stat.history.length > 20) {
                            stat.history.shift();
                        }
                    });
                    
                    // Mettre à jour le graphique d'activité
                    const labels = Array.from({length: 10}, (_, i) => 
                        moment().subtract(9 - i, 'minutes').format('HH:mm')
                    );
                    
                    this.systemActivityChart.data.labels = labels;
                    this.systemActivityChart.data.datasets[0].data = data.system.history.cpu.slice(-10);
                    this.systemActivityChart.data.datasets[1].data = data.system.history.memory.slice(-10);
                    this.systemActivityChart.update();
                    
                    // Mettre à jour l'état de l'agent
                    this.agentRunning = data.agent.initialized;
                    this.agentCapabilities = data.agent.capabilities;
                    
                    // Mettre à jour le graphique de performance
                    if (data.agent.performance) {
                        this.performanceChart.data.datasets[0].data = [
                            data.agent.performance.accuracy || 0,
                            data.agent.performance.speed || 0,
                            data.agent.performance.efficiency || 0,
                            data.agent.performance.learning || 0,
                            data.agent.performance.adaptation || 0
                        ];
                        this.performanceChart.update();
                    }
                })
                .catch(error => {
                    console.error('Erreur lors de la récupération des données système:', error);
                });
                
            // Récupérer le journal d'activité
            api.getActivityLog()
                .then(response => {
                    this.activityLog = response.data.activities.map(activity => {
                        let color;
                        switch (activity.level) {
                            case 'info': color = 'blue'; break;
                            case 'warning': color = 'orange'; break;
                            case 'error': color = 'red'; break;
                            default: color = 'grey';
                        }
                        return {
                            ...activity,
                            color
                        };
                    });
                })
                .catch(error => {
                    console.error('Erreur lors de la récupération du journal d\'activité:', error);
                });
        },
        startAutoRefresh() {
            this.refreshInterval = setInterval(() => {
                this.fetchData();
            }, 5000); // Rafraîchir toutes les 5 secondes
        },
        stopAutoRefresh() {
            clearInterval(this.refreshInterval);
        },
        refreshSystemActivity() {
            this.fetchData();
        },
        refreshActivityLog() {
            api.getActivityLog()
                .then(response => {
                    this.activityLog = response.data.activities.map(activity => {
                        let color;
                        switch (activity.level) {
                            case 'info': color = 'blue'; break;
                            case 'warning': color = 'orange'; break;
                            case 'error': color = 'red'; break;
                            default: color = 'grey';
                        }
                        return {
                            ...activity,
                            color
                        };
                    });
                })
                .catch(error => {
                    console.error('Erreur lors de la récupération du journal d\'activité:', error);
                });
        },
        startAgent() {
            api.startAgent()
                .then(response => {
                    this.agentRunning = true;
                    this.$root.showSnackbar('Agent démarré avec succès', 'success');
                    this.fetchData();
                })
                .catch(error => {
                    console.error('Erreur lors du démarrage de l\'agent:', error);
                    this.$root.showSnackbar('Erreur lors du démarrage de l\'agent', 'error');
                });
        },
        stopAgent() {
            api.stopAgent()
                .then(response => {
                    this.agentRunning = false;
                    this.$root.showSnackbar('Agent arrêté avec succès', 'success');
                    this.fetchData();
                })
                .catch(error => {
                    console.error('Erreur lors de l\'arrêt de l\'agent:', error);
                    this.$root.showSnackbar('Erreur lors de l\'arrêt de l\'agent', 'error');
                });
        },
        formatDate(timestamp) {
            return moment(timestamp).format('DD/MM/YYYY HH:mm:ss');
        }
    }
});
