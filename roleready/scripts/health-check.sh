#!/bin/bash

# Production health check script
set -e

echo "🔍 RoleReady Health Check Starting..."

# Check if services are running
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo "Checking $service_name at $url..."
    
    if curl -s -f -o /dev/null "$url"; then
        echo "✅ $service_name is healthy"
        return 0
    else
        echo "❌ $service_name is unhealthy"
        return 1
    fi
}

# Check API health
check_service "API" "http://localhost:8000/health"

# Check Web health
check_service "Web" "http://localhost:3000"

# Check database connection (if psql is available)
if command -v psql &> /dev/null; then
    echo "Checking database connection..."
    if psql "$DATABASE_URL" -c "SELECT 1;" &> /dev/null; then
        echo "✅ Database is healthy"
    else
        echo "❌ Database connection failed"
        exit 1
    fi
fi

# Check Redis connection (if redis-cli is available)
if command -v redis-cli &> /dev/null; then
    echo "Checking Redis connection..."
    if redis-cli -u "$REDIS_URL" ping &> /dev/null; then
        echo "✅ Redis is healthy"
    else
        echo "❌ Redis connection failed"
        exit 1
    fi
fi

echo "🎉 All health checks passed!"
exit 0
