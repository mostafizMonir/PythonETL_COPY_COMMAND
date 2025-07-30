#!/bin/bash

# PostgreSQL Data Transfer - Service Stopper Script
# This script stops both the FastAPI backend and Angular frontend

echo "🛑 PostgreSQL Data Transfer - Stopping Services"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to stop a service by PID
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        echo -e "${YELLOW}Stopping $service_name (PID: $pid)...${NC}"
        
        if kill -0 "$pid" 2>/dev/null; then
            # Try graceful shutdown first
            kill "$pid"
            sleep 2
            
            # Check if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}Forcing shutdown of $service_name...${NC}"
                kill -9 "$pid"
                sleep 1
            fi
            
            # Verify it's stopped
            if ! kill -0 "$pid" 2>/dev/null; then
                echo -e "${GREEN}✅ $service_name stopped successfully${NC}"
                rm -f "$pid_file"
            else
                echo -e "${RED}❌ Failed to stop $service_name${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  $service_name was not running${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}⚠️  No PID file found for $service_name${NC}"
    fi
}

# Create logs directory if it doesn't exist
mkdir -p logs

# Stop backend service
stop_service "FastAPI Backend" "logs/backend.pid"

# Stop frontend service  
stop_service "Angular Frontend" "logs/frontend.pid"

# Also try to kill any remaining processes on the ports
echo ""
echo -e "${BLUE}Checking for remaining processes on ports 8000 and 4200...${NC}"

# Kill any process using port 8000 (FastAPI)
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Found process on port 8000, terminating...${NC}"
    lsof -ti:8000 | xargs kill -9 2>/dev/null
fi

# Kill any process using port 4200 (Angular)
if lsof -Pi :4200 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Found process on port 4200, terminating...${NC}"
    lsof -ti:4200 | xargs kill -9 2>/dev/null
fi

echo ""
echo -e "${GREEN}🎉 All services stopped!${NC}"
echo "=============================================="
echo -e "${BLUE}✅ Port 8000 (FastAPI) is now available${NC}"
echo -e "${BLUE}✅ Port 4200 (Angular) is now available${NC}"
echo ""
echo -e "${YELLOW}📋 Log files are preserved in the logs/ directory${NC}"
echo -e "${YELLOW}💡 To start services again, run:${NC} ./start_services.sh" 