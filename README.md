# PostgreSQL Data Transfer Tool

run this to view in console :  docker-compose run --rm --build -e TRANSFER_MODE=full postgres-data-transfer

A robust Python-based ETL tool for transferring data between PostgreSQL databases, with special optimizations for AWS RDS connections.

## Features

- **High Performance**: Uses PostgreSQL COPY command for efficient data transfer
- **Batch Processing**: Configurable batch sizes to manage memory usage
- **SSL Support**: Enhanced SSL configuration for AWS RDS connections
- **Retry Logic**: Automatic retry with exponential backoff for connection issues
- **Multiple Transfer Modes**: Full transfer, incremental transfer, and custom date ranges
- **Docker Support**: Containerized deployment with Docker Compose

## Quick Start

### 1. Environment Configuration

Create a `.env` file with your database configurations:

```bash
# Source Database (AWS RDS)
SOURCE_HOST=binsight-replica.c7sseomys1q4.af-south-1.rds.amazonaws.com
SOURCE_PORT=5432
SOURCE_DB=your_source_database
SOURCE_USER=your_username
SOURCE_PASSWORD=your_password

# Destination Database
DEST_HOST=your_destination_host
DEST_PORT=5432
DEST_DB=your_destination_database
DEST_USER=your_destination_username
DEST_PASSWORD=your_destination_password

# Transfer Configuration
TABLE_NAME=your_table_name
WAREHOUSE_TABLE=your_warehouse_table
BATCH_SIZE=10000
TRANSFER_MODE=full

# SSL Configuration for AWS RDS
SSL_MODE=require
```

### 2. Run the Transfer

```bash
# Full transfer
docker-compose run --rm --build -e TRANSFER_MODE=full postgres-data-transfer

# Daily incremental transfer
docker-compose run --rm --build -e TRANSFER_MODE=daily postgres-data-transfer
```

## AWS RDS SSL Connection Issues

### Problem
When connecting to AWS RDS instances, you may encounter SSL connection errors:
```
Database connection error: SSL connection has been closed unexpectedly.
```

### Solution

The tool now includes enhanced SSL handling for AWS RDS connections:

1. **Automatic SSL Detection**: The tool automatically detects AWS RDS endpoints and applies appropriate SSL settings
2. **Configurable SSL Modes**: You can specify different SSL modes via the `SSL_MODE` environment variable
3. **Retry Logic**: Automatic retry with exponential backoff for SSL connection failures
4. **Connection Keepalive**: Enhanced connection parameters to maintain stable connections

### SSL Mode Options

- `require` (default): Requires SSL but doesn't verify certificates
- `prefer`: Uses SSL if available, falls back to non-SSL
- `verify-ca`: Requires SSL and verifies server certificate
- `verify-full`: Requires SSL and verifies server certificate and hostname

### Testing SSL Connection

Use the included SSL test script to diagnose connection issues:

```bash
# Test SSL connection
docker-compose run --rm --build postgres-data-transfer python ssl_test.py
```

### Troubleshooting Steps

1. **Check Network Connectivity**:
   ```bash
   # Test basic connectivity
   telnet binsight-replica.c7sseomys1q4.af-south-1.rds.amazonaws.com 5432
   ```

2. **Verify Security Groups**: Ensure your AWS RDS security group allows connections from your source IP

3. **Check SSL Mode**: Try different SSL modes in your `.env` file:
   ```bash
   SSL_MODE=prefer    # Less strict
   SSL_MODE=require   # Default
   SSL_MODE=verify-ca # More strict
   ```

4. **Increase Timeouts**: If connections are timing out, the tool automatically uses longer timeouts for AWS RDS

5. **Check RDS Configuration**: Ensure your RDS instance has SSL enabled

### Common SSL Error Solutions

| Error | Solution |
|-------|----------|
| `SSL connection has been closed unexpectedly` | Use `SSL_MODE=require` or `SSL_MODE=prefer` |
| `connection timeout` | Increase `connect_timeout` in configuration |
| `certificate verify failed` | Use `SSL_MODE=require` instead of `verify-ca` |
| `hostname verification failed` | Use `SSL_MODE=verify-ca` instead of `verify-full` |

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SOURCE_HOST` | - | Source database host |
| `SOURCE_PORT` | 5432 | Source database port |
| `SOURCE_DB` | - | Source database name |
| `SOURCE_USER` | - | Source database user |
| `SOURCE_PASSWORD` | - | Source database password |
| `DEST_HOST` | - | Destination database host |
| `DEST_PORT` | 5432 | Destination database port |
| `DEST_DB` | - | Destination database name |
| `DEST_USER` | - | Destination database user |
| `DEST_PASSWORD` | - | Destination database password |
| `TABLE_NAME` | - | Source table name |
| `WAREHOUSE_TABLE` | - | Destination table name |
| `BATCH_SIZE` | 10000 | Number of rows to process per batch |
| `TRANSFER_MODE` | daily | Transfer mode (daily, full, custom) |
| `SSL_MODE` | require | SSL mode for AWS RDS connections |
| `VERIFY_TRANSFER` | true | Whether to verify transfer after completion |

### Transfer Modes

- **`full`**: Transfer all data from source to destination
- **`daily`**: Transfer only yesterday's data (incremental)
- **`custom`**: Transfer data based on custom date filters

## Performance Optimization

- **Batch Processing**: Adjust `BATCH_SIZE` based on your data size and memory constraints
- **COPY Command**: Uses PostgreSQL's COPY command for maximum performance
- **Memory Management**: Automatic garbage collection between batches
- **Connection Pooling**: Efficient connection management with retry logic

## Monitoring and Logging

The tool provides detailed logging for monitoring transfer progress:

- Transfer progress with row counts and timing
- SSL connection status and retry attempts
- Error details with stack traces
- Performance metrics (rows/second)

Logs are written to both console and `data_transfer.log` file.

## Security Considerations

- **SSL Encryption**: All AWS RDS connections use SSL encryption
- **Environment Variables**: Sensitive data stored in environment variables
- **Connection Timeouts**: Configurable timeouts to prevent hanging connections
- **Application Name**: Connections are tagged for monitoring

## Support

For issues with AWS RDS SSL connections:

1. Run the SSL test script: `python ssl_test.py`
2. Check your `.env` configuration
3. Verify network connectivity and security groups
4. Try different SSL modes
5. Check AWS RDS console for connection logs


finally run this :  docker-compose run --rm --build -e TRANSFER_MODE=full postgres-data-transfer