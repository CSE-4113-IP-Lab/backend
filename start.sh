#!/bin/bash

echo "🚀 Starting CSEDU Backend Services..."

# Start PostgreSQL databases
echo "📊 Starting PostgreSQL databases..."
docker-compose -f docker-compose-db.yml up -d

# Wait for databases
echo "⏳ Waiting for databases to be ready..."
sleep 15

# Start pgpool
echo "🏊 Starting pgpool-II..."
pgpool -n  &

# Wait for pgpool
echo "⏳ Waiting for pgpool to be ready..."
sleep 5

# Start FastAPI applications
echo "🚀 Starting FastAPI applications..."
docker-compose up -d

# Wait for apps to start
echo "⏳ Waiting for applications to start..."
sleep 10

echo "✅ All services started successfully!"
echo ""
echo "📊 Services running:"
echo "   - PostgreSQL: ports 5433, 5434, 5435"
echo "   - pgpool-II: port 9999"
echo "   - FastAPI Apps: ports 8001, 8002, 8003"
echo "   - Nginx: port 80"
echo ""
echo "🌐 Access your app at: http://localhost"
echo ""
echo "📝 Showing nginx logs (Press Ctrl+C to exit logs, services will keep running):"
echo "================================================================================================"

# Show nginx logs in real-time
docker-compose logs -f nginx
