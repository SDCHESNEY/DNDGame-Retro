#!/bin/bash
# Restore Docker volumes for LLM Dungeon Master

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/rpg_backup_*.tar.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🎲 Restoring LLM Dungeon Master"
echo "================================"
echo "⚠️  WARNING: This will overwrite current data!"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

TEMP_DIR=$(mktemp -d)

# Extract backup
echo "📦 Extracting backup..."
tar xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Stop containers
echo "⏸️  Stopping containers..."
docker-compose down

# Restore database
echo "💾 Restoring PostgreSQL database..."
docker-compose up -d db
sleep 5
docker-compose exec -T db psql -U rpguser rpg_dungeon < "$TEMP_DIR"/db_*.sql

# Restore volumes
echo "💾 Restoring Docker volumes..."
docker run --rm \
    -v rpg_dungeon_postgres_data:/postgres_data \
    -v rpg_dungeon_redis_data:/redis_data \
    -v rpg_dungeon_app_data:/app_data \
    -v "$TEMP_DIR:/backup" \
    alpine tar xzf /backup/volumes_*.tar.gz -C /

# Cleanup
rm -rf "$TEMP_DIR"

# Restart all services
echo "▶️  Restarting all services..."
docker-compose up -d

echo ""
echo "✅ Restore complete!"
echo "🔍 Verify with: curl http://localhost:8000/health"
