# Documentation de Production

## Prérequis

- Docker et Docker Compose
- AWS CLI configuré
- Accès au cluster EKS
- Variables d'environnement configurées

## Configuration de l'Environnement

1. Créer les secrets nécessaires :
```bash
# Variables d'environnement
export DOCKERHUB_USERNAME="your-username"
export DOCKERHUB_TOKEN="your-token"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="eu-west-1"
export SLACK_WEBHOOK_URL="your-webhook-url"

# Configurer AWS CLI
aws configure
```

2. Configurer le cluster EKS :
```bash
aws eks update-kubeconfig --name polyad-cluster --region $AWS_REGION
```

## Déploiement

1. Construire les images Docker :
```bash
docker-compose build
```

2. Pousser les images sur Docker Hub :
```bash
docker-compose push
```

3. Déployer sur EKS :
```bash
kubectl apply -f kubernetes/production/
```

## Monitoring

1. Accéder à Prometheus :
```
http://localhost:9090
```

2. Accéder à Grafana :
```
http://localhost:3000
```

3. Vérifier les métriques :
```bash
kubectl get pods
kubectl logs -l app=polyad --tail=100
```

## Sauvegarde

1. Sauvegarde automatique :
- Intervalle : 24h
- Retention : 7 jours
- Stockage : S3 (bucket: polyad-backups)

2. Sauvegarde manuelle :
```bash
python -m polyad.backup
```

## Sécurité

1. Authentification :
- JWT avec secret configuré
- Session timeout : 1h
- Password policy stricte

2. Rate limiting :
- 60 requêtes par minute
- Limite de burst : 10 requêtes

3. Sécurité des données :
- Chiffrement des backups
- Audit des accès
- Logging sécurisé

## Maintenance

1. Mise à jour des images :
```bash
docker-compose pull
```

2. Redémarrage des services :
```bash
kubectl rollout restart deployment/polyad
```

3. Vérification de l'état :
```bash
kubectl get pods
kubectl get services
kubectl get deployments
```

## Dépannage

1. Vérifier les logs :
```bash
kubectl logs -l app=polyad --tail=100
```

2. Vérifier les métriques :
```bash
kubectl get metrics
```

3. Vérifier les événements :
```bash
kubectl get events
```

## Alertes

1. Configuration des alertes :
- CPU > 80%
- Mémoire > 90%
- Disque > 90%
- Temps de réponse > 2s

2. Notifications :
- Slack
- Email
- PagerDuty
