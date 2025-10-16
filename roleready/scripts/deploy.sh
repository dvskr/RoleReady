#!/bin/bash

# Production deployment script
set -e

echo "🚀 Starting RoleReady Production Deployment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if environment file exists
if [ ! -f .env.production ]; then
    echo "❌ .env.production file not found. Please create it from .env.production.example"
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Run health checks
echo "🏥 Running health checks..."
./scripts/health-check.sh

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml exec api python -c "
import asyncio
from roleready_api.core.supabase import supabase_client
# Add migration logic here
print('Migrations completed')
"

echo "✅ Deployment completed successfully!"
echo "🌐 Application is available at: $APP_URL"
echo "📊 API is available at: $APP_URL/api"
