# Performance et Optimisations

## Métriques de Performance

### Vitesse
- CPU: 3-5 tokens/s
- GPU Metal: ~6 tokens/s
- Cloud: instantané

### Utilisation Mémoire
- q4_0: 8-10 Go RAM
- q2_K: 6-8 Go RAM
- Avec outils: 10-12 Go RAM

### Temps d'Exécution
- Cas complexe: 5-10 minutes

## Optimisations

### Gestion des Ressources
- Quantification dynamique (q4_0 ↔ q2_K)
- Bascule CPU/GPU via Metal
- Monitoring avec psutil et smc
- Pause thermique (30-60s si >80°C)
- Désactivation swap macOS

### Seuils et Limites
- CPU: max 80%
- Température: max 80°C
- RAM libre: min 1 Go
- Threads: 6 (1 par cœur)
