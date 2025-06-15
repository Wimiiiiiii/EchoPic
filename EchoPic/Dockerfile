FROM python:3.8-slim

# Installation des dépendances système minimales
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Création et configuration du répertoire de l'application
WORKDIR /app

# Copie des fichiers de l'application
COPY . /app/

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 5443

# Commande pour démarrer l'application
CMD ["python", "app/app.py"] 