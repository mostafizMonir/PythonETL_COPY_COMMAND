# Docker PostgreSQL Data Transfer - PowerShell Quick Start Script
Write-Host "🐳 Starting PostgreSQL Data Transfer API with Docker" -ForegroundColor Blue
Write-Host "==================================================" -ForegroundColor Blue

# Function to write colored output
function Write-ColorOutput($Message, $Color) {
    Write-Host $Message -ForegroundColor $Color
}

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-ColorOutput "❌ Docker is not running. Please start Docker Desktop and try again." "Red"
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-ColorOutput "⚠️  No .env file found. Creating from template..." "Yellow"
    if (Test-Path "docker.env.template") {
        Copy-Item "docker.env.template" ".env"
        Write-ColorOutput "📋 Please edit .env file with your database credentials before running:" "Blue"
        Write-ColorOutput "   notepad .env" "Yellow"
        Write-ColorOutput "   # or use your preferred editor" "Yellow"
        Write-Host ""
        exit 1
    } else {
        Write-ColorOutput "❌ Template file not found. Please create .env file manually." "Red"
        exit 1
    }
}

# Check if Docker Compose file exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-ColorOutput "❌ docker-compose.yml not found" "Red"
    exit 1
}

Write-ColorOutput "🔧 Building and starting FastAPI backend..." "Blue"

# Stop any existing containers
docker compose down data-transfer-api 2>$null

# Build and start the service
try {
    docker compose up --build -d data-transfer-api
    
    Write-Host ""
    Write-ColorOutput "🎉 FastAPI backend started successfully!" "Green"
    Write-Host "=================================================="
    Write-ColorOutput "📡 API Backend: http://localhost:8000" "Blue"
    Write-ColorOutput "📚 API Documentation: http://localhost:8000/docs" "Blue"
    Write-ColorOutput "🔍 Health Check: http://localhost:8000/health" "Blue"
    Write-Host ""
    Write-ColorOutput "📋 Useful commands:" "Yellow"
    Write-Host "• View logs: docker compose logs -f data-transfer-api"
    Write-Host "• Stop service: docker compose down"
    Write-Host "• Rebuild: docker compose up --build data-transfer-api"
    Write-Host ""
    Write-ColorOutput "🌐 Ready! You can now start your Angular frontend and access the web UI at http://localhost:4200" "Green"
    
    # Wait a moment and check if service is healthy
    Write-ColorOutput "⏳ Checking service health..." "Yellow"
    Start-Sleep -Seconds 5
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "✅ Service is healthy and ready!" "Green"
        } else {
            Write-ColorOutput "⚠️  Service may still be starting. Check logs if needed: docker compose logs data-transfer-api" "Yellow"
        }
    } catch {
        Write-ColorOutput "⚠️  Service may still be starting. Check logs if needed: docker compose logs data-transfer-api" "Yellow"
    }
    
} catch {
    Write-ColorOutput "❌ Failed to start FastAPI backend" "Red"
    Write-Host "Check the logs for errors:"
    Write-Host "docker compose logs data-transfer-api"
    exit 1
} 