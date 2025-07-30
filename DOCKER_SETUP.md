# PostgreSQL Data Transfer - Docker Setup Guide

This guide shows you how to run the FastAPI backend using Docker Compose, making deployment and development much easier.

## 🐳 Docker Setup

### Prerequisites
- **Docker** and **Docker Compose** installed on your system
- **PostgreSQL** databases (source and destination) accessible from your Docker host

### Quick Start

1. **Clone or ensure you have the project files**
2. **Configure your database connections** (see Configuration section below)
3. **Run with Docker Compose**:

```bash
# Start the FastAPI backend
docker compose up data-transfer-api

# Or run in background
docker compose up -d data-transfer-api
```

4. **Access the services**:
   - **FastAPI Backend**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

## 🔧 Configuration Options

### Option 1: Using Environment File (.env)

Create a `.env` file in the project root:

```bash
# Copy the template
cp docker.env.template .env

# Edit with your actual database credentials
nano .env  # or your preferred editor
```

Example `.env` file:
```bash
SOURCE_HOST=source-rds-endpoint.amazonaws.com
SOURCE_PORT=5432
SOURCE_DB=source_database
SOURCE_USER=your_username
SOURCE_PASSWORD=your_password

DEST_HOST=warehouse-rds-endpoint.amazonaws.com
DEST_PORT=5432
DEST_DB=warehouse_database
DEST_USER=warehouse_username
DEST_PASSWORD=warehouse_password

TABLE_NAME=event_plan_member
WAREHOUSE_TABLE=event_plan_member
BATCH_SIZE=10000
SSL_MODE=require
```

### Option 2: Environment Variables

Set environment variables directly:

```bash
export SOURCE_HOST=your-source-host
export SOURCE_DB=your-source-db
export SOURCE_USER=your-username
export SOURCE_PASSWORD=your-password
# ... etc

docker compose up data-transfer-api
```

### Option 3: Inline with Docker Compose

```bash
SOURCE_HOST=your-host SOURCE_DB=your-db docker compose up data-transfer-api
```

## 📋 Available Docker Compose Configurations

### 1. Production Setup (`docker-compose.yml`)
```bash
# Start FastAPI backend only
docker compose up data-transfer-api

# Start original CLI transfer (if needed)
docker compose --profile cli up postgres-data-transfer
```

### 2. Development Setup (`docker-compose.dev.yml`)
```bash
# Development with hot reload
docker compose -f docker-compose.dev.yml up

# This includes volume mounting for live code changes
```

## 🚀 Common Commands

### Starting Services
```bash
# Start and view logs
docker compose up data-transfer-api

# Start in background
docker compose up -d data-transfer-api

# Start with specific compose file
docker compose -f docker-compose.dev.yml up
```

### Monitoring
```bash
# View logs
docker compose logs data-transfer-api

# Follow logs
docker compose logs -f data-transfer-api

# Check service status
docker compose ps
```

### Stopping Services
```bash
# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v

# Stop specific service
docker compose stop data-transfer-api
```

### Rebuilding
```bash
# Rebuild and start
docker compose up --build data-transfer-api

# Force rebuild
docker compose build --no-cache data-transfer-api
```

## 🌐 Using with Angular Frontend

The FastAPI backend in Docker will be accessible at `http://localhost:8000`. Your Angular frontend can connect to it:

1. **Start the containerized backend**:
```bash
docker compose up -d data-transfer-api
```

2. **Start the Angular frontend** (in a separate terminal):
```bash
cd frontend
npm install
npm start
```

3. **Access the web application**: http://localhost:4200

## 🔍 Troubleshooting

### Common Issues

1. **Port 8000 already in use**:
```bash
# Check what's using the port
netstat -tulpn | grep 8000
# or
lsof -i :8000

# Stop other services or change port in docker-compose.yml
```

2. **Database connection errors**:
   - Verify your database credentials in `.env`
   - Ensure databases are accessible from your Docker host
   - Check network connectivity with `docker compose exec data-transfer-api ping your-db-host`

3. **Container won't start**:
```bash
# Check logs for errors
docker compose logs data-transfer-api

# Rebuild from scratch
docker compose down
docker compose build --no-cache data-transfer-api
docker compose up data-transfer-api
```

4. **Environment variables not loading**:
   - Ensure `.env` file is in the same directory as `docker-compose.yml`
   - Check file permissions: `chmod 644 .env`
   - Verify syntax (no spaces around `=`)

### Health Checks

The FastAPI container includes health checks:
```bash
# Check container health
docker compose ps

# Manual health check
curl http://localhost:8000/health
```

### Debugging

```bash
# Access container shell
docker compose exec data-transfer-api bash

# Check environment variables
docker compose exec data-transfer-api env

# Test database connectivity
docker compose exec data-transfer-api psql -h $SOURCE_HOST -U $SOURCE_USER -d $SOURCE_DB -c "SELECT 1"
```

## 📁 File Structure

The Docker setup uses these files:
```
PythonETL_COPY_COMMAND/
├── docker-compose.yml          # Main compose file
├── docker-compose.dev.yml      # Development compose file
├── Dockerfile.api              # FastAPI container definition
├── docker.env.template         # Environment template
├── main.py                     # FastAPI application
├── data_transfer.py           # Transfer logic
├── api_requirements.txt       # Python dependencies
└── logs/                      # Log files (mounted volume)
```

## 🔒 Security Considerations

1. **Environment Files**: Never commit `.env` files with real credentials
2. **Network Access**: Ensure database hosts allow connections from your Docker host
3. **SSL/TLS**: Use SSL mode `require` for AWS RDS and other cloud databases
4. **Firewall**: Only expose necessary ports (8000 for FastAPI)

## 📈 Performance Tips

1. **Volume Mounting**: Logs are mounted to `./logs` for persistence
2. **Health Checks**: Built-in health monitoring for reliability
3. **Resource Limits**: Add resource limits in production:
```yaml
services:
  data-transfer-api:
    # ... other config
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

## 🎯 Production Deployment

For production deployment:

1. **Use specific image tags** instead of `latest`
2. **Set resource limits** and health checks
3. **Use secrets management** instead of environment files
4. **Configure reverse proxy** (nginx/traefik) for HTTPS
5. **Set up monitoring** and log aggregation
6. **Restrict CORS origins** in `main.py`

Example production override:
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  data-transfer-api:
    restart: always
    environment:
      - ENVIRONMENT=production
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: `docker compose logs data-transfer-api`
2. **Verify configuration**: Ensure all required environment variables are set
3. **Test connectivity**: Verify database access from the container
4. **Review documentation**: Check FastAPI docs at http://localhost:8000/docs 