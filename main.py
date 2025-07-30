from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from data_transfer import PostgreSQLDataTransfer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PostgreSQL Data Transfer API", version="1.0.0")

# Add CORS middleware for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",  # Angular dev server
        "http://127.0.0.1:4200",  # Alternative localhost
        "http://localhost:3000",  # Alternative port
        "*"  # Allow all origins for development (restrict in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global transfer status tracking
transfer_status = {
    "is_running": False,
    "current_batch": 0,
    "total_rows": 0,
    "transferred_rows": 0,
    "start_time": None,
    "estimated_completion": None,
    "status": "idle",
    "error_message": None,
    "logs": []
}

class SourceDatabaseConfig(BaseModel):
    host: str = Field(..., description="Source database host")
    port: int = Field(5432, description="Source database port")
    database: str = Field(..., description="Source database name")
    user: str = Field(..., description="Source database username")
    password: str = Field(..., description="Source database password")

class DestinationDatabaseConfig(BaseModel):
    host: str = Field(..., description="Destination database host")
    port: int = Field(5432, description="Destination database port")
    database: str = Field(..., description="Destination database name")
    user: str = Field(..., description="Destination database username")
    password: str = Field(..., description="Destination database password")

class TransferConfig(BaseModel):
    table_name: str = Field(..., description="Source table name")
    warehouse_table: str = Field(..., description="Destination table name")
    source_db_schema: str = Field("public", description="Source database schema")
    dest_db_schema: str = Field("my", description="Destination database schema")
    batch_size: int = Field(10000, description="Batch size for transfer")
    transfer_mode: str = Field("full", description="Transfer mode: full, daily, or custom")
    date_filter: Optional[str] = Field(None, description="Custom date filter for data")
    ssl_mode: str = Field("require", description="SSL mode for connections")
    verify_transfer: bool = Field(True, description="Verify transfer after completion")

class DataTransferRequest(BaseModel):
    source_db: SourceDatabaseConfig
    dest_db: DestinationDatabaseConfig
    transfer_config: TransferConfig

class TransferResponse(BaseModel):
    message: str
    transfer_id: str
    status: str

class StatusResponse(BaseModel):
    is_running: bool
    current_batch: int
    total_rows: int
    transferred_rows: int
    progress_percentage: float
    start_time: Optional[str]
    estimated_completion: Optional[str]
    status: str
    error_message: Optional[str]
    logs: list

def set_environment_variables(config: DataTransferRequest):
    """Set environment variables from the request configuration"""
    # Source database
    os.environ['SOURCE_HOST'] = config.source_db.host
    os.environ['SOURCE_PORT'] = str(config.source_db.port)
    os.environ['SOURCE_DB'] = config.source_db.database
    os.environ['SOURCE_USER'] = config.source_db.user
    os.environ['SOURCE_PASSWORD'] = config.source_db.password
    
    # Destination database
    os.environ['DEST_HOST'] = config.dest_db.host
    os.environ['DEST_PORT'] = str(config.dest_db.port)
    os.environ['DEST_DB'] = config.dest_db.database
    os.environ['DEST_USER'] = config.dest_db.user
    os.environ['DEST_PASSWORD'] = config.dest_db.password
    
    # Transfer configuration
    os.environ['TABLE_NAME'] = config.transfer_config.table_name
    os.environ['WAREHOUSE_TABLE'] = config.transfer_config.warehouse_table
    os.environ['SOURCE_DB_SCHEMA'] = config.transfer_config.source_db_schema
    os.environ['DEST_DB_SCHEMA'] = config.transfer_config.dest_db_schema
    os.environ['BATCH_SIZE'] = str(config.transfer_config.batch_size)
    os.environ['TRANSFER_MODE'] = config.transfer_config.transfer_mode
    os.environ['SSL_MODE'] = config.transfer_config.ssl_mode
    os.environ['VERIFY_TRANSFER'] = str(config.transfer_config.verify_transfer).lower()
    
    if config.transfer_config.date_filter:
        os.environ['DATE_FILTER'] = config.transfer_config.date_filter

def run_data_transfer(config: DataTransferRequest):
    """Run the data transfer in a separate thread"""
    global transfer_status
    
    try:
        transfer_status.update({
            "is_running": True,
            "status": "initializing",
            "start_time": datetime.now().isoformat(),
            "error_message": None,
            "logs": [],
            "transferred_rows": 0  # Reset transferred rows
        })
        
        # Set environment variables
        set_environment_variables(config)
        
        # Create transfer instance
        transfer = PostgreSQLDataTransfer()
        
        # Create warehouse table if needed
        transfer_status["status"] = "creating_tables"
        transfer_status["logs"].append(f"{datetime.now().isoformat()}: Creating warehouse table...")
        transfer.create_warehouse_table_if_not_exists(None)
        
        # Get total rows for progress tracking
        transfer_status["status"] = "counting_rows"
        transfer_status["logs"].append(f"{datetime.now().isoformat()}: Counting total rows...")
        
        date_filter = config.transfer_config.date_filter if config.transfer_config.date_filter else None
        total_rows = transfer.get_total_rows(date_filter)
        transfer_status["total_rows"] = total_rows
        
        # Start transfer
        transfer_status["status"] = "transferring"
        transfer_status["logs"].append(f"{datetime.now().isoformat()}: Starting data transfer...")
        
        success = False
        mode = config.transfer_config.transfer_mode
        
        # Define a callback function to update progress
        def update_progress(transferred_count: int, batch_number: int):
            global transfer_status
            transfer_status["transferred_rows"] = transferred_count
            transfer_status["current_batch"] = batch_number
            logger.info(f" progress {transferred_count} :   ...")
            # Log progress update
            progress_percentage = (transferred_count / total_rows * 100) if total_rows > 0 else 0
            transfer_status["logs"].append(f"{datetime.now().isoformat()}: Progress - {transferred_count:,}/{total_rows:,} rows ({progress_percentage:.1f}%) - Batch {batch_number}")
            logger.info(f" progress percentage{progress_percentage} : ...")
            # Calculate estimated completion time
            if transferred_count > 0 and transfer_status["start_time"]:
                elapsed_time = (datetime.now() - datetime.fromisoformat(transfer_status["start_time"])).total_seconds()
                if elapsed_time > 0:
                    rows_per_second = transferred_count / elapsed_time
                    remaining_rows = total_rows - transferred_count
                    if rows_per_second > 0:
                        remaining_seconds = remaining_rows / rows_per_second
                        estimated_completion = datetime.now() + timedelta(seconds=remaining_seconds)
                        transfer_status["estimated_completion"] = estimated_completion.isoformat()
        
        if mode == 'daily':
            success = transfer.daily_incremental_transfer(progress_callback=update_progress)
        elif mode == 'full':
            success = transfer.full_transfer(progress_callback=update_progress)
        elif mode == 'custom':
            success = transfer.transfer_batch_copy(date_filter, mode='incremental', progress_callback=update_progress)
        
        if success:
            transfer_status["status"] = "verifying" if config.transfer_config.verify_transfer else "completed"
            transfer_status["logs"].append(f"{datetime.now().isoformat()}: Transfer completed successfully!")
            
            # Verify if requested
            if config.transfer_config.verify_transfer:
                transfer_status["logs"].append(f"{datetime.now().isoformat()}: Verifying transfer...")
                if transfer.verify_transfer(date_filter):
                    transfer_status["status"] = "completed"
                    transfer_status["logs"].append(f"{datetime.now().isoformat()}: Verification passed!")
                else:
                    transfer_status["status"] = "verification_failed"
                    transfer_status["logs"].append(f"{datetime.now().isoformat()}: Verification failed!")
        else:
            transfer_status["status"] = "failed"
            transfer_status["error_message"] = "Data transfer failed"
            transfer_status["logs"].append(f"{datetime.now().isoformat()}: Transfer failed!")
            
    except Exception as e:
        transfer_status["status"] = "error"
        transfer_status["error_message"] = str(e)
        transfer_status["logs"].append(f"{datetime.now().isoformat()}: Error: {str(e)}")
        logger.error(f"Transfer error: {e}")
    finally:
        transfer_status["is_running"] = False

@app.get("/")
async def root():
    return {"message": "PostgreSQL Data Transfer API"}

@app.post("/transfer/start", response_model=TransferResponse)
async def start_transfer(config: DataTransferRequest, background_tasks: BackgroundTasks):
    """Start a data transfer job"""
    global transfer_status
    
    if transfer_status["is_running"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transfer already in progress"
        )
    
    # Reset status
    transfer_status = {
        "is_running": False,
        "current_batch": 0,
        "total_rows": 0,
        "transferred_rows": 0,
        "start_time": None,
        "estimated_completion": None,
        "status": "idle",
        "error_message": None,
        "logs": []
    }
    
    # Start transfer in background
    transfer_thread = threading.Thread(target=run_data_transfer, args=(config,))
    transfer_thread.daemon = True
    transfer_thread.start()
    
    return TransferResponse(
        message="Data transfer started successfully",
        transfer_id=f"transfer_{int(time.time())}",
        status="started"
    )

@app.get("/transfer/status", response_model=StatusResponse)
async def get_transfer_status():
    """Get current transfer status"""
    global transfer_status
    
    progress_percentage = 0
    if transfer_status["total_rows"] > 0 and transfer_status["transferred_rows"] >= 0:
        progress_percentage = (transfer_status["transferred_rows"] / transfer_status["total_rows"]) * 100
        # Ensure progress doesn't exceed 100%
        progress_percentage = min(progress_percentage, 100.0)
    
    return StatusResponse(
        is_running=transfer_status["is_running"],
        current_batch=transfer_status["current_batch"],
        total_rows=transfer_status["total_rows"],
        transferred_rows=transfer_status["transferred_rows"],
        progress_percentage=round(progress_percentage, 2),
        start_time=transfer_status["start_time"],
        estimated_completion=transfer_status["estimated_completion"],
        status=transfer_status["status"],
        error_message=transfer_status["error_message"],
        logs=transfer_status["logs"][-10:]  # Return last 10 log entries
    )

@app.post("/transfer/stop")
async def stop_transfer():
    """Stop the current transfer"""
    global transfer_status
    
    if not transfer_status["is_running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transfer is currently running"
        )
    
    # Note: This is a simple implementation. In production, you'd need
    # proper thread management and graceful shutdown
    transfer_status["status"] = "stopped"
    transfer_status["is_running"] = False
    transfer_status["logs"].append(f"{datetime.now().isoformat()}: Transfer stopped by user")
    
    return {"message": "Transfer stop requested"}

@app.get("/transfer/logs")
async def get_transfer_logs():
    """Get all transfer logs"""
    global transfer_status
    return {"logs": transfer_status["logs"]}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 