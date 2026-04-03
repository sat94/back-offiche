# Ansible — Infrastructure MeetVoice

## Architecture

```
ansible/
├── site.yml                    ← Playbook principal
├── ansible.cfg                 ← Config (vault, SSH)
├── group_vars/
│   ├── all.yml                 ← Variables globales (versions, ports)
│   └── vault.yml               ← Secrets chiffrés (JAMAIS commité en clair)
├── inventory/
│   ├── hosts.yml               ← IPs réelles (gitignored)
│   └── hosts.yml.example       ← Template sans IPs
└── roles/
    ├── ssh_hardening/          ← Hardening SSH (root, password, ports) [NOUVEAU]
    ├── node_exporter/          ← Sur TOUS les serveurs
    ├── prometheus/             ← Sur BACKEND (monitoring_server)
    ├── grafana/                ← Sur BACKEND
    ├── alertmanager/           ← Sur BACKEND (alertes Slack/email)
    ├── loki/                   ← Sur BACKEND (logs centralisés)
    ├── promtail/               ← Sur tous les monitored_servers
    ├── nginx/                  ← Sur BACKEND (reverse proxy)
    ├── certbot/                ← Sur BACKEND (TLS Let's Encrypt)
    ├── self_healing/           ← Sur TOUS (redémarre les services down)
    └── semaphore/              ← Sur BACKEND (UI web Ansible)
```

---

## Installation du poste de travail (Contrôleur)

Avant de déployer, ton propre PC (Windows) doit être prêt :

1.  **Activer WSL (Linux)** : 
    *   Ouvre PowerShell en Admin : `wsl --install`
    *   Vérifie que le service `LxssManager` est démarré.
2.  **Installer les outils (dans WSL)** :
    ```bash
    cd ansible/
    pip install -r requirements_ansible.txt
    ```

## Premier déploiement

### 1. Configurer les secrets (vault)

```bash
# Copier le template vault
cp group_vars/vault.yml.example group_vars/vault.yml

# Éditer les valeurs (mot de passe Grafana, webhook Slack, etc.)
nano group_vars/vault.yml

# Chiffrer le vault
echo "MON_MOT_DE_PASSE_VAULT" > ~/.vault_pass
chmod 600 ~/.vault_pass
ansible-vault encrypt group_vars/vault.yml
```

### 2. Configurer l'inventaire

```bash
cp inventory/hosts.yml.example inventory/hosts.yml
nano inventory/hosts.yml   # Remplir les vraies IPs
```

### 3. Déploiement complet

```bash
# Déploiement initial (tout sauf certbot et semaphore)
ansible-playbook site.yml --skip-tags "certbot,semaphore"

# Après DNS configuré : activer HTTPS
ansible-playbook site.yml --tags certbot

# Interface web Ansible (optionnel)
ansible-playbook site.yml --tags semaphore
```

---

## Commandes courantes

```bash
# Vérifier la syntaxe sans déployer
ansible-playbook site.yml --syntax-check

# Mode dry-run (voir ce qui va changer)
ansible-playbook site.yml --check --diff

# Self-healing uniquement (redémarre les services down)
ansible-playbook site.yml --tags self_healing

# Redéployer un rôle spécifique
ansible-playbook site.yml --tags prometheus
ansible-playbook site.yml --tags grafana

# Cibler un seul serveur
ansible-playbook site.yml --limit FRONTEND

# Voir les facts d'un serveur
ansible FRONTEND -m setup
```

---

## Self-Healing automatique

Chaque service est configuré avec `Restart=always` dans systemd. En plus :

- Un **cron quotidien à 4h00** sur le BACKEND ré-applique `site.yml --tags self_healing`
- Si un service ne démarre pas, systemd le relance automatiquement toutes les 10s
- Après 5 échecs en 120s, systemd cesse de relancer (évite les boucles infinies)
- Les alertes Alertmanager → Slack préviennent si un service reste DOWN plus d'1 minute

---

## Semaphore UI (Ansible Tower open-source)

Accessible sur `http://BACKEND_IP:3001` après déploiement.

Permet de :
- Déclencher des playbooks depuis un navigateur
- Planifier des runs automatiques (équivalent cron)
- Voir l'historique des exécutions
- Gérer les inventaires et clés SSH

> **Pas besoin d'Ansible Tower** (payant, lourd) ni d'AWX (nécessite Kubernetes).
> Semaphore est un seul binaire, léger, parfait pour une équipe de 1-10 personnes.

---

## Gestion du vault

```bash
# Voir les secrets (demande le mot de passe)
ansible-vault view group_vars/vault.yml

# Modifier les secrets
ansible-vault edit group_vars/vault.yml

# Changer le mot de passe du vault
ansible-vault rekey group_vars/vault.yml
```
