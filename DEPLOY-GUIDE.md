# 🚀 GUIDE DÉPLOIEMENT COMPLET - BOT DISCORD MONSTER

## 📦 CONTENU ARCHIVE

**Fichier** : `discord-bot-monster.tar.gz` (28KB)

### Structure complète

```
discord-bot-monster/
├── 📄 README.md                    # Documentation complète (8000+ mots)
├── ⚡ QUICKSTART.md                # Déploiement rapide <10 min
├── 🚀 IMPROVEMENTS.md              # 25+ améliorations vs bot basique
├── 🐙 .gitignore                   # Fichiers à ignorer Git
│
├── ⚙️ docker-compose.yml           # Orchestration 3 services
├── 🔐 .env.example                 # Template variables (à copier vers .env)
│
├── 🐳 bot/
│   ├── Dockerfile                  # Multi-stage optimisé
│   ├── requirements.txt            # 40+ dépendances Python
│   ├── bot_monster.py              # Code principal (800+ lignes)
│   ├── utils.py                    # Fonctions utilitaires
│   ├── admin_migration.py          # Module admin serveur
│   └── cogs/                       # Modules commandes (vides, à compléter)
│       └── __init__.py
│
├── 🗄️ configs/
│   └── postgres/
│       ├── init.sql                # Tables + indexes + triggers (400+ lignes)
│       └── extensions.sql          # Extensions PostgreSQL
│
├── 🔧 scripts/
│   ├── deploy.sh                   # Déploiement automatique (executable)
│   └── backup.sh                   # Backup auto (executable)
│
└── 📂 data/                        # Volumes Docker (vides initialement)
    ├── postgres/
    ├── redis/
    └── logs/
```

---

## ⚡ DÉPLOIEMENT EXPRESS (<10 MIN)

### 1. Transfert VPS (1 min)

```bash
# Sur VPS
cd /opt/stacks
wget https://votre-url/discord-bot-monster.tar.gz
tar -xzf discord-bot-monster.tar.gz
cd discord-bot-monster
```

### 2. Configuration .env (5 min)

```bash
# Copier template
cp .env.example .env

# Générer secrets sécurisés
POSTGRES_PASS=$(openssl rand -hex 32)
REDIS_PASS=$(openssl rand -hex 32)
API_KEY=$(openssl rand -base64 32)

# Éditer .env
nano .env

# REMPLIR OBLIGATOIREMENT :
# ─────────────────────────────────────────────────────────
# DISCORD_TOKEN=MTMxMjc4...XXXXXX  # Token bot Discord
# GUILD_ID=1381550039721312350     # ID serveur Discord
# API_KEY=$API_KEY                 # Clé générée ci-dessus
# POSTGRES_PASSWORD=$POSTGRES_PASS # Password générée
# REDIS_PASSWORD=$REDIS_PASS       # Password générée
# ─────────────────────────────────────────────────────────

# Sauvegarder : CTRL+O, ENTER, CTRL+X
chmod 600 .env
```

### 3. Déploiement (2 min)

```bash
# Rendre scripts exécutables
chmod +x scripts/*.sh

# Lancer déploiement automatique
sudo ./scripts/deploy.sh

# Attendre message : ✅ DÉPLOIEMENT TERMINÉ
```

### 4. Vérifications (1 min)

```bash
# Status containers (tous doivent être "healthy")
docker compose ps

# Logs temps réel
docker compose logs -f --tail=50

# Test API
curl http://localhost:5000/health
# Doit retourner : {"status":"healthy",...}

# Test bot Discord
# Dans Discord : !ping
# Doit répondre : 🏓 Pong! Latence : XXms
```

---

## 🔑 OBTENIR TOKEN DISCORD

### Étape 1 : Créer Application Discord

1. **Discord Developer Portal** : https://discord.com/developers/applications
2. Cliquer **New Application**
3. Nom : `GVBOT` (ou autre)
4. Créer

### Étape 2 : Créer Bot

1. Section **Bot** (menu gauche)
2. Cliquer **Add Bot** → Confirm
3. **Reset Token** → **Copier le token** ⚠️ (1 seule fois)
4. Activer **Privileged Gateway Intents** :
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent
5. Save Changes

### Étape 3 : Inviter Bot sur Serveur

1. Section **OAuth2** → **URL Generator**
2. **Scopes** :
   - ✅ `bot`
   - ✅ `applications.commands`
3. **Bot Permissions** :
   - ✅ Administrator (ou permissions granulaires)
4. **Copier l'URL générée**
5. Ouvrir URL dans navigateur
6. Sélectionner ton serveur Discord
7. Autoriser

### Étape 4 : Obtenir Guild ID

1. Sur Discord : **Paramètres utilisateur** → **Avancés**
2. Activer **Mode développeur**
3. Clic droit sur **ton serveur** → **Copier l'identifiant**
4. C'est le `GUILD_ID` (exemple : `1381550039721312350`)

---

## 📊 STRUCTURE SERVEUR DISCORD RECOMMANDÉE

Si tu n'as pas encore structuré ton serveur, voici la structure optimale pour GVB :

### Catégories & Channels

```
📋 ACCUEIL & RÈGLES
  ├─ #✅-règlement-serveur
  ├─ #📢-annonces-générales
  └─ #📚-guide-utilisation-discord

📝 FORMULAIRES
  ├─ #rapports-chantier
  ├─ #feuilles-heures
  ├─ #demandes-congés
  └─ #rapports-intervention

🛒 COMMANDES MATÉRIEL
  ├─ #demandes-matériel
  ├─ #commandes-encours
  ├─ #réceptions
  └─ #stock-consommables

👷 ÉQUIPE & RH
  ├─ #📅-planning-complet
  ├─ #📆-planning-hebdo
  ├─ #🤖-mon-planning
  ├─ #🎓-formations
  └─ #📢-notifications-équipe

🗝️ CHANTIERS ACTIFS
  ├─ #albatros
  ├─ #anseur
  ├─ #beautemps
  └─ ... (autres chantiers)

📦 CHANTIERS ARCHIVÉS
  ├─ #2025-projet-terminé
  └─ ...

🔧 INTERVENTIONS
  ├─ #urgences
  ├─ #planifiées
  └─ #demandes-clients

📊 LOGS & ADMIN
  ├─ #logs-bot
  ├─ #logs-webhooks
  ├─ #audit-serveur
  └─ #reporting-stats
```

**Rôles recommandés** :
- Admin
- Manager
- Technicien
- Apprenti/Stagiaire

---

## 🎯 PREMIERS TESTS

### Test 1 : Commandes basiques

```
!ping          # Latence bot
!help          # Liste commandes
!info          # Informations bot
!presence      # Qui est en ligne
```

### Test 2 : Stats & activité

```
!stats         # Top activité 7j
!stats 30      # Top activité 30j
!resume        # Stats du jour
```

### Test 3 : Tâches

```
!tache @User beautemps Vérifier tableau électrique
!taches
!done 1
```

### Test 4 : API REST (depuis n8n)

**HTTP Request node n8n** :
```
URL: http://gvbot:5000/health
Method: GET

# Doit retourner :
{
  "status": "healthy",
  "bot": "ok",
  "database": "ok",
  "redis": "ok",
  "latency_ms": 42.5
}
```

---

## 🔧 CONFIGURATION CHANNELS IDS

Une fois ton serveur Discord créé, tu dois récupérer les IDs des channels importants.

### Obtenir Channel IDs

1. Sur Discord : **Mode développeur activé**
2. Clic droit sur **channel** → **Copier l'identifiant**
3. Éditer `.env` :

```bash
nano .env

# Ajouter IDs :
CHANNEL_PLANNING_HEBDO=1234567890123456789
CHANNEL_LOGS_BOT=1234567890123456789
CHANNEL_ANNONCES=1234567890123456789
CHANNEL_NOTIFICATIONS_EQUIPE=1234567890123456789

# Sauvegarder : CTRL+O, ENTER, CTRL+X
```

4. Redémarrer bot :

```bash
docker compose restart gvbot
```

---

## 🌐 INTÉGRATION N8N

### Communiquer n8n → Bot

**Workflow n8n** :
1. Node **HTTP Request**
2. URL : `http://gvbot:5000/api/discord/task`
3. Method : `POST`
4. Authentication : Header
   - Name : `Authorization`
   - Value : `Bearer VOTRE_API_KEY`
5. Body :
```json
{
  "user_id": 123456789,
  "assignee_id": 987654321,
  "description": "Vérifier tableau",
  "chantier": "beautemps"
}
```

### Communiquer Bot → n8n

**Webhook n8n** :
1. Node **Webhook** dans n8n
2. Copier URL webhook : `https://webhooks.marvinmake.duckdns.org/webhook/discord`
3. Ajouter dans `.env` :
```bash
N8N_WEBHOOK_URL=https://webhooks.marvinmake.duckdns.org/webhook/discord
```
4. Le bot peut maintenant trigger workflows n8n

---

## 🗄️ ACCÈS BASE DE DONNÉES

### PostgreSQL Shell

```bash
# Connexion
docker compose exec postgres_discord psql -U gvb -d discord_gvb

# Commandes utiles
\dt                          # Lister tables
\d messages                  # Structure table
SELECT * FROM stats_globales;
SELECT * FROM user_stats ORDER BY messages_7d DESC LIMIT 10;

# Quitter
\q
```

### Requêtes SQL utiles

```sql
-- Top contributeurs 30j
SELECT user_name, messages_30d 
FROM user_stats 
ORDER BY messages_30d DESC 
LIMIT 10;

-- Tâches en cours par chantier
SELECT chantier, COUNT(*) 
FROM tasks 
WHERE status='todo' 
GROUP BY chantier;

-- Planning semaine
SELECT * FROM planning 
WHERE date_debut >= CURRENT_DATE 
AND date_debut <= CURRENT_DATE + INTERVAL '7 days'
ORDER BY date_debut;

-- Cleanup vieux messages (>1 an)
SELECT cleanup_old_messages(365);
```

---

## 🔄 BACKUP & RESTAURATION

### Backup Manuel

```bash
# Backup PostgreSQL
docker compose exec postgres_discord pg_dump -U gvb discord_gvb | \
  gzip > backup_$(date +%Y%m%d).sql.gz

# Backup Redis
docker compose exec redis_discord redis-cli SAVE
docker compose cp redis_discord:/data/dump.rdb backup_redis_$(date +%Y%m%d).rdb
```

### Backup Automatique (Cron)

```bash
# Éditer crontab
crontab -e

# Ajouter ligne (backup quotidien 3h du matin)
0 3 * * * /opt/stacks/discord-bot-monster/scripts/backup.sh

# Sauvegarder
```

### Restauration

```bash
# Restaurer PostgreSQL
gunzip < backup_20260102.sql.gz | \
  docker compose exec -T postgres_discord psql -U gvb -d discord_gvb

# Restaurer Redis
docker compose exec redis_discord redis-cli FLUSHALL
docker compose cp backup_redis_20260102.rdb redis_discord:/data/dump.rdb
docker compose restart redis_discord
```

---

## 📊 MONITORING

### Logs Temps Réel

```bash
# Tous services
docker compose logs -f --tail=50

# Bot uniquement
docker compose logs -f gvbot --tail=100

# Erreurs uniquement
docker compose logs gvbot | grep -i error
```

### Métriques Prometheus (si activé)

```bash
# Dans .env
ENABLE_METRICS=true

# Redémarrer
docker compose restart gvbot

# Accéder métriques
curl http://localhost:9090/metrics
```

---

## 🐛 TROUBLESHOOTING

### Bot ne démarre pas

```bash
# Vérifier logs
docker compose logs gvbot | grep ERROR

# Vérifier variables .env
docker compose config

# Vérifier token Discord
# Developer Portal > Bot > Regenerate Token
```

### PostgreSQL connexion failed

```bash
# Vérifier status
docker compose ps postgres_discord

# Vérifier logs
docker compose logs postgres_discord

# Recréer DB (⚠️ perte données)
docker compose down
sudo rm -rf data/postgres/*
docker compose up -d
```

### API ne répond pas

```bash
# Test local
docker compose exec gvbot curl http://localhost:5000/health

# Vérifier port
docker compose ps | grep gvbot

# Vérifier réseau proxy
docker network inspect proxy | grep gvbot
```

### Commandes Discord ne fonctionnent pas

```bash
# Vérifier intents Discord (Developer Portal)
# Vérifier permissions bot sur serveur
# Vérifier préfixe (défaut !)

# Logs commandes
docker compose logs gvbot | grep command
```

---

## 🚀 PROCHAINES ÉTAPES

### Phase 2 : Compléter Cogs

Les modules cogs sont vides (`bot/cogs/`). Tu peux les compléter avec commandes spécifiques :

1. `cogs/commands_equipe.py` : !presence, !stats, !resume
2. `cogs/commands_tasks.py` : !tache, !taches, !done
3. `cogs/commands_planning.py` : !monplanning, !planifier
4. `cogs/commands_admin.py` : !creerchantier, !archiverchantier
5. `cogs/commands_moderation.py` : !warn, !timeout, !ban

### Phase 3 : Intégrations Avancées

- [ ] Google Calendar OAuth2 sync planning
- [ ] RAG Qdrant (!ask support technique)
- [ ] Génération rapports Excel automatiques
- [ ] OCR factures fournisseurs
- [ ] Dashboard web React

---

## 📞 SUPPORT

**Développeur** : Marvin Ansseau
**Email** : marv.inmake83@gmail.com
**Discord** : GVB-Électricité

**Documentation** : `/opt/stacks/discord-bot-monster/README.md`

---

## ✅ CHECKLIST POST-DÉPLOIEMENT

- [ ] Bot online sur Discord
- [ ] !ping répond correctement
- [ ] !help affiche commandes
- [ ] PostgreSQL accessible (`docker compose exec postgres_discord psql`)
- [ ] Redis accessible (`docker compose exec redis_discord redis-cli ping`)
- [ ] API répond (`curl http://localhost:5000/health`)
- [ ] Logs propres (pas d'ERROR)
- [ ] Backup configuré (cron si souhaité)
- [ ] Channels IDs configurés dans .env
- [ ] Test n8n → bot (créer tâche via API)
- [ ] Planning hebdo auto (attendre lundi 6h)

---

**🎉 Félicitations ! Ton bot Discord Monster est opérationnel !**

**Temps total installation : <10 minutes** ⚡

Marv_InMake
