#!/bin/bash

# Docker PostgreSQL Data Transfer - Quick Start Script
echo "🐳 Starting PostgreSQL Data Transfer API with Docker"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    if [ -f "docker.env.template" ]; then
        cp docker.env.template .env
        echo -e "${BLUE}📋 Please edit .env file with your database credentials before running:${NC}"
        echo -e "${YELLOW}   nano .env${NC}"
        echo -e "${YELLOW}   # or use your preferred editor${NC}"
        echo ""
        exit 1
    else
        echo -e "${RED}❌ Template file not found. Please create .env file manually.${NC}"
        exit 1
    fi
fi

# Check if Docker Compose file exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ docker-compose.yml not found${NC}"
    exit 1
fi

echo -e "${BLUE}🔧 Building and starting FastAPI backend...${NC}"

# Stop any existing containers
docker compose down data-transfer-api 2>/dev/null

# Build and start the service
if docker compose up --build -d data-transfer-api; then
    echo ""
    echo -e "${GREEN}🎉 FastAPI backend started successfully!${NC}"
    echo "=================================================="
    echo -e "${BLUE}📡 API Backend:${NC} http://localhost:8000"
    echo -e "${BLUE}📚 API Documentation:${NC} http://localhost:8000/docs"
    echo -e "${BLUE}🔍 Health Check:${NC} http://localhost:8000/health"
    echo ""
    echo -e "${YELLOW}📋 Useful commands:${NC}"
    echo "• View logs: docker compose logs -f data-transfer-api"
    echo "• Stop service: docker compose down"
    echo "• Rebuild: docker compose up --build data-transfer-api"
    echo ""
    echo -e "${GREEN}🌐 Ready! You can now start your Angular frontend and access the web UI at http://localhost:4200${NC}"
    
    # Wait a moment and check if service is healthy
    echo -e "${YELLOW}⏳ Checking service health...${NC}"
    sleep 5
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service is healthy and ready!${NC}"
    else
        echo -e "${YELLOW}⚠️  Service may still be starting. Check logs if needed: docker compose logs data-transfer-api${NC}"
    fi
    
else
    echo -e "${RED}❌ Failed to start FastAPI backend${NC}"
    echo "Check the logs for errors:"
    echo "docker compose logs data-transfer-api"
    exit 1
fi 