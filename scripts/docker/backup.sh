#!/bin/bash
# Backup Docker volumes for LLM Dungeon Master

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/rpg_backup_${TIMESTAMP}.tar.gz"

echo "🎲 Backing up LLM Dungeon Master"
echo "================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Stop containers gracefully
echo "⏸️  Stopping containers..."
docker-compose stop

# Backup PostgreSQL
echo "💾 Backing up PostgreSQL database..."
docker-compose run --rm db pg_dump -U rpguser rpg_dungeon > "${BACKUP_DIR}/db_${TIMESTAMP}.sql"

# Backup volumes
echo "💾 Backing up Docker volumes..."
docker run --rm \
    -v rpg_dungeon_postgres_data:/postgres_data \
    -v rpg_dungeon_redis_data:/redis_data \
    -v rpg_dungeon_app_data:/app_data \
    -v "$(pwd)/${BACKUP_DIR}:/backup" \
    alpine tar czf "/backup/volumes_${TIMESTAMP}.tar.gz" \
    /postgres_data /redis_data /app_data

# Create combined backup
echo "📦 Creating combined backup..."
tar czf "$BACKUP_FILE" -C "$BACKUP_DIR" "db_${TIMESTAMP}.sql" "volumes_${TIMESTAMP}.tar.gz"

# Cleanup temporary files
rm "${BACKUP_DIR}/db_${TIMESTAMP}.sql"
rm "${BACKUP_DIR}/volumes_${TIMESTAMP}.tar.gz"

# Restart containers
echo "▶️  Restarting containers..."
docker-compose start

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo ""
echo "✅ Backup complete!"
echo "📁 File: $BACKUP_FILE"
echo "💾 Size: $BACKUP_SIZE"
echo ""
echo "To restore: ./scripts/docker/restore.sh $BACKUP_FILE"
