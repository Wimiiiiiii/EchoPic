# Moteur de Recherche d'Images

Ce projet est une application web permettant de rechercher des images similaires en utilisant différents modèles d'indexation (MobileNet, ResNet50, ViT) et différentes méthodes de calcul de similarité.

## Prérequis

- Docker
- Docker Compose
- Python 3.8+
- Git

## Installation

1. Cloner le repository :
```bash
git clone <repository-url>
cd <repository-name>
```

2. Créer les dossiers nécessaires :
```bash
mkdir -p app/static/uploads
mkdir -p app/static/results
mkdir -p data
mkdir -p models
```

3. Copier les modèles pré-entraînés dans le dossier `models/`

4. Lancer l'application avec Docker Compose :
```bash
docker-compose up --build
```

L'application sera accessible à l'adresse : http://localhost:5000

## Utilisation

1. Connectez-vous avec les identifiants par défaut :
   - Username: admin
   - Password: admin

2. Sur la page d'accueil :
   - Sélectionnez une image à rechercher
   - Choisissez un ou plusieurs modèles d'indexation
   - Sélectionnez la méthode de calcul de similarité
   - Cliquez sur "Rechercher"

3. Les résultats afficheront :
   - Les images les plus similaires
   - Les métriques de performance (R, P, AP, MAP, R-Precision)
   - La courbe de précision/rappel

## Structure du Projet

```
project/
├── app/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── login.html
│   └── app.py
├── data/
├── models/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Sécurité

- L'application utilise Flask-Login pour l'authentification
- Les mots de passe sont hashés
- Les fichiers uploadés sont validés et sécurisés
- Les routes sont protégées

## Performance

- Utilisation de Redis pour le cache
- Optimisation des requêtes de recherche
- Gestion efficace de la mémoire

## Développement

Pour développer l'application localement :

1. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancer l'application :
```bash
python app/app.py
```

Pour déployer l'application sur votre VM et la rendre accessible publiquement :

1. Construire l'image Docker :
```bash
docker build -t echopic .
```

2. Lancer le conteneur :
```bash
docker run -d \
  -p 5000:5000 \
  --name echopic \
  echopic
```

3. Accès à l'application :
```bash
http://<IP_DE_VOTRE_VM>:5000
```

Assurez-vous que :
- Le port 5000 est ouvert dans le pare-feu de votre VM
- Les règles de sécurité de votre cloud provider autorisent le trafic sur le port 5000

4. Sécurité recommandée :
- Envisagez d'utiliser HTTPS avec un reverse proxy (comme Nginx)
- Configurez un domaine personnalisé si nécessaire
- Mettez en place des limites de taux (rate limiting) pour protéger votre API 