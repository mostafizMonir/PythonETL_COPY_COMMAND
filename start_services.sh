#!/bin/bash

# PostgreSQL Data Transfer - Service Starter Script
# This script starts both the FastAPI backend and Angular frontend

echo "🚀 PostgreSQL Data Transfer - Starting Services"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Python
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Check Node.js
if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found${NC}"

# Check npm
if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ npm found${NC}"

echo ""

# Check if ports are available
if port_in_use 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use (FastAPI)${NC}"
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

if port_in_use 4200; then
    echo -e "${YELLOW}⚠️  Port 4200 is already in use (Angular)${NC}"
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${BLUE}Installing dependencies...${NC}"

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
if ! pip install -r api_requirements.txt; then
    echo -e "${RED}❌ Failed to install Python dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Install Angular dependencies
echo -e "${YELLOW}📦 Installing Angular dependencies...${NC}"
cd frontend
if ! npm install; then
    echo -e "${RED}❌ Failed to install Angular dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Angular dependencies installed${NC}"
cd ..

echo ""
echo -e "${BLUE}Starting services...${NC}"

# Create log directories
mkdir -p logs

# Function to start FastAPI backend
start_backend() {
    echo -e "${YELLOW}🔧 Starting FastAPI backend on port 8000...${NC}"
    python main.py > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > logs/backend.pid
    
    # Wait a moment for the server to start
    sleep 3
    
    # Check if the backend is running
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ FastAPI backend started successfully (PID: $BACKEND_PID)${NC}"
        echo -e "${BLUE}   📡 API available at: http://localhost:8000${NC}"
        echo -e "${BLUE}   📚 API docs at: http://localhost:8000/docs${NC}"
    else
        echo -e "${RED}❌ Failed to start FastAPI backend${NC}"
        cat logs/backend.log
        exit 1
    fi
}

# Function to start Angular frontend
start_frontend() {
    echo -e "${YELLOW}🎨 Starting Angular frontend on port 4200...${NC}"
    cd frontend
    npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    cd ..
    
    echo -e "${GREEN}✅ Angular frontend is starting (PID: $FRONTEND_PID)${NC}"
    echo -e "${BLUE}   🌐 Web app will be available at: http://localhost:4200${NC}"
    echo -e "${YELLOW}   ⏳ Please wait a moment for Angular to compile...${NC}"
}

# Start both services
start_backend
echo ""
start_frontend

echo ""
echo -e "${GREEN}🎉 Both services are starting!${NC}"
echo "=============================================="
echo -e "${BLUE}📡 FastAPI Backend:${NC} http://localhost:8000"
echo -e "${BLUE}🌐 Angular Frontend:${NC} http://localhost:4200"
echo -e "${BLUE}📚 API Documentation:${NC} http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}📋 Service Information:${NC}"
echo "• Backend logs: logs/backend.log"
echo "• Frontend logs: logs/frontend.log"
echo "• Backend PID: $(cat logs/backend.pid 2>/dev/null || echo 'N/A')"
echo "• Frontend PID: $(cat logs/frontend.pid 2>/dev/null || echo 'N/A')"
echo ""
echo -e "${YELLOW}⚠️  To stop services, run:${NC} ./stop_services.sh"
echo -e "${YELLOW}⚠️  Or manually kill the processes using the PIDs above${NC}"
echo ""
echo -e "${GREEN}🚀 Ready to transfer data! Open http://localhost:4200 in your browser${NC}" 