#!/bin/bash

echo "🛑 Stopping CSEDU Backend Services..."

# Stop pgpool
echo "🏊 Stopping pgpool-II..."
sudo pkill -f pgpool 
sudo rm -f /opt/homebrew/var/run/pgpool.pid
sleep 2

# Stop FastAPI applications
echo "🚀 Stopping FastAPI applications..."
docker-compose down

# Stop PostgreSQL databases
echo "📊 Stopping PostgreSQL databases..."
docker-compose -f docker-compose-db.yml down --remove-orphans


docker system prune -f --volumes

# Clean up any dangling networks
echo "🌐 Cleaning up unused networks..."
docker network prune -f

echo "✅ All services stopped successfully!"
