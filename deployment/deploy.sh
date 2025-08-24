#!/bin/bash

# EIA-ADK Deployment Script
# Quick and easy deployment of MCP servers and EIA agent

set -e

echo "🚀 EIA-ADK Deployment Script"
echo "==============================="

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f env.template ]; then
        cp env.template .env
        echo "✅ Created .env file from template"
        echo "📝 Please edit .env file with your actual configuration values"
        echo "   Required: GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_KEY"
        echo "   Optional: NEO4J_PASSWORD (will use default if not set)"
        echo ""
        read -p "Press Enter after configuring .env file..." -r
    else
        echo "❌ env.template not found. Please create .env file manually."
        exit 1
    fi
fi

# Load environment variables
source .env

# Validate required environment variables
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ]; then
    echo "❌ GOOGLE_API_KEY is not set in .env file"
    exit 1
fi

if [ -z "$SUPABASE_URL" ] || [ "$SUPABASE_URL" = "https://your-project-ref.supabase.co" ]; then
    echo "❌ SUPABASE_URL is not set in .env file"
    exit 1
fi

if [ -z "$SUPABASE_ANON_KEY" ] || [ "$SUPABASE_ANON_KEY" = "your_supabase_anon_key_here" ]; then
    echo "❌ SUPABASE_ANON_KEY is not set in .env file"
    exit 1
fi

# Set default Neo4j password if not provided
if [ -z "$NEO4J_PASSWORD" ] || [ "$NEO4J_PASSWORD" = "your_secure_neo4j_password_here" ]; then
    export NEO4J_PASSWORD="neo4j-password-$(date +%s)"
    echo "⚠️  Using generated Neo4j password: $NEO4J_PASSWORD"
    # Update .env file with generated password
    sed -i.bak "s/NEO4J_PASSWORD=.*/NEO4J_PASSWORD=$NEO4J_PASSWORD/" .env
fi

echo "📦 Building Docker images..."
docker-compose build

echo "🔧 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

services=("eia-agent:8000" "geo-mcp:8765" "neo4j:7474")
for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1 || 
       curl -f -s "http://localhost:$port/tools/ping" > /dev/null 2>&1 ||
       curl -f -s "http://localhost:$port" > /dev/null 2>&1; then
        echo "✅ $name is healthy on port $port"
    else
        echo "⚠️  $name might not be ready yet on port $port"
    fi
done

echo ""
echo "🎉 Deployment completed!"
echo "==============================="
echo "📋 Service URLs:"
echo "   • EIA Agent API:     http://localhost (via nginx)"
echo "   • EIA Agent Direct:  http://localhost:8000"
echo "   • Geo MCP Server:    http://localhost:8765"
echo "   • Neo4j MCP Server:  http://localhost:8766" 
echo "   • Neo4j Web UI:      http://localhost:7474"
echo "   • Nginx Proxy:       http://localhost:80"
echo ""
echo "📖 API Documentation:"
echo "   • EIA Agent:         http://localhost:8000/docs"
echo "   • Health Check:      http://localhost/health"
echo ""
echo "🔧 Management Commands:"
echo "   • View logs:         docker-compose logs -f [service]"
echo "   • Stop services:     docker-compose down"
echo "   • Restart service:   docker-compose restart [service]"
echo "   • Update services:   docker-compose pull && docker-compose up -d"
echo ""
echo "🔐 Neo4j Credentials:"
echo "   • Username: neo4j"
echo "   • Password: $NEO4J_PASSWORD"
echo ""

# Test the main API
echo "🧪 Testing EIA Agent API..."
if curl -f -s "http://localhost:8000/health" | grep -q "healthy"; then
    echo "✅ EIA Agent API is responding correctly"
else
    echo "⚠️  EIA Agent API test failed - check logs with: docker-compose logs eia-agent"
fi

echo ""
echo "🔥 Ready to use! Try making a request:"
echo "curl -X POST 'http://localhost:8000/pipeline/run' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"project_path\":\"data/sample_project/lines.geojson\",\"target_layers\":[\"hydro.rivers\",\"ecosystems\"]}'"
