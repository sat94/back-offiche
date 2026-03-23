# Back Office - Projet Django

Projet Django avec double base de données : PostgreSQL et MongoDB

## 📋 Structure du projet

### Applications

#### 1. **core** (PostgreSQL)
Gère les données relationnelles :
- **Abonnement** : Gestion des abonnements utilisateurs
- **Facture** : Gestion des factures

#### 2. **content** (MongoDB)
Gère les données NoSQL :
- **Article** : Gestion des articles de blog
- **Contact** : Gestion des contacts/demandes
- **ReseauSocial** : Gestion des réseaux sociaux

## 🗄️ Bases de données

### PostgreSQL
- Tables : `abonnements`, `factures`
- Configuration dans `.env`

### MongoDB
- Collections : `articles`, `contacts`, `reseaux_sociaux`
- Configuration dans `.env`

## 🚀 Installation

### 1. Activer l'environnement virtuel
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Installer les dépendances
```powershell
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement
Modifier le fichier `.env` avec vos paramètres

### 4. Appliquer les migrations PostgreSQL
```powershell
python manage.py migrate
```

### 5. Créer un superutilisateur
```powershell
python manage.py createsuperuser
```

### 6. Lancer le serveur
```powershell
python manage.py runserver
```

## 📝 Utilisation

### Modèles PostgreSQL (core)

Accéder à l'admin Django : `http://localhost:8000/admin`

### Modèles MongoDB (content)

Utiliser les classes Python directement :

```python
from content.models import Article, Contact, ReseauSocial

# Créer un article
article_id = Article.create_article(
    titre="Mon article",
    contenu="Contenu...",
    auteur="Admin",
    categorie="tech",
    tags=["django", "mongodb"]
)

# Créer un contact
contact_id = Contact.create_contact(
    nom="Jean Dupont",
    email="jean@example.com",
    message="Bonjour"
)

# Créer un réseau social
reseau_id = ReseauSocial.create_reseau(
    plateforme="twitter",
    nom_compte="@moncompte",
    url="https://twitter.com/moncompte"
)
```

## 📂 Fichiers utiles

- `content/mongo_admin.py` : Exemples d'utilisation des modèles MongoDB
- `back_office/mongodb.py` : Configuration de la connexion MongoDB
- `check_db.py` : Script pour vérifier les tables PostgreSQL
- `fix_migrations.py` : Script pour réinitialiser les migrations

## 🔧 Commandes utiles

```powershell
# Créer une nouvelle migration
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver

# Tester les modèles MongoDB
python content/mongo_admin.py

# Vérifier les tables PostgreSQL
python check_db.py
```

## 📦 Dépendances principales

- Django 5.2.8
- psycopg2-binary (PostgreSQL)
- pymongo (MongoDB)
- python-decouple (Variables d'environnement)

## 🔐 Sécurité

- Ne jamais committer le fichier `.env`
- Changer la `SECRET_KEY` en production
- Mettre `DEBUG=False` en production

