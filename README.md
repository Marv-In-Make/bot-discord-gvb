# 🤖 DISCORD BOT MONSTER - GVB-ÉLECTRICITÉ

**Version** : 2.0 Monster Edition
**Date** : 2026-01-02
**Auteur** : Marvin Ansseau

## 🎯 Vue d'ensemble

Stack complète Discord bot ultra-optimisé pour gestion équipe GVB-Électricité.

### ✨ Fonctionnalités

**Bot Discord** :
- ✅ 20+ commandes (!presence, !stats, !t aches, !planning, etc.)
- ✅ Logging automatique tous messages PostgreSQL
- ✅ Cache intelligent Redis
- ✅ Rate limiting anti-spam
- ✅ Modération automatique
- ✅ Embeds riches pour tous retours
- ✅ Pagination listes longues
- ✅ Permissions granulaires par rôle

**API REST FastAPI** :
- ✅ 15+ endpoints (/health, /stats, /api/discord/*)
- ✅ Authentification Bearer token
- ✅ Documentation Swagger auto (/docs)
- ✅ Rate limiting
- ✅ CORS configuré

**Base de données PostgreSQL** :
- ✅ 10 tables optimisées
- ✅ 40+ indexes
- ✅ Full-text search (pg_trgm)
- ✅ Triggers auto-update
- ✅ Fonctions nettoyage automatique

**Cache & Queue Redis** :
- ✅ Cache stats (refresh 1h)
- ✅ Rate limiting distributed
- ✅ Session storage

**Monitoring & Observabilité** :
- ✅ Métriques Prometheus (/metrics)
- ✅ Logging structuré JSON
- ✅ Healthchecks Docker
- ✅ Webhooks alertes Discord

**Automatisations** :
- ✅ Planning hebdo (lundi 6h)
- ✅ Stats cache (1h)
- ✅ Cleanup vieilles données (24h)
- ✅ Backup automatique (configurable)

## 📦 Architecture

```
Services Docker :
├── gvbot            : Bot Discord Python 3.11
├── postgres_discord : PostgreSQL 16 Alpine
└── redis_discord    : Redis 7 Alpine

Réseaux :
├── discord_network  : Interne (bot ↔ DB ↔ Redis)
└── proxy            : Externe (API REST ↔ n8n)

Volumes :
├── ./data/postgres  : Données PostgreSQL
├── ./data/redis     : Données Redis
└── ./data/logs      : Logs applicatifs
```

## 🚀 Installation Rapide

### Prérequis
- Docker & Docker Compose ≥ 2.40
- Réseau Docker `proxy` existant (pour n8n)
- Token Discord bot
- Guild ID Discord

### Étape 1 : Transfert sur VPS

```bash
# Sur VPS
cd /opt/stacks
tar -xzf discord-bot-monster.tar.gz
cd discord-bot-monster
```

### Étape 2 : Configuration

```bash
# Copier .env
cp .env.example .env

# Éditer .env
nano .env

# OBLIGATOIRE à remplir :
# - DISCORD_TOKEN
# - GUILD_ID
# - API_KEY (générer avec : openssl rand -base64 32)
# - POSTGRES_PASSWORD (générer avec : openssl rand -hex 32)
# - REDIS_PASSWORD (générer avec : openssl rand -hex 32)

# Sauvegarder : CTRL+O, ENTER, CTRL+X
chmod 600 .env
```

### Étape 3 : Déploiement

```bash
# Déploiement automatique
sudo ./scripts/deploy.sh

# OU manuel
docker compose pull
docker compose up -d

# Vérifier logs
docker compose logs -f --tail=50
```

### Étape 4 : Vérifications

```bash
# Status containers (doivent être "healthy")
docker compose ps

# Tester API
curl http://localhost:5000/health

# Tester bot Discord
# Dans Discord : !ping
```

## 📋 Commandes Discord

### 👥 Équipe
```bash
!presence              # Qui est en ligne
!stats [jours]         # Top activité (défaut 7j)
!resume                # Stats du jour
```

### 📋 Tâches
```bash
!tache @user chantier description    # Créer tâche
!taches [@user]                      # Lister tâches
!done <id>                           # Marquer terminée
```

### 📅 Planning
```bash
!monplanning [@user]                 # Afficher planning
!planifier @user chantier JJ/MM JJ/MM notes  # Ajouter (Manager)
```

### 🔧 Admin
```bash
!auditserveur                        # Export JSON structure
!creerchantier <nom>                 # Créer channel chantier
!archiverchantier <nom>              # Archiver channel
```

### ⚙️ Utilitaires
```bash
!ping                  # Latence bot
!help [commande]       # Aide
!info                  # Informations bot
```

## 🌐 API REST

### Endpoints

```bash
# Health check
GET /health

# Stats globales
GET /stats
Authorization: Bearer YOUR_API_KEY

# Créer tâche
POST /api/discord/task
Authorization: Bearer YOUR_API_KEY
{
  "user_id": 123456789,
  "assignee_id": 987654321,
  "description": "Vérifier tableau",
  "chantier": "beautemps"
}

# Métriques Prometheus (si activé)
GET /metrics
```

### Test depuis n8n

```bash
# HTTP Request node
URL: http://gvbot:5000/health
Method: GET

# Doit retourner : {"status": "healthy", ...}
```

## 🗄️ Base de données

### Tables principales

| Table | Description | Records estimés |
|-------|-------------|-----------------|
| `messages` | Tous messages Discord | 100K+ |
| `tasks` | Tâches assignées | 1K+ |
| `planning` | Événements planning | 5K+ |
| `user_stats` | Cache stats utilisateurs | 50 |
| `chantiers` | Référentiel chantiers | 100 |

### Connexion PostgreSQL

```bash
# Shell PostgreSQL
docker compose exec postgres_discord psql -U gvb -d discord_gvb

# Top contributeurs 30j
SELECT user_name, messages_30d 
FROM user_stats 
ORDER BY messages_30d DESC 
LIMIT 10;

# Tâches en cours
SELECT * FROM tasks WHERE status='todo' ORDER BY created_at DESC;

# Planning semaine
SELECT * FROM planning 
WHERE date_debut >= CURRENT_DATE 
AND date_debut <= CURRENT_DATE + INTERVAL '7 days'
ORDER BY date_debut;

# Stats globales
SELECT * FROM stats_globales;

# Quitter
\q
```

## 🔧 Maintenance

### Logs

```bash
# Logs temps réel
docker compose logs -f gvbot

# Erreurs uniquement
docker compose logs gvbot | grep -i error

# Dernières 100 lignes
docker compose logs gvbot --tail=100
```

### Backup

```bash
# Backup automatique (script fourni)
./scripts/backup.sh

# Backup manuel PostgreSQL
docker compose exec postgres_discord \
  pg_dump -U gvb discord_gvb | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup manuel Redis
docker compose exec redis_discord redis-cli --rdb /tmp/dump.rdb
docker compose cp redis_discord:/tmp/dump.rdb ./backup_redis_$(date +%Y%m%d).rdb
```

### Restauration

```bash
# PostgreSQL
gunzip < backup_20260102.sql.gz | \
  docker compose exec -T postgres_discord psql -U gvb -d discord_gvb

# Redis
docker compose exec -T redis_discord redis-cli --pipe < backup_redis_20260102.rdb
```

### Update bot

```bash
# Modifier code
nano bot/bot_monster.py

# Rebuild image
docker compose build gvbot

# Redémarrer
docker compose up -d gvbot

# Vérifier
docker compose logs -f gvbot --tail=50
```

## 📊 Monitoring

### Métriques disponibles

Si `ENABLE_METRICS=true` dans `.env` :

```bash
# Prometheus metrics
curl http://localhost:9090/metrics

# Métriques disponibles :
# - discord_commands_total
# - discord_messages_total
# - discord_command_duration_seconds
# - discord_guild_members_total
# - postgres_connections_active
# - api_requests_total
# - api_request_duration_seconds
```

### Stack Grafana (optionnel)

Créer `docker-compose.monitoring.yml` :
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9091:9090"
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 🛡️ Sécurité

### Checklist

- [x] User non-root dans container (botuser:1000)
- [x] no-new-privileges security_opt
- [x] Secrets dans .env (chmod 600)
- [x] API REST avec Bearer token
- [x] Rate limiting actif
- [x] PostgreSQL isolé (réseau interne)
- [x] Redis avec mot de passe
- [x] Logs rotatifs (max 10MB x 5 fichiers)
- [x] Healthchecks actifs

### Renouveler API key

```bash
# Générer nouvelle clé
openssl rand -base64 32

# Modifier .env
nano .env  # Remplacer API_KEY

# Redémarrer
docker compose restart gvbot
```

## 🐛 Troubleshooting

### Bot ne démarre pas

```bash
# Vérifier logs
docker compose logs gvbot | grep -i error

# Vérifier variables .env
docker compose config

# Tester token Discord
# Developer Portal > Bot > Reset Token
```

### PostgreSQL connexion failed

```bash
# Vérifier status
docker compose ps postgres_discord

# Vérifier logs
docker compose logs postgres_discord

# Recréer base
docker compose down
sudo rm -rf data/postgres/*
docker compose up -d
```

### API ne répond pas

```bash
# Vérifier port binding
docker compose ps | grep gvbot

# Tester healthcheck
docker compose exec gvbot curl http://localhost:5000/health

# Vérifier réseau proxy
docker network inspect proxy
```

### Redis inaccessible

```bash
# Vérifier status
docker compose ps redis_discord

# Test connexion
docker compose exec redis_discord redis-cli ping
# Doit retourner : PONG

# Vérifier mot de passe
docker compose exec redis_discord redis-cli -a "${REDIS_PASSWORD}" ping
```

### Commandes Discord ne fonctionnent pas

```bash
# Vérifier bot online sur Discord
# Vérifier permissions bot (intents activés)
# Vérifier préfixe (défaut !)

# Logs commandes
docker compose logs gvbot | grep -i command
```

## 📚 Développement

### Structure code

```
bot/
├── bot_monster.py          # Core bot + API REST
├── admin_migration.py      # Scripts admin
├── utils.py                # Fonctions utilitaires
├── cogs/                   # Modules commandes
│   ├── commands_equipe.py
│   ├── commands_tasks.py
│   ├── commands_planning.py
│   ├── commands_admin.py
│   └── commands_moderation.py
└── requirements.txt
```

### Ajouter commande

```python
# Dans bot/cogs/commands_custom.py
from discord.ext import commands

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='test')
    async def test_command(self, ctx):
        """Commande de test"""
        await ctx.send("✅ Test OK!")

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))
```

Puis charger dans `bot_monster.py` :
```python
await bot.load_extension('cogs.commands_custom')
```

### Tests

```bash
# Lancer tests (si pytest configuré)
docker compose exec gvbot pytest tests/

# Test commande spécifique
# Dans Discord : !test
```

## 🗺️ Roadmap

### Phase 2 (à venir)
- [ ] Module RAG Qdrant (!ask pour support technique)
- [ ] Intégration Google Calendar (sync auto planning)
- [ ] Génération rapports Excel automatiques
- [ ] OCR factures fournisseurs
- [ ] Dashboard web React (stats temps réel)

### Phase 3 (futur)
- [ ] App mobile React Native
- [ ] IA prédictive stocks matériel
- [ ] Signature électronique documents
- [ ] Intégration caméras chantiers
- [ ] SaaS multi-serveurs Discord

## 📞 Support

**Développeur** : Marvin Ansseau
**Email** : marv.inmake83@gmail.com
**Discord** : GVB-Électricité

**Documentation complète** : `/opt/stacks/discord-bot-monster/docs/`

## 📄 Licence

Propriétaire - GVB-Électricité
© 2026 Marvin Ansseau

---

**Stack production-ready déployable en <15 minutes** 🚀

Marv_InMake
