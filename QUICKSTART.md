# ⚡ QUICKSTART - Bot Discord Monster

Déploiement ultra-rapide en **10 minutes**.

## 📦 1. Transfert VPS

```bash
# Sur VPS
cd /opt/stacks
wget https://votre-url/discord-bot-monster.tar.gz
tar -xzf discord-bot-monster.tar.gz
cd discord-bot-monster
```

## 🔑 2. Configuration .env (5 min)

```bash
# Copier template
cp .env.example .env

# Générer secrets
POSTGRES_PASS=$(openssl rand -hex 32)
REDIS_PASS=$(openssl rand -hex 32)
API_KEY=$(openssl rand -base64 32)

# Éditer .env
nano .env

# Remplir OBLIGATOIREMENT :
DISCORD_TOKEN=MTMxMjc4NjY0Nzk5MjM1MDc4NA.XXXXXX
GUILD_ID=1381550039721312350
API_KEY=$API_KEY
POSTGRES_PASSWORD=$POSTGRES_PASS
REDIS_PASSWORD=$REDIS_PASS

# Sauvegarder : CTRL+O, ENTER, CTRL+X
chmod 600 .env
```

## 🚀 3. Déploiement (2 min)

```bash
# Rendre scripts exécutables
chmod +x scripts/*.sh

# Lancer déploiement
sudo ./scripts/deploy.sh

# Attendre message : ✅ TOUS LES SERVICES SONT HEALTHY
```

## ✅ 4. Vérifications (1 min)

```bash
# Status containers
docker compose ps

# Logs
docker compose logs -f --tail=50

# Test API
curl http://localhost:5000/health

# Test bot Discord
# Dans Discord : !ping
```

## 🎯 5. Premier test

```bash
# Sur Discord :
!presence    # Voir qui est en ligne
!stats      # Stats activité
!help       # Liste commandes

# Via API (depuis n8n) :
curl -H "Authorization: Bearer VOTRE_API_KEY" \
  http://gvbot:5000/stats
```

## ❌ Problèmes ?

```bash
# Bot ne démarre pas
docker compose logs gvbot | grep ERROR

# PostgreSQL erreur
docker compose logs postgres_discord

# Redémarrer tout
docker compose down && docker compose up -d
```

## 📚 Suite

Voir **README.md** pour documentation complète.

---

**Temps total : <10 min** ⚡

Marv_InMake
