// Routes pour Vue Router

// Composant Vision
Vue.component('vision-panel', {
    template: `
        <div>
            <v-card class="mb-4">
                <v-card-title>
                    Traitement Visuel
                    <v-spacer></v-spacer>
                    <v-btn color="primary" @click="captureImage">
                        <v-icon left>mdi-camera</v-icon>
                        Capturer
                    </v-btn>
                    <v-btn color="secondary" class="ml-2" @click="uploadImage">
                        <v-icon left>mdi-upload</v-icon>
                        Importer
                    </v-btn>
                </v-card-title>
                <v-card-text>
                    <v-row>
                        <v-col cols="12" md="6">
                            <v-card outlined>
                                <v-card-title>Image d'entrée</v-card-title>
                                <v-card-text class="text-center">
                                    <div v-if="!inputImage" class="pa-5 grey lighten-3 text-center">
                                        <v-icon size="64" color="grey">mdi-image</v-icon>
                                        <div class="mt-2">Aucune image</div>
                                    </div>
                                    <img v-else :src="inputImage" class="img-fluid" style="max-height: 300px;" />
                                </v-card-text>
                            </v-card>
                        </v-col>
                        <v-col cols="12" md="6">
                            <v-card outlined>
                                <v-card-title>Analyse</v-card-title>
                                <v-card-text>
                                    <div v-if="loading" class="text-center pa-5">
                                        <v-progress-circular indeterminate color="primary"></v-progress-circular>
                                        <div class="mt-2">Analyse en cours...</div>
                                    </div>
                                    <div v-else-if="!analysisResult" class="pa-5 grey lighten-3 text-center">
                                        <v-icon size="64" color="grey">mdi-magnify</v-icon>
                                        <div class="mt-2">Aucune analyse</div>
                                    </div>
                                    <div v-else>
                                        <v-list>
                                            <v-list-item v-for="(item, i) in analysisResult.items" :key="i">
                                                <v-list-item-icon>
                                                    <v-icon color="primary">mdi-check-circle</v-icon>
                                                </v-list-item-icon>
                                                <v-list-item-content>
                                                    <v-list-item-title>{{ item.label }}</v-list-item-title>
                                                    <v-list-item-subtitle>Confiance: {{ (item.confidence * 100).toFixed(2) }}%</v-list-item-subtitle>
                                                </v-list-item-content>
                                            </v-list-item>
                                        </v-list>
                                        <v-divider class="my-3"></v-divider>
                                        <div class="text-body-1 pa-2">
                                            <strong>Description:</strong> {{ analysisResult.description }}
                                        </div>
                                    </div>
                                </v-card-text>
                            </v-card>
                        </v-col>
                    </v-row>
                </v-card-text>
            </v-card>

            <v-card>
                <v-card-title>Historique des analyses</v-card-title>
                <v-card-text>
                    <v-data-table
                        :headers="historyHeaders"
                        :items="analysisHistory"
                        :items-per-page="5"
                        class="elevation-1"
                    >
                        <template v-slot:item.timestamp="{ item }">
                            {{ formatDate(item.timestamp) }}
                        </template>
                        <template v-slot:item.image="{ item }">
                            <v-img
                                :src="item.image"
                                max-height="50"
                                max-width="100"
                                contain
                            ></v-img>
                        </template>
                        <template v-slot:item.actions="{ item }">
                            <v-btn icon small @click="viewAnalysis(item)">
                                <v-icon small>mdi-eye</v-icon>
                            </v-btn>
                            <v-btn icon small @click="deleteAnalysis(item)">
                                <v-icon small>mdi-delete</v-icon>
                            </v-btn>
                        </template>
                    </v-data-table>
                </v-card-text>
            </v-card>

            <!-- Dialog pour l'upload d'image -->
            <v-dialog v-model="uploadDialog" max-width="500px">
                <v-card>
                    <v-card-title>Importer une image</v-card-title>
                    <v-card-text>
                        <v-file-input
                            v-model="imageFile"
                            accept="image/*"
                            label="Sélectionner une image"
                            prepend-icon="mdi-camera"
                            show-size
                            truncate-length="15"
                        ></v-file-input>
                    </v-card-text>
                    <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn color="primary" @click="processUploadedImage" :disabled="!imageFile">
                            Analyser
                        </v-btn>
                        <v-btn text @click="uploadDialog = false">Annuler</v-btn>
                    </v-card-actions>
                </v-card>
            </v-dialog>

            <!-- Dialog pour voir une analyse -->
            <v-dialog v-model="viewDialog" max-width="700px">
                <v-card>
                    <v-card-title>Détails de l'analyse</v-card-title>
                    <v-card-text>
                        <v-row>
                            <v-col cols="12" md="6">
                                <v-img :src="selectedAnalysis.image" contain max-height="300"></v-img>
                            </v-col>
                            <v-col cols="12" md="6">
                                <div class="text-body-1">
                                    <strong>Date:</strong> {{ formatDate(selectedAnalysis.timestamp) }}
                                </div>
                                <div class="text-body-1 mt-2">
                                    <strong>Description:</strong> {{ selectedAnalysis.description }}
                                </div>
                                <v-divider class="my-3"></v-divider>
                                <div class="text-body-1">
                                    <strong>Éléments détectés:</strong>
                                </div>
                                <v-list dense>
                                    <v-list-item v-for="(item, i) in selectedAnalysis.items" :key="i">
                                        <v-list-item-content>
                                            <v-list-item-title>{{ item.label }}</v-list-item-title>
                                            <v-list-item-subtitle>Confiance: {{ (item.confidence * 100).toFixed(2) }}%</v-list-item-subtitle>
                                        </v-list-item-content>
                                    </v-list-item>
                                </v-list>
                            </v-col>
                        </v-row>
                    </v-card-text>
                    <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn text @click="viewDialog = false">Fermer</v-btn>
                    </v-card-actions>
                </v-card>
            </v-dialog>
        </div>
    `,
    data() {
        return {
            inputImage: null,
            analysisResult: null,
            loading: false,
            uploadDialog: false,
            viewDialog: false,
            imageFile: null,
            selectedAnalysis: {
                image: '',
                timestamp: '',
                description: '',
                items: []
            },
            analysisHistory: [],
            historyHeaders: [
                { text: 'Date', value: 'timestamp' },
                { text: 'Image', value: 'image' },
                { text: 'Description', value: 'description' },
                { text: 'Actions', value: 'actions', sortable: false }
            ]
        };
    },
    mounted() {
        this.loadAnalysisHistory();
    },
    methods: {
        captureImage() {
            // Simuler une capture de caméra
            this.loading = true;
            setTimeout(() => {
                this.inputImage = '/static/img/sample_capture.jpg';
                this.analyzeImage();
            }, 1000);
        },
        uploadImage() {
            this.uploadDialog = true;
        },
        processUploadedImage() {
            if (!this.imageFile) return;
            
            this.uploadDialog = false;
            this.loading = true;
            
            // Créer une URL pour l'image
            const reader = new FileReader();
            reader.onload = (e) => {
                this.inputImage = e.target.result;
                this.analyzeImage();
            };
            reader.readAsDataURL(this.imageFile);
        },
        analyzeImage() {
            // Simuler une analyse d'image
            setTimeout(() => {
                this.analysisResult = {
                    description: "Une scène extérieure avec plusieurs personnes et des bâtiments.",
                    items: [
                        { label: "Personne", confidence: 0.98 },
                        { label: "Bâtiment", confidence: 0.95 },
                        { label: "Arbre", confidence: 0.87 },
                        { label: "Voiture", confidence: 0.76 }
                    ]
                };
                
                // Ajouter à l'historique
                this.analysisHistory.unshift({
                    id: Date.now(),
                    timestamp: new Date().toISOString(),
                    image: this.inputImage,
                    description: this.analysisResult.description,
                    items: this.analysisResult.items
                });
                
                this.loading = false;
            }, 2000);
        },
        loadAnalysisHistory() {
            // Simuler le chargement de l'historique
            api.getVisionHistory()
                .then(response => {
                    this.analysisHistory = response.data.history;
                })
                .catch(error => {
                    console.error('Erreur lors du chargement de l\'historique:', error);
                });
        },
        viewAnalysis(item) {
            this.selectedAnalysis = item;
            this.viewDialog = true;
        },
        deleteAnalysis(item) {
            const index = this.analysisHistory.findIndex(a => a.id === item.id);
            if (index !== -1) {
                this.analysisHistory.splice(index, 1);
                this.$root.showSnackbar('Analyse supprimée', 'success');
            }
        },
        formatDate(timestamp) {
            return moment(timestamp).format('DD/MM/YYYY HH:mm:ss');
        }
    }
});

// Composant Audio
Vue.component('audio-panel', {
    template: `
        <div>
            <v-card class="mb-4">
                <v-card-title>
                    Traitement Audio
                    <v-spacer></v-spacer>
                    <v-btn color="primary" @click="startRecording" :disabled="isRecording">
                        <v-icon left>mdi-microphone</v-icon>
                        Enregistrer
                    </v-btn>
                    <v-btn color="error" class="ml-2" @click="stopRecording" :disabled="!isRecording">
                        <v-icon left>mdi-stop</v-icon>
                        Arrêter
                    </v-btn>
                </v-card-title>
                <v-card-text>
                    <v-row>
                        <v-col cols="12" md="6">
                            <v-card outlined>
                                <v-card-title>État de l'enregistrement</v-card-title>
                                <v-card-text class="text-center">
                                    <div v-if="isRecording" class="pa-5">
                                        <v-progress-circular indeterminate color="red" size="64"></v-progress-circular>
                                        <div class="mt-2">Enregistrement en cours...</div>
                                        <div class="mt-2">Durée: {{ recordingTime }} secondes</div>
                                    </div>
                                    <div v-else-if="audioUrl" class="pa-5">
                                        <v-icon size="64" color="green">mdi-check-circle</v-icon>
                                        <div class="mt-2">Enregistrement terminé</div>
                                        <audio controls :src="audioUrl" class="mt-3 w-100"></audio>
                                    </div>
                                    <div v-else class="pa-5 grey lighten-3">
                                        <v-icon size="64" color="grey">mdi-microphone-off</v-icon>
                                        <div class="mt-2">Aucun enregistrement</div>
                                    </div>
                                </v-card-text>
                            </v-card>
                        </v-col>
                        <v-col cols="12" md="6">
                            <v-card outlined>
                                <v-card-title>Transcription</v-card-title>
                                <v-card-text>
                                    <div v-if="transcribing" class="text-center pa-5">
                                        <v-progress-circular indeterminate color="primary"></v-progress-circular>
                                        <div class="mt-2">Transcription en cours...</div>
                                    </div>
                                    <div v-else-if="!transcription" class="pa-5 grey lighten-3 text-center">
                                        <v-icon size="64" color="grey">mdi-text</v-icon>
                                        <div class="mt-2">Aucune transcription</div>
                                    </div>
                                    <div v-else class="pa-3">
                                        <div class="text-body-1">{{ transcription }}</div>
                                    </div>
                                </v-card-text>
                            </v-card>
                        </v-col>
                    </v-row>
                </v-card-text>
            </v-card>

            <v-card>
                <v-card-title>Historique des transcriptions</v-card-title>
                <v-card-text>
                    <v-data-table
                        :headers="historyHeaders"
                        :items="transcriptionHistory"
                        :items-per-page="5"
                        class="elevation-1"
                    >
                        <template v-slot:item.timestamp="{ item }">
                            {{ formatDate(item.timestamp) }}
                        </template>
                        <template v-slot:item.audio="{ item }">
                            <audio controls :src="item.audio" style="height: 30px;"></audio>
                        </template>
                        <template v-slot:item.actions="{ item }">
                            <v-btn icon small @click="deleteTranscription(item)">
                                <v-icon small>mdi-delete</v-icon>
                            </v-btn>
                        </template>
                    </v-data-table>
                </v-card-text>
            </v-card>
        </div>
    `,
    data() {
        return {
            isRecording: false,
            recordingTime: 0,
            recordingInterval: null,
            audioUrl: null,
            transcription: null,
            transcribing: false,
            transcriptionHistory: [],
            historyHeaders: [
                { text: 'Date', value: 'timestamp' },
                { text: 'Audio', value: 'audio' },
                { text: 'Transcription', value: 'transcription' },
                { text: 'Actions', value: 'actions', sortable: false }
            ]
        };
    },
    mounted() {
        this.loadTranscriptionHistory();
    },
    methods: {
        startRecording() {
            this.isRecording = true;
            this.recordingTime = 0;
            this.audioUrl = null;
            this.transcription = null;
            
            // Simuler un enregistrement
            this.recordingInterval = setInterval(() => {
                this.recordingTime++;
            }, 1000);
        },
        stopRecording() {
            this.isRecording = false;
            clearInterval(this.recordingInterval);
            
            // Simuler un fichier audio
            this.audioUrl = '/static/audio/sample_recording.mp3';
            
            // Simuler une transcription
            this.transcribeAudio();
        },
        transcribeAudio() {
            this.transcribing = true;
            
            // Simuler une transcription
            setTimeout(() => {
                this.transcription = "Ceci est un exemple de transcription audio générée par le système Polyad. Le système est capable de reconnaître la parole et de la convertir en texte avec une grande précision.";
                this.transcribing = false;
                
                // Ajouter à l'historique
                this.transcriptionHistory.unshift({
                    id: Date.now(),
                    timestamp: new Date().toISOString(),
                    audio: this.audioUrl,
                    transcription: this.transcription
                });
            }, 2000);
        },
        loadTranscriptionHistory() {
            // Simuler le chargement de l'historique
            api.getAudioHistory()
                .then(response => {
                    this.transcriptionHistory = response.data.history;
                })
                .catch(error => {
                    console.error('Erreur lors du chargement de l\'historique:', error);
                });
        },
        deleteTranscription(item) {
            const index = this.transcriptionHistory.findIndex(t => t.id === item.id);
            if (index !== -1) {
                this.transcriptionHistory.splice(index, 1);
                this.$root.showSnackbar('Transcription supprimée', 'success');
            }
        },
        formatDate(timestamp) {
            return moment(timestamp).format('DD/MM/YYYY HH:mm:ss');
        }
    }
});

// Configuration des routes
const routes = [
    { path: '/', component: Vue.component('dashboard-home') },
    { path: '/vision', component: Vue.component('vision-panel') },
    { path: '/audio', component: Vue.component('audio-panel') },
    { 
        path: '/learning', 
        component: {
            template: '<div><h2>Apprentissage</h2><p>Fonctionnalité en développement</p></div>'
        } 
    },
    { 
        path: '/settings', 
        component: {
            template: '<div><h2>Paramètres</h2><p>Fonctionnalité en développement</p></div>'
        } 
    }
];

const router = new VueRouter({
    routes
});
