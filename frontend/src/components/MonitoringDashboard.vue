<template>
  <div class="monitoring-dashboard">
    <!-- En-tête -->
    <div class="dashboard-header">
      <h2>Monitoring</h2>
      <div class="status-indicator">
        <div :class="['status-dot', healthStatus]">
          <i class="fas fa-circle"></i>
        </div>
        <span>{{ healthStatusDisplay }}</span>
      </div>
    </div>

    <!-- Grille de métriques -->
    <div class="metrics-grid">
      <!-- Métriques de performance -->
      <div class="metric-card">
        <h3>Performance</h3>
        <div class="metric-row">
          <div class="metric-item">
            <span class="metric-label">Temps de réponse</span>
            <span class="metric-value">{{ formatTime(responseTime) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Débit</span>
            <span class="metric-value">{{ throughput }} req/min</span>
          </div>
        </div>
      </div>

      <!-- Métriques de ressources -->
      <div class="metric-card">
        <h3>Ressources</h3>
        <div class="metric-row">
          <div class="metric-item">
            <span class="metric-label">CPU</span>
            <span class="metric-value">{{ cpuUsage }}%</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Mémoire</span>
            <span class="metric-value">{{ memoryUsage }}%</span>
          </div>
        </div>
      </div>

      <!-- Métriques d'erreurs -->
      <div class="metric-card">
        <h3>Erreurs</h3>
        <div class="metric-row">
          <div class="metric-item">
            <span class="metric-label">Taux d'erreur</span>
            <span class="metric-value">{{ errorRate }}%</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Latence</span>
            <span class="metric-value">{{ latency }}ms</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Graphiques -->
    <div class="charts-section">
      <div class="chart-card">
        <h3>Utilisation des ressources</h3>
        <div id="resources-chart"></div>
      </div>
      
      <div class="chart-card">
        <h3>Performance</h3>
        <div id="performance-chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import ApexCharts from 'apexcharts'

// Données réactives
const responseTime = ref(0)
const throughput = ref(0)
const cpuUsage = ref(0)
const memoryUsage = ref(0)
const errorRate = ref(0)
const latency = ref(0)

// Statut de santé
const healthStatus = computed(() => {
  if (errorRate.value > 5 || responseTime.value > 5000) {
    return 'critical'
  }
  if (errorRate.value > 1 || responseTime.value > 2000) {
    return 'warning'
  }
  return 'healthy'
})

const healthStatusDisplay = computed(() => {
  return healthStatus.value.charAt(0).toUpperCase() + healthStatus.value.slice(1)
})

// Fonction pour formater le temps
const formatTime = (ms) => {
  const seconds = Math.floor(ms / 1000)
  return `${seconds}s`
}

// Initialisation des graphiques
onMounted(() => {
  // Graphique des ressources
  const resourcesChart = new ApexCharts(document.querySelector('#resources-chart'), {
    series: [{
      name: 'CPU',
      data: [cpuUsage.value]
    }, {
      name: 'Mémoire',
      data: [memoryUsage.value]
    }],
    chart: {
      type: 'line',
      height: 350
    },
    xaxis: {
      type: 'datetime'
    },
    yaxis: {
      min: 0,
      max: 100
    }
  })

  // Graphique de performance
  const performanceChart = new ApexCharts(document.querySelector('#performance-chart'), {
    series: [{
      name: 'Temps de réponse',
      data: [responseTime.value]
    }, {
      name: 'Débit',
      data: [throughput.value]
    }],
    chart: {
      type: 'line',
      height: 350
    },
    xaxis: {
      type: 'datetime'
    }
  })

  // Initialiser les graphiques
  resourcesChart.render()
  performanceChart.render()

  // Mettre à jour les données toutes les secondes
  setInterval(() => {
    // Simuler la mise à jour des données
    cpuUsage.value = Math.floor(Math.random() * 100)
    memoryUsage.value = Math.floor(Math.random() * 100)
    responseTime.value = Math.floor(Math.random() * 5000)
    throughput.value = Math.floor(Math.random() * 100)
    errorRate.value = Math.floor(Math.random() * 5)
    latency.value = Math.floor(Math.random() * 500)

    // Mettre à jour les graphiques
    resourcesChart.updateSeries([
      { data: [cpuUsage.value] },
      { data: [memoryUsage.value] }
    ])

    performanceChart.updateSeries([
      { data: [responseTime.value] },
      { data: [throughput.value] }
    ])
  }, 1000)
})
</script>

<style scoped>
.monitoring-dashboard {
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  font-size: 1rem;
  color: #6c757d;
}

.status-dot.healthy {
  color: #28a745;
}

.status-dot.warning {
  color: #ffc107;
}

.status-dot.critical {
  color: #dc3545;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.metric-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.metric-card h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.metric-row {
  display: flex;
  gap: 20px;
}

.metric-item {
  flex: 1;
}

.metric-label {
  display: block;
  color: #6c757d;
  font-size: 0.875rem;
}

.metric-value {
  display: block;
  font-size: 1.25rem;
  font-weight: bold;
  color: #333;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
}

.chart-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-card h3 {
  margin: 0 0 20px 0;
  color: #333;
}
</style>
