#!/bin/bash
# Start LLM Dungeon Master in development mode with hot reload

set -e

echo "🎲 Starting LLM Dungeon Master (Development Mode)"
echo "================================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your configuration."
    echo "   Especially set your OPENAI_API_KEY!"
    exit 1
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build api

echo "🚀 Starting services..."
docker-compose up -d db redis
echo "⏳ Waiting for database and Redis to be ready..."
sleep 5

echo "🎮 Starting FastAPI server (development mode with hot reload)..."
docker-compose up api

echo ""
echo "✅ LLM Dungeon Master is running!"
echo "📡 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "🔍 Health: http://localhost:8000/health"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"
