# Étage de construction
FROM python:3.12-slim as builder

# Configuration de l'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Créer un utilisateur non-root
RUN useradd --create-home --shell /bin/bash appuser

# Copier les fichiers nécessaires
COPY requirements.txt pyproject.toml setup.py /app/
COPY polyad/ /app/polyad/

# Installer les dépendances avec pip
RUN pip install --user --no-cache-dir -r /app/requirements.txt

# Étage final pour le backend
FROM python:3.12-slim as backend

# Configuration de l'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Créer un utilisateur non-root
RUN useradd --create-home --shell /bin/bash appuser

# Copier les fichiers nécessaires
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app/ /home/appuser/app

# Définir le répertoire de travail
WORKDIR /home/appuser/app

# Donner les droits à l'utilisateur
RUN chown -R appuser:appuser /home/appuser

# Exposer les ports
EXPOSE 8000

# Définir l'utilisateur
USER appuser

# Commande par défaut
CMD ["python", "-m", "polyad"]

# Étage final pour le dashboard
FROM python:3.12-slim as dashboard

# Configuration de l'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Créer un utilisateur non-root
RUN useradd --create-home --shell /bin/bash appuser

# Copier les fichiers nécessaires
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app/ /home/appuser/app

# Définir le répertoire de travail
WORKDIR /home/appuser/app

# Donner les droits à l'utilisateur
RUN chown -R appuser:appuser /home/appuser

# Exposer les ports
EXPOSE 8001

# Définir l'utilisateur
USER appuser

# Commande par défaut
CMD ["python", "-m", "dashboard"]
