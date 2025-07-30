# Docker Quick Start Guide

🐳 **Run PostgreSQL Data Transfer API with Docker in 3 easy steps!**

## 📋 Prerequisites

1. **Docker Desktop** installed and running
   - Windows/Mac: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: Install Docker Engine and Docker Compose

2. **Database Access**: Ensure your PostgreSQL databases are accessible from your machine

## 🚀 3-Step Quick Start

### Step 1: Configure Database Connection

Create a `.env` file with your database details:

```bash
# Copy template
cp docker.env.template .env

# Edit with your credentials (Windows)
notepad .env

# Edit with your credentials (Linux/Mac)
nano .env
```

Example `.env` content:
```bash
SOURCE_HOST=your-source-database.amazonaws.com
SOURCE_DB=source_database
SOURCE_USER=your_username
SOURCE_PASSWORD=your_password

DEST_HOST=your-warehouse-database.amazonaws.com
DEST_DB=warehouse_database
DEST_USER=warehouse_username
DEST_PASSWORD=warehouse_password

TABLE_NAME=event_plan_member
WAREHOUSE_TABLE=event_plan_member
```

### Step 2: Start the API

**Windows (PowerShell):**
```powershell
.\docker-start.ps1
```

**Linux/Mac:**
```bash
./docker-start.sh
```

**Or manually:**
```bash
docker compose up -d data-transfer-api
```

### Step 3: Access the Services

- **Web UI**: Start Angular frontend → http://localhost:4200
- **API Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎯 Complete Example

```bash
# 1. Configure
cp docker.env.template .env
# Edit .env with your database details

# 2. Start API
docker compose up -d data-transfer-api

# 3. Start frontend (separate terminal)
cd frontend
npm install
npm start

# 4. Access web app at http://localhost:4200
```

## 🛠️ Common Commands

```bash
# View logs
docker compose logs -f data-transfer-api

# Stop service
docker compose down

# Restart service
docker compose restart data-transfer-api

# Rebuild and start
docker compose up --build data-transfer-api

# Check service status
docker compose ps
```

## 🔍 Troubleshooting

**API not accessible?**
- Ensure Docker Desktop is running
- Check: `docker compose ps`
- View logs: `docker compose logs data-transfer-api`

**Database connection issues?**
- Verify credentials in `.env` file
- Test connectivity: `docker compose exec data-transfer-api ping your-db-host`

**Port 8000 in use?**
- Stop other services using port 8000
- Or change port in `docker-compose.yml`

## ✅ Success Indicators

When running correctly, you should see:
- ✅ Container status: `Up` in `docker compose ps`
- ✅ Health check: `curl http://localhost:8000/health` returns 200
- ✅ API docs accessible at http://localhost:8000/docs
- ✅ Angular app can connect to the API

## 📚 Full Documentation

For detailed setup and configuration options, see:
- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Comprehensive Docker guide
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Full application setup

---

**🎉 That's it! Your PostgreSQL Data Transfer API is now running in Docker and ready to use with the web interface.** 