#!/bin/bash
# View logs from Docker containers

SERVICE="${1:-api}"

echo "🎲 LLM Dungeon Master - Docker Logs"
echo "===================================="

if [ "$SERVICE" == "all" ]; then
    echo "Showing logs for all services..."
    docker-compose logs -f
else
    echo "Showing logs for: $SERVICE"
    echo "(Use 'all' to see all services)"
    docker-compose logs -f "$SERVICE"
fi
