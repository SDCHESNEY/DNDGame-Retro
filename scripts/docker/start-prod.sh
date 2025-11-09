#!/bin/bash
# Start LLM Dungeon Master in production mode

set -e

echo "🎲 Starting LLM Dungeon Master (Production Mode)"
echo "================================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Validate required environment variables
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  Warning: OPENAI_API_KEY not configured in .env"
fi

if grep -q "changeme" .env; then
    echo "⚠️  Warning: Default passwords detected in .env. Please change them!"
fi

# Build and start services
echo "🔨 Building Docker images (production)..."
docker-compose build api-prod

echo "🚀 Starting services..."
docker-compose --profile production up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo "🔍 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy!"
else
    echo "⚠️  API health check failed. Check logs with: docker-compose logs api-prod"
fi

echo ""
echo "✅ LLM Dungeon Master is running in PRODUCTION mode!"
echo "📡 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "🔍 Health: http://localhost:8000/health"
echo ""
echo "To stop: docker-compose --profile production down"
echo "To view logs: docker-compose logs -f api-prod"
