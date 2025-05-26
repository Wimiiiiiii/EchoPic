FROM python:3.8-slim

WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python avec les versions spécifiques
RUN pip install --no-cache-dir -r requirements.txt

# Création des dossiers nécessaires
RUN mkdir -p /app/static/uploads \
    /app/static/rp_curves \
# Copie de l'application
COPY . /app/

# Ajout du répertoire de travail au PYTHONPATH
ENV PYTHONPATH=/app

# Variables d'environnement
ENV FLASK_APP=app/app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1


# Exposition du port
EXPOSE 5000

# Commande de démarrage avec Gunicorn optimisé pour la production
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--worker-class", "gevent", \
     "--chdir", "/app", \
     "app.app:app"] 