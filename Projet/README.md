# EchoPic - Service de Recherche d'Images

## Description
EchoPic est un service SaaS de recherche d'images par similarité, permettant de combiner plusieurs modèles de deep learning pour une recherche plus précise.

## Prérequis
- Docker
- Docker Compose
- Git

## Structure du Projet
```
EchoPic/
├── app/
│   ├── app.py
│   └── templates/
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   ├── uploads/
│   ├── rp_curves/
│   └── image.orig/
├── features/
│   ├── ResNet50.pkl
│   ├── MobileNet.pkl
│   └── VIT.pkl
├── postgres/
│   └── init/
│       └── 01-init.sql
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

## Installation

1. **Cloner le repository**
```bash
git clone [URL_DU_REPO]
cd EchoPic
```

2. **Créer le fichier .env**
```bash
# Créer un fichier .env à la racine du projet
touch .env
```

3. **Configurer les variables d'environnement**
```env

FLASK_APP=app/app.py
FLASK_ENV=development
FLASK_SECRET_KEY=8f42a73054b1749f8f58848be5e6502c8c8d9c3c1b4e2a7f6d5c3b2a1e0f9d8c7b

POSTGRES_HOST=localhost
POSTGRES_USER=echopic_user
POSTGRES_PASSWORD=echopic_password_secure
POSTGRES_DB=echopic_db
POSTGRES_PORT=5432
```

4. **Vérifier la structure des dossiers**
```bash
# Créer les dossiers nécessaires s'ils n'existent pas
mkdir -p app/static/uploads app/static/rp_curves
```

## Déploiement avec Docker Compose

1. **Construire les images**
```bash
docker-compose build
```

2. **Démarrer les services**
```bash
docker-compose up -d
```

3. **Vérifier l'état des services**
```bash
docker-compose ps
```

4. **Voir les logs**
```bash
# Tous les services
docker-compose logs

# Service web uniquement
docker-compose logs web

# Service base de données uniquement
docker-compose logs db
```

## Utilisation

1. **Accéder à l'application**
- Interface web : https://163.172.234.100:5443

2. **Fonctionnalités disponibles**
- Recherche d'images par similarité
- Combinaison de plusieurs modèles (max 3)
- Génération de courbes RP


## Maintenance

1. **Arrêter les services**
```bash
docker-compose down
```

2. **Redémarrer les services**
```bash
docker-compose restart #SERVICE
```

3. **Reconstruire et redémarrer**
```bash
docker-compose up -d --build
```

4. **Nettoyer les volumes**
```bash
docker system prune -a --volumes
```


## Débogage

1. **Accéder au conteneur web**
```bash
docker-compose exec web /bin/bash
```

2. **Accéder à la base de données**
```bash
docker-compose exec db psql -U echopic_user -d echopic_db
```

3. **Vérifier les logs en temps réel**
```bash
docker-compose logs -f
```

## Volumes Docker
- `./app:/app/app` : Code de l'application
- `./app/static:/app/static` : Fichiers statiques
- `./app/features:/app/features` : Fichiers de features
- `./app/static/image.orig:/app/image.orig` : Images originales
- `postgres_data:/var/lib/postgresql/data` : Données PostgreSQL

## Sécurité
- Les mots de passe sont stockés dans le fichier .env
- Le port 5432 (PostgreSQL) n'est pas exposé publiquement
- Les uploads sont limités à 1MB par fichier
- Les noms de fichiers sont sécurisés avant le stockage

## Support
Pour toute question ou problème, veuillez ouvrir une issue sur le repository.

## Configuration HTTPS

1. **Certificats SSL**
- Les certificats sont stockés dans le dossier `certs/`
- Pour le développement, un certificat auto-signé est utilisé

2. **Génération d'un nouveau certificat**
```bash
# Générer un nouveau certificat auto-signé
openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365 -subj "/CN=localhost"
```

43 **Sécurité**
- Le certificat auto-signé générera un avertissement dans le navigateur
- En production, utilisez un certificat valide
- Les certificats sont montés en volume dans le conteneur 