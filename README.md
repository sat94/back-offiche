# Back Office MeetVoice

Back office Django pour la gestion de la plateforme MeetVoice : comptes, moderation, bases de donnees, monitoring, facturation, articles, messagerie et terminal SSH.

## Pre-requis

- Python 3.12+
- Une cle SSH ed25519 dont la cle publique est ajoutee sur les serveurs distants

## Installation

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration SSH

L'application ouvre des tunnels SSH vers les serveurs de bases de donnees et de monitoring au demarrage. Chaque developpeur doit configurer sa propre cle SSH.

### 1. Generer une cle SSH (si vous n'en avez pas)

```powershell
ssh-keygen -t ed25519 -C "votre_nom"
```

Cela cree deux fichiers dans `~/.ssh/` :
- `id_ed25519` (cle privee)
- `id_ed25519.pub` (cle publique)

### 2. Ajouter la cle publique sur les serveurs

Demander a un administrateur d'ajouter votre cle publique (`id_ed25519.pub`) dans le fichier `~/.ssh/authorized_keys` de chaque serveur, ou utiliser :

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@<IP_SERVEUR>
```

### 3. Configurer le `.env`

Copier le `.env` d'exemple et renseigner votre chemin de cle :

```env
SSH_KEY_PATH=C:/Users/VOTRE_NOM/.ssh/id_ed25519
SSH_USER=root
```

Le chemin par defaut est `~/.ssh/id_ed25519` si non renseigne.

## Variables d'environnement

Creer un fichier `.env` a la racine du projet avec les variables suivantes :

| Variable | Description |
|---|---|
| `SECRET_KEY` | Cle secrete Django |
| `DEBUG` | Mode debug (`True`/`False`) |
| `ALLOWED_HOSTS` | Hotes autorises (separes par des virgules) |
| `SSH_KEY_PATH` | Chemin vers la cle privee SSH |
| `SSH_USER` | Utilisateur SSH (defaut : `root`) |
| `PG_MAIN_NAME` | Nom de la base PostgreSQL principale |
| `PG_MAIN_USER` | Utilisateur PostgreSQL |
| `PG_MAIN_PASSWORD` | Mot de passe PostgreSQL |
| `AWS_ACCESS_KEY_ID` | Cle AWS pour S3 |
| `AWS_SECRET_ACCESS_KEY` | Secret AWS pour S3 |
| `MOLLIE_API_KEY` | Cle API Mollie (paiements) |
| `SMTP_HOST` | Serveur SMTP |
| `SMTP_USER` | Utilisateur SMTP |
| `SMTP_PASSWORD` | Mot de passe SMTP |

## Lancement

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acceder au back office : `http://localhost:8000/`

## Structure du projet

```
back_office/          # Configuration Django, settings, tunnels SSH
core/                 # Modeles PostgreSQL (abonnements, factures)
compte/               # Gestion des comptes utilisateurs
content/              # Modeles PostgreSQL articles + routeur de base
dashboard/            # Vues principales, URLs, helpers (Mollie, IMAP, SSH, AI, newsletter)
monitoring/           # Prometheus + Grafana (docker-compose)
templates/dashboard/  # Templates HTML
static/               # CSS, JS
```

## Applications

| App | Base de donnees | Description |
|---|---|---|
| `core` | PostgreSQL | Abonnements, factures |
| `compte` | PostgreSQL | Comptes utilisateurs |
| `content` | PostgreSQL (articles) | Articles, routeur multi-DB |
| `dashboard` | PostgreSQL + MongoDB | Interface d'administration |

## Fonctionnalites

- **Comptes** : liste, detail, activation/desactivation, suppression
- **Moderation** : photos, posts, commentaires, messages, evenements
- **Bases de donnees** : exploration PostgreSQL et MongoDB
- **Monitoring** : metriques serveurs via Node Exporter (Prometheus/Grafana)
- **Facturation** : integration Mollie (abonnements, remboursements)
- **Articles** : gestion des articles de blog
- **Mailbox** : lecture/envoi d'emails via IMAP/SMTP
- **Newsletter** : generation d'images AI et envoi de newsletters
- **Terminal SSH** : terminal distant avec assistant AI
- **Contabo** : gestion des VPS (snapshots, reinstallation, mots de passe)

## Docker

```powershell
docker build -t back-office .
docker run -p 8000:8000 --env-file .env back-office
```

## Tests

```powershell
python manage.py test
```

Ou depuis l'interface : `http://localhost:8000/tests/`
