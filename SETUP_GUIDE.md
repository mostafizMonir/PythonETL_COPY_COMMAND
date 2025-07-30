# PostgreSQL Data Transfer - Setup Guide

This project provides a modern web interface for transferring data between PostgreSQL databases with recovery conflict handling and real-time monitoring.

## 📋 Prerequisites

- **Python 3.8+** for the FastAPI backend
- **Node.js 16+** and **npm** for the Angular frontend
- **PostgreSQL** databases (source and destination)

## 🚀 Quick Start

### Option 1: Docker (Recommended) 🐳

**Fastest way to get started:**

```bash
# 1. Configure database connection
cp docker.env.template .env
# Edit .env with your database credentials

# 2. Start FastAPI backend with Docker
docker compose up -d data-transfer-api

# 3. Start Angular frontend (separate terminal)
cd frontend
npm install
npm start

# 4. Access web app at http://localhost:4200
```

**Quick scripts:**
- Windows: `.\docker-start.ps1`
- Linux/Mac: `./docker-start.sh`

📚 **See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for detailed Docker instructions**

### Option 2: Local Development

#### 1. Backend Setup (FastAPI)

```bash
# Install Python dependencies
pip install -r api_requirements.txt

# Set environment variables (optional - can be configured via web UI)
export SOURCE_HOST=your-source-host
export SOURCE_DB=your-source-db
export SOURCE_USER=your-username
export SOURCE_PASSWORD=your-password

export DEST_HOST=your-warehouse-host
export DEST_DB=your-warehouse-db
export DEST_USER=your-warehouse-username
export DEST_PASSWORD=your-warehouse-password

# Start the FastAPI server
python main.py
```

The API will be available at: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### 2. Frontend Setup (Angular)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the Angular development server
npm start
```

The web application will be available at: `http://localhost:4200`

## 🌟 Features

### Web Interface
- **Modern UI** with Angular Material Design
- **Real-time Progress Monitoring** with live updates
- **Form Validation** with helpful error messages
- **Responsive Design** that works on all devices
- **Status Indicators** with color-coded progress

### Backend Capabilities
- **Recovery Conflict Handling** for read replicas
- **Cursor-based Pagination** for efficient large dataset transfers
- **Checkpointing System** to resume interrupted transfers
- **Real-time Status API** with progress tracking
- **Multiple Transfer Modes**: Full, Daily Incremental, Custom Date Range

### Configuration Options
- **Source & Destination Databases**: Host, port, database, credentials
- **Transfer Settings**: Table names, schemas, batch size
- **Advanced Options**: SSL mode, transfer mode, date filters
- **Verification**: Optional post-transfer verification

## 📱 Using the Web Interface

### 1. Configure Databases

1. **Source Database Section**:
   - Enter your source PostgreSQL connection details
   - Host, port, database name, username, password

2. **Destination Database Section**:
   - Enter your warehouse PostgreSQL connection details
   - Similar fields as source database

### 2. Transfer Settings

1. **Table Configuration**:
   - Source table name (e.g., `event_plan_member`)
   - Destination table name (usually the same)
   - Source and destination schemas

2. **Performance Settings**:
   - Batch size (recommended: 5000-10000 for large tables)
   - SSL mode for AWS RDS connections

3. **Transfer Mode**:
   - **Full Transfer**: Complete table copy
   - **Daily Incremental**: Yesterday's data only
   - **Custom**: Specify date filter (e.g., `created_at >= '2024-01-01'`)

### 3. Start Transfer

1. Fill in all required fields
2. Click **"Start Transfer"** button
3. Monitor real-time progress in the status card
4. View live logs and transfer statistics

### 4. Monitor Progress

The status card shows:
- Current transfer status
- Progress bar with percentage
- Rows transferred vs total rows
- Start time and estimated completion
- Recent log entries
- Any error messages

## 🔧 API Endpoints

### Transfer Management
- `POST /transfer/start` - Start a new transfer
- `GET /transfer/status` - Get current transfer status
- `POST /transfer/stop` - Stop current transfer
- `GET /transfer/logs` - Get all transfer logs

### Monitoring
- `GET /health` - Health check
- `GET /` - API information

## 📊 Recovery Conflict Handling

The system automatically handles PostgreSQL recovery conflicts with:

1. **Automatic Detection** of conflict errors
2. **Exponential Backoff** retry strategy
3. **Connection Reconnection** after conflicts
4. **Cursor-based Pagination** to avoid large offsets
5. **Configurable Retry Limits** and delays

## 🛠️ Troubleshooting

### Common Issues

1. **"Unable to connect to server"**
   - Ensure FastAPI server is running on `http://localhost:8000`
   - Check if port 8000 is available

2. **Database Connection Errors**
   - Verify database credentials and connection details
   - Check network connectivity to database hosts
   - Ensure databases are accessible from your machine

3. **Transfer Fails with Recovery Conflicts**
   - The system handles these automatically with retries
   - Consider reducing batch size for busy read replicas
   - Monitor logs for detailed error information

4. **Frontend Not Loading**
   - Ensure Angular dev server is running on port 4200
   - Check for any console errors in browser developer tools
   - Verify all npm dependencies are installed

### Configuration Tips

1. **For Large Tables**:
   - Use smaller batch sizes (2000-5000)
   - Enable cursor pagination (default)
   - Consider running during off-peak hours

2. **For AWS RDS**:
   - Use SSL mode "require"
   - Increase timeout settings if needed
   - Monitor CloudWatch metrics during transfer

3. **For High Availability**:
   - Use checkpointing (enabled by default)
   - Monitor transfer logs for any issues
   - Set up proper error alerting

## 📝 Development

### Backend Development
```bash
# Install development dependencies
pip install -r api_requirements.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server with auto-reload
ng serve --open
```

## 🔒 Security Considerations

1. **Credentials**: Never commit database passwords to version control
2. **Network**: Ensure secure connections to databases (SSL/TLS)
3. **Access**: Restrict API access in production environments
4. **Monitoring**: Monitor transfer logs for any security issues

## 📈 Performance Tips

1. **Batch Size**: Start with 10000, reduce if encountering conflicts
2. **Network**: Ensure good network connectivity between source and destination
3. **Resources**: Monitor CPU and memory usage during large transfers
4. **Timing**: Consider running large transfers during off-peak hours

## 🤝 Support

For issues or questions:
1. Check the browser console for frontend errors
2. Review FastAPI logs for backend issues
3. Monitor database logs for connection problems
4. Use the health check endpoint to verify API status 