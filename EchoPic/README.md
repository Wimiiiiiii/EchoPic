# EchoPic - Service de Recherche d'Images

## Description
EchoPic est un service SaaS de recherche d'images par similarité, permettant de combiner plusieurs modèles de deep learning.

## Prérequis
- Docker
- Docker Compose
- Git

## Structure du Projet
```
EchoPic/

├── app/                             # Dossier principal de l'application
│   ├── features/                    
│   ├── MobileNet.pkl                # Modèle MobileNet 
│   ├── Resnet50.pkl                 # Modèle ResNet50 
│   ├── VGG16.pkl                    # Modèle VGG16 
│   ├── VIT.pkl                      # Modèle Vision Transformer 
│   │
│   ├── static/                      # Fichiers statiques
│   │   ├── css/                     # Feuilles de style CSS
│   │   ├── image.orig/              # Images originales
│   │   ├── images/                  # Images utilisées dans le site web
│   │   ├── js/                      # Fichiers JavaScript
│   │   ├── rp_curves/               # Courbes RP (Recall-Precision)
│   │   └── uploads/                 # Dossier pour les images téléchargées par les utilisateurs
│   │
│   ├── templates/                   
│   │   ├── index.html               # Page d'accueil
│   │   ├── results.html             # Page de résultats
│   │   └── search.html              # Page de recherche
│   │
│   ├── .env                         # Variables d'environnement
│   ├── 1RP.txt                      # Fichier texte pour les résultats RP
│   └── app.py                       # Script principal de l'application Flask
│
├── postgres/                        # Configuration PostgreSQL
│   └── init/
│       └── 01-init.sql              # Script d'initialisation de la base de données
│
├── docker-compose.yml               # Configuration Docker Compose
├── Dockerfile                       # Configuration Docker pour l'application
├── README.md                        # Documentation du projet
└── requirements.txt                 # Dépendances

```
## Installation

1. **Cloner le repository**
```bash
git clone https://github.com/Wimiiiiiii/EchoPic.git
cd EchoPic
```

2. **Créer le fichier .env**
```bash
# Créer un fichier .env à la racine du projet
touch .env
```

3. **Configurer les variables d'environnement**
```env
Données gardées secretes ....
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
docker-compose restart #NOM_DU_SERVICE
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
- `./app/features:/app/features` : Fichiers des modèles IA en format .pkl
- `./app/static/image.orig:/app/image.orig` : Images originales
- `postgres_data:/var/lib/postgresql/data` : Données PostgreSQL

## Sécurité
- Les mots de passe sont stockés dans le fichier .env
- Le port 5432 (PostgreSQL) n'est pas exposé publiquement
- Les uploads sont limités à 1MB par fichier
- Les noms de fichiers sont sécurisés avant le stockage

## Support
Pour toute question ou problème, veuillez nous contacter via nos comptes LinkedIn en bas de page d'acceuil du site web.

## Configuration HTTPS

1. **Certificats SSL**
- Les certificats sont stockés dans le dossier `certs/`
- Pour le développement, un certificat auto-signé est utilisé

2. **Génération d'un nouveau certificat**
```bash
# Générer un nouveau certificat auto-signé
openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365 -subj "/CN=EchoPic"
```

43 **Sécurité**
- Le certificat auto-signé générera un avertissement dans le navigateur
- Les certificats sont montés en volume dans le conteneur 