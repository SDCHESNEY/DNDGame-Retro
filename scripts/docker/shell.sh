#!/bin/bash
# Open a shell in the API container

SERVICE="${1:-api}"

echo "🎲 Opening shell in container: $SERVICE"

docker-compose exec "$SERVICE" /bin/bash
