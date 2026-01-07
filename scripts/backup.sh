#!/bin/bash
#================================================================
# DISCORD BOT MONSTER - SCRIPT BACKUP AUTOMATIQUE
#================================================================
# Usage: ./scripts/backup.sh
# Cron: 0 3 * * * /opt/stacks/discord-bot-monster/scripts/backup.sh
#================================================================

set -e

# Configuration
BACKUP_DIR="${BACKUP_PATH:-/opt/backups/discord-bot}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)

echo "================================"
echo "DISCORD BOT - BACKUP"
echo "================================"
echo "Date: $(date)"
echo "Backup dir: $BACKUP_DIR"
echo ""

# Créer dossier backup
mkdir -p "$BACKUP_DIR"/{postgres,redis,configs}

# Backup PostgreSQL
echo "📦 Backup PostgreSQL..."
docker compose exec -T postgres_discord pg_dump -U gvb discord_gvb | \
  gzip > "$BACKUP_DIR/postgres/discord_gvb_$DATE.sql.gz"
echo "✅ PostgreSQL backup: discord_gvb_$DATE.sql.gz"

# Backup Redis
echo "📦 Backup Redis..."
docker compose exec redis_discord redis-cli SAVE
docker compose cp redis_discord:/data/dump.rdb "$BACKUP_DIR/redis/dump_$DATE.rdb"
echo "✅ Redis backup: dump_$DATE.rdb"

# Backup configs
echo "📦 Backup configs..."
tar -czf "$BACKUP_DIR/configs/configs_$DATE.tar.gz" \
  .env docker-compose.yml configs/ bot/*.py 2>/dev/null || true
echo "✅ Configs backup: configs_$DATE.tar.gz"

# Nettoyage anciens backups
echo ""
echo "🧹 Nettoyage backups > $RETENTION_DAYS jours..."
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
echo "✅ Nettoyage terminé"

# Résumé
echo ""
echo "================================"
echo "✅ BACKUP TERMINÉ"
echo "================================"
echo "PostgreSQL: $(ls -lh $BACKUP_DIR/postgres/discord_gvb_$DATE.sql.gz | awk '{print $5}')"
echo "Redis: $(ls -lh $BACKUP_DIR/redis/dump_$DATE.rdb | awk '{print $5}')"
echo "Configs: $(ls -lh $BACKUP_DIR/configs/configs_$DATE.tar.gz | awk '{print $5}')"
echo ""
echo "Total backups: $(find $BACKUP_DIR -type f | wc -l) fichiers"
echo "Espace utilisé: $(du -sh $BACKUP_DIR | awk '{print $1}')"
