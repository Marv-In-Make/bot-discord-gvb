#!/bin/bash
#================================================================
# DISCORD BOT MONSTER - SCRIPT DÉPLOIEMENT AUTOMATIQUE
#================================================================
# Usage: sudo ./scripts/deploy.sh
#================================================================

set -e

echo "================================"
echo "DISCORD BOT MONSTER - DÉPLOIEMENT"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Ce script doit être exécuté en root${NC}"
    exit 1
fi

# Check .env existe
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Fichier .env introuvable${NC}"
    echo "Copier .env.example vers .env et le configurer."
    exit 1
fi

# Vérifier variables obligatoires
echo -e "${YELLOW}Vérification variables .env...${NC}"
source .env

required_vars=("DISCORD_TOKEN" "GUILD_ID" "API_KEY" "POSTGRES_PASSWORD" "REDIS_PASSWORD")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" == "CHANGEME" ] || [[ "${!var}" == *"CHANGEME"* ]]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo -e "${RED}❌ Variables manquantes ou non configurées :${NC}"
    printf '%s\n' "${missing_vars[@]}"
    exit 1
fi

echo -e "${GREEN}✅ Variables .env OK${NC}"

# Permissions
echo -e "${YELLOW}Configuration permissions...${NC}"
chmod 600 .env
chmod -R 755 scripts/
chmod -R 755 bot/
mkdir -p data/{postgres,redis,logs}
chown -R 1000:1000 data/logs
echo -e "${GREEN}✅ Permissions configurées${NC}"

# Vérifier réseau proxy existe
echo -e "${YELLOW}Vérification réseau Docker...${NC}"
if ! docker network inspect proxy &>/dev/null; then
    echo -e "${YELLOW}⚠️  Réseau 'proxy' inexistant, création...${NC}"
    docker network create proxy
fi
echo -e "${GREEN}✅ Réseau proxy OK${NC}"

# Valider docker-compose.yml
echo -e "${YELLOW}Validation configuration Docker...${NC}"
if ! docker compose config &>/dev/null; then
    echo -e "${RED}❌ Erreur dans docker-compose.yml${NC}"
    docker compose config
    exit 1
fi
echo -e "${GREEN}✅ Configuration valide${NC}"

# Pull images
echo -e "${YELLOW}Téléchargement images Docker...${NC}"
docker compose pull

# Build image bot
echo -e "${YELLOW}Build image bot (peut prendre 2-3 min)...${NC}"
docker compose build gvbot

# Démarrage stack
echo -e "${YELLOW}Démarrage stack...${NC}"
docker compose up -d

# Attendre que les services soient healthy
echo -e "${YELLOW}Attente démarrage services (max 2 min)...${NC}"
sleep 15

MAX_WAIT=120
ELAPSED=0
INTERVAL=10

while [ $ELAPSED -lt $MAX_WAIT ]; do
    TOTAL_CONTAINERS=$(docker compose ps -q | wc -l)
    HEALTHY_CONTAINERS=$(docker compose ps --format json 2>/dev/null | grep -c '"Health":"healthy"' || echo 0)
    
    echo "Services healthy: $HEALTHY_CONTAINERS/$TOTAL_CONTAINERS"
    
    if [ "$HEALTHY_CONTAINERS" -eq "$TOTAL_CONTAINERS" ]; then
        break
    fi
    
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

# Vérifier status final
echo ""
echo "================================"
echo "STATUS FINAL"
echo "================================"
docker compose ps

# Test healthcheck API
echo ""
echo -e "${YELLOW}Test API healthcheck...${NC}"
sleep 5
API_RESPONSE=$(curl -s http://localhost:5000/health 2>/dev/null || echo "ERROR")

if [[ "$API_RESPONSE" == *"healthy"* ]]; then
    echo -e "${GREEN}✅ API répond correctement${NC}"
else
    echo -e "${RED}❌ API ne répond pas (normal si bot démarre encore)${NC}"
fi

# Résumé
echo ""
echo "================================"
echo -e "${GREEN}✅ DÉPLOIEMENT TERMINÉ${NC}"
echo "================================"
echo ""
echo "📍 ACCÈS AUX SERVICES"
echo "─────────────────────────────────"
echo "API REST (interne)   : http://localhost:5000"
echo "Health endpoint      : http://localhost:5000/health"
echo "Stats endpoint       : http://localhost:5000/stats"
echo ""
echo "📊 COMMANDES UTILES"
echo "─────────────────────────────────"
echo "Logs temps réel      : docker compose logs -f --tail=50"
echo "Status containers    : docker compose ps"
echo "PostgreSQL shell     : docker compose exec postgres_discord psql -U gvb -d discord_gvb"
echo "Redis CLI            : docker compose exec redis_discord redis-cli"
echo ""
echo "📝 TEST BOT DISCORD"
echo "─────────────────────────────────"
echo "Dans Discord : !ping"
echo "Dans Discord : !help"
echo ""
echo "🔧 EN CAS DE PROBLÈME"
echo "─────────────────────────────────"
echo "docker compose logs gvbot | grep ERROR"
echo "docker compose restart gvbot"
echo ""
