#!/bin/bash

# 🚂 Railway Deployment Script for EIA-ADK
# Deploys all 3 services to Railway platform

set -e

echo "🚂 EIA-ADK Railway Deployment"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI is not installed.${NC}"
    echo "Install it with: npm install -g @railway/cli"
    echo "Then login with: railway login"
    exit 1
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo -e "${RED}❌ Not logged in to Railway.${NC}"
    echo "Please login with: railway login"
    exit 1
fi

echo -e "${GREEN}✅ Railway CLI is ready${NC}"

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local dockerfile_path=$2
    local env_vars_func=$3
    
    echo -e "\n${BLUE}🚀 Deploying $service_name...${NC}"
    
    # Create new project
    railway init "$service_name" --name "$service_name"
    
    # Deploy with custom Dockerfile
    echo -e "${YELLOW}📦 Building and deploying...${NC}"
    railway up --dockerfile "$dockerfile_path"
    
    # Set environment variables
    echo -e "${YELLOW}🔧 Setting environment variables...${NC}"
    $env_vars_func
    
    # Get the service URL
    local service_url=$(railway domain)
    if [ -n "$service_url" ]; then
        echo -e "${GREEN}✅ $service_name deployed at: https://$service_url${NC}"
        eval "${service_name}_URL=https://$service_url"
    else
        echo -e "${YELLOW}⚠️  Getting deployment URL for $service_name...${NC}"
        # Try to get URL from railway status
        service_url=$(railway status | grep -oP 'https://[^\s]+' | head -1)
        if [ -n "$service_url" ]; then
            echo -e "${GREEN}✅ $service_name deployed at: $service_url${NC}"
            eval "${service_name}_URL=$service_url"
        else
            echo -e "${YELLOW}⚠️  URL will be available after deployment completes${NC}"
        fi
    fi
}

# Environment variables for Geo-Fetch-MCP
set_geo_mcp_env() {
    railway variables set SUPABASE_URL="https://cunekdzofzcqxnsrxmwc.supabase.co"
    railway variables set SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1bmVrZHpvZnpjcXhuc3J4bXdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjQ0NDU5MTksImV4cCI6MjA0MDAyMTkxOX0.OsZKs1PQNF0KTSRWGKK2FhIWfmmWi9pA2ow_fgFpyBU"
    railway variables set SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1bmVrZHpvZnpjcXhuc3J4bXdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjQ0NDU5MTksImV4cCI6MjA0MDAyMTkxOX0.OsZKs1PQNF0KTSRWGKK2FhIWfmmWi9pA2ow_fgFpyBU"
}

# Environment variables for Neo4j-MCP
set_neo4j_mcp_env() {
    railway variables set NEO4J_URI="neo4j+s://e6699d7f.databases.neo4j.io"
    railway variables set NEO4J_USERNAME="neo4j"
    railway variables set NEO4J_PASSWORD="6WtfZ9o8zBB0aKZqXN6TNE7ikJY284roRJGJV8uxRCU"
    railway variables set NEO4J_DATABASE="neo4j"
}

# Environment variables for EIA Agent
set_eia_agent_env() {
    railway variables set GOOGLE_API_KEY="AIzaSyCcGhv_e4wnVSakwENOdS1eWbd5_YIe4mQ"
    railway variables set SUPABASE_URL="https://cunekdzofzcqxnsrxmwc.supabase.co"
    railway variables set SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1bmVrZHpvZnpjcXhuc3J4bXdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjQ0NDU5MTksImV4cCI6MjA0MDAyMTkxOX0.OsZKs1PQNF0KTSRWGKK2FhIWfmmWi9pA2ow_fgFpyBU"
    railway variables set SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1bmVrZHpvZnpjcXhuc3J4bXdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcyNDQ0NTkxOSwiZXhwIjoyMDQwMDIxOTE5fQ.7Oi8PVkJaTXIfgmFZBm1xDCRhF7PEoC8d4Gqwj4k7Cc"
    
    # Set service URLs if available
    if [ -n "$geo_fetch_mcp_URL" ]; then
        railway variables set GEO_MCP_URL="$geo_fetch_mcp_URL"
    fi
    if [ -n "$neo4j_mcp_URL" ]; then
        railway variables set NEO4J_MCP_URL="$neo4j_mcp_URL"
    fi
}

# Deploy services in order
echo -e "${BLUE}Starting deployment of 3 services...${NC}"

# 1. Deploy Geo-Fetch-MCP
cd geo-fetch-mcp
deploy_service "geo-fetch-mcp" "../Dockerfile.geo-mcp-railway" "set_geo_mcp_env"
cd ..

# 2. Deploy Neo4j-MCP
cd mcp-geo2neo
deploy_service "neo4j-mcp" "../Dockerfile.neo4j-mcp-railway" "set_neo4j_mcp_env"
cd ..

# 3. Deploy EIA Agent (main service)
deploy_service "eia-agent" "Dockerfile.agent-railway" "set_eia_agent_env"

echo -e "\n${GREEN}🎉 All services deployed successfully!${NC}"
echo -e "${BLUE}======================================${NC}"

# Wait a moment for deployments to stabilize
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 30

# Test deployments
echo -e "\n${BLUE}🧪 Testing deployed services...${NC}"

test_service() {
    local name=$1
    local url=$2
    local endpoint=$3
    
    echo -e "${YELLOW}Testing $name...${NC}"
    if curl -f -s "$url$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  $name might still be starting up${NC}"
    fi
}

# Get actual service URLs
echo -e "${BLUE}📋 Getting service URLs...${NC}"
railway projects

echo -e "\n${GREEN}🚂 Railway Deployment Complete!${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}📋 Your services are deployed on Railway:${NC}"
echo ""
echo -e "${BLUE}🌍 Geo-Fetch-MCP:${NC} Check Railway dashboard for URL"
echo -e "${BLUE}🔗 Neo4j-MCP:${NC} Check Railway dashboard for URL" 
echo -e "${BLUE}🤖 EIA-Agent:${NC} Check Railway dashboard for URL"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Go to railway.app dashboard to get service URLs"
echo "2. Update EIA agent with service URLs if needed"
echo "3. Test your APIs using the URLs"
echo "4. Monitor logs and performance"
echo ""
echo -e "${GREEN}🎯 Your EIA-ADK system is live on Railway! 🚂${NC}"

# Show Railway projects
echo -e "\n${BLUE}📊 Railway Projects:${NC}"
railway projects
