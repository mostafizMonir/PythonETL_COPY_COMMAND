import psycopg2
import pandas as pd
import logging
from datetime import datetime, timedelta
import time
import os
from typing import Optional, Tuple
import sys
from contextlib import contextmanager
import gc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_transfer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PostgreSQLDataTransfer:
    def __init__(self):
        # Source Database Configuration
        self.source_config = {
            'host': os.getenv('SOURCE_HOST', 'source-rds-endpoint.amazonaws.com'),
            'port': os.getenv('SOURCE_PORT', '5432'),
            'database': os.getenv('SOURCE_DB', 'source_database'),
            'user': os.getenv('SOURCE_USER', 'your_username'),
            'password': os.getenv('SOURCE_PASSWORD', 'your_password')
        }
        
        # Destination Database Configuration
        self.dest_config = {
            'host': os.getenv('DEST_HOST', 'warehouse-rds-endpoint.amazonaws.com'),
            'port': os.getenv('DEST_PORT', '5432'),
            'database': os.getenv('DEST_DB', 'warehouse_database'),
            'user': os.getenv('DEST_USER', 'warehouse_username'),
            'password': os.getenv('DEST_PASSWORD', 'warehouse_password')
        }
        
        # Transfer Configuration
        self.batch_size = int(os.getenv('BATCH_SIZE', '10000'))  # Process 10k rows at a time
        self.table_name = os.getenv('TABLE_NAME', 'your_table_name')
        self.warehouse_table = os.getenv('WAREHOUSE_TABLE', 'your_warehouse_table')
        self.source_db_schema = os.getenv('SOURCE_DB_SCHEMA', 'public')
        self.dest_db_schema = os.getenv('DEST_DB_SCHEMA', 'my')
        
    @contextmanager
    def get_connection(self, config: dict, autocommit: bool = False):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(**config)
            if autocommit:
                conn.autocommit = True
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_total_rows(self, date_filter: Optional[str] = None) -> int:
        """Get total number of rows to transfer"""
        query = f"SELECT COUNT(*) FROM {self.source_db_schema}.{self.table_name}"
        if date_filter:
            query += f" WHERE {date_filter}"
        
        with self.get_connection(self.source_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]

    def create_warehouse_table_if_not_exists(self, source_table_structure: str):
        """Create warehouse schema and table with the same structure as the source."""
        create_schema_query = f"CREATE SCHEMA IF NOT EXISTS {self.dest_db_schema};"
        
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.dest_db_schema}.{self.warehouse_table} AS
        SELECT * FROM {self.source_db_schema}.{self.table_name} WHERE 1=0;
        """
        
        try:
            with self.get_connection(self.dest_config, autocommit=True) as conn:
                with conn.cursor() as cursor:
                    # Create schema if it doesn't exist
                    logger.info(f"Ensuring schema '{self.dest_db_schema}' exists...")
                    cursor.execute(create_schema_query)
                    logger.info(f"Schema '{self.dest_db_schema}' is ready.")

                    # Check if table exists
                    cursor.execute(f"""
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = '{self.dest_db_schema}' AND table_name = '{self.warehouse_table}';
                    """)
                    
                    if not cursor.fetchone():
                        logger.info(f"Table '{self.warehouse_table}' not found in schema '{self.dest_db_schema}'. Creating...")
                        cursor.execute(create_table_query)
                        logger.info(f"Table '{self.warehouse_table}' created successfully.")
                    else:
                        logger.info(f"Table '{self.warehouse_table}' already exists in schema '{self.dest_db_schema}'.")

        except Exception as e:
            logger.error(f"Error during schema/table creation: {e}")
            raise

    def transfer_batch_copy(self, date_filter: Optional[str] = None, mode: str = 'incremental'):
        """
        Transfer data using COPY command for better performance
        Modes: 'full' - full transfer, 'incremental' - only new/updated records
        """
        start_time = time.time()
        
        try:
            # Get total rows
            total_rows = self.get_total_rows(date_filter)
            logger.info(f"Starting transfer of {total_rows:,} rows")
            
            if total_rows == 0:
                logger.info("No rows to transfer")
                return True
            
            # Build base query
            base_query = f"SELECT * FROM {self.source_db_schema}.{self.table_name}"
            if date_filter:
                base_query += f" WHERE {date_filter}"
           # base_query += " ORDER BY id"  # Assuming 'id' column exists for consistent ordering
            
            transferred_rows = 0
            batch_number = 1
            
            with self.get_connection(self.source_config) as source_conn:
                with self.get_connection(self.dest_config) as dest_conn:
                    
                    # Clear warehouse table if full transfer
                    if mode == 'full':
                        with dest_conn.cursor() as dest_cursor:
                            logger.info(f"TRUNCATE TABLE {self.dest_db_schema}.{self.warehouse_table}")
                            dest_cursor.execute(f"TRUNCATE TABLE {self.dest_db_schema}.{self.warehouse_table}")
                            dest_conn.commit()
                            logger.info("Warehouse table truncated for full transfer")
                    
                    # Process in batches
                    offset = 0
                    while offset < total_rows:
                        batch_start_time = time.time()                        
                       
                        # Fetch batch from source
                        query = f"{base_query} LIMIT {self.batch_size} OFFSET {offset}"
                        
                        logger.info(f" Batch {batch_number} : {query}")

                        with source_conn.cursor() as source_cursor:
                            source_cursor.execute(query)
                            batch_data = source_cursor.fetchall()
                            
                            if not batch_data:
                                break
                            
                            # Get column names
                            column_names = [desc[0] for desc in source_cursor.description]
                        
                        # Insert batch into warehouse using COPY
                        with dest_conn.cursor() as dest_cursor:
                            # Create a temporary table for batch processing
                            temp_table = f"temp_{self.warehouse_table}_{batch_number}"
                            
                            logger.info(f"Creating temp table : CREATE TEMP TABLE {temp_table} AS SELECT * FROM {self.dest_db_schema}.{self.warehouse_table} WHERE 1=0 ")
                            
                            # Create temp table with same structure
                            dest_cursor.execute(f"""
                                CREATE TEMP TABLE {temp_table} AS 
                                SELECT * FROM {self.dest_db_schema}.{self.warehouse_table} WHERE 1=0
                            """)
                            
                            # Use COPY to insert data efficiently
                            copy_query = f"COPY {temp_table} ({','.join(column_names)}) FROM STDIN WITH CSV"
                            
                            # Convert batch data to CSV format
                            import io
                            import csv
                            
                            output = io.StringIO()
                            writer = csv.writer(output)
                            for row in batch_data:
                                writer.writerow(row)
                            output.seek(0)
                            
                            logger.info(f" Batch {batch_number} :  copy expert executing...")

                            dest_cursor.copy_expert(copy_query, output)
                            
                            # Insert from temp table to main table (handling duplicates)
                            if mode == 'incremental':
                                # Assuming 'id' is the primary key
                                dest_cursor.execute(f"""
                                    INSERT INTO {self.dest_db_schema}.{self.warehouse_table} 
                                    SELECT * FROM {temp_table}
                                    ON CONFLICT (id) DO UPDATE SET
                                    updated_at = EXCLUDED.updated_at
                                """)
                            else:
                                logger.info(f" Batch {batch_number} :  INSERT INTO {self.dest_db_schema}.{self.warehouse_table} SELECT * FROM {temp_table}")
                                dest_cursor.execute(f"""
                                    INSERT INTO {self.dest_db_schema}.{self.warehouse_table} 
                                    SELECT * FROM {temp_table}
                                """)
                            
                            dest_conn.commit()
                        
                        transferred_rows += len(batch_data)
                        batch_time = time.time() - batch_start_time
                        
                        logger.info(
                            f"Batch {batch_number}: {len(batch_data):,} rows "
                            f"({transferred_rows:,}/{total_rows:,}) "
                            f"in {batch_time:.2f}s - "
                            f"{len(batch_data)/batch_time:.0f} rows/sec"
                        )
                        
                        offset += self.batch_size
                        batch_number += 1
                        
                        # Force garbage collection to manage memory
                        gc.collect()
            
            total_time = time.time() - start_time
            avg_speed = transferred_rows / total_time if total_time > 0 else 0
            
            logger.info(
                f"Transfer completed successfully! "
                f"{transferred_rows:,} rows in {total_time:.2f}s "
                f"(Average: {avg_speed:.0f} rows/sec)"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            return False

    def transfer_pandas_chunks(self, date_filter: Optional[str] = None):
        """Alternative method using pandas for complex transformations"""
        start_time = time.time()
        
        try:
            # Build query
            query = f"SELECT * FROM {self.source_db_schema}.{self.table_name}"
            if date_filter:
                query += f" WHERE {date_filter}"
            
            source_conn_str = f"postgresql://{self.source_config['user']}:{self.source_config['password']}@{self.source_config['host']}:{self.source_config['port']}/{self.source_config['database']}"
            dest_conn_str = f"postgresql://{self.dest_config['user']}:{self.dest_config['password']}@{self.dest_config['host']}:{self.dest_config['port']}/{self.dest_config['database']}"
            
            transferred_rows = 0
            chunk_number = 1
            
            # Process in chunks to manage memory
            for chunk in pd.read_sql(query, source_conn_str, chunksize=self.batch_size):
                chunk_start_time = time.time()
                
                # Apply any transformations here if needed
                # chunk = self.transform_data(chunk)
                
                # Insert chunk to warehouse
                chunk.to_sql(
                    self.warehouse_table,
                    dest_conn_str,
                    if_exists='append',
                    index=False,
                    method='multi'  # Faster inserts
                )
                
                transferred_rows += len(chunk)
                chunk_time = time.time() - chunk_start_time
                
                logger.info(
                    f"Chunk {chunk_number}: {len(chunk):,} rows "
                    f"in {chunk_time:.2f}s - "
                    f"{len(chunk)/chunk_time:.0f} rows/sec"
                )
                
                chunk_number += 1
                
                # Force garbage collection
                del chunk
                gc.collect()
            
            total_time = time.time() - start_time
            avg_speed = transferred_rows / total_time if total_time > 0 else 0
            
            logger.info(
                f"Pandas transfer completed! "
                f"{transferred_rows:,} rows in {total_time:.2f}s "
                f"(Average: {avg_speed:.0f} rows/sec)"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Pandas transfer failed: {e}")
            return False

    def daily_incremental_transfer(self):
        """Transfer only yesterday's data"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        date_filter = f"DATE(created_at) = '{yesterday}'"  # Adjust column name as needed
        
        logger.info(f"Starting daily incremental transfer for {yesterday}")
        return self.transfer_batch_copy(date_filter, mode='incremental')

    def full_transfer(self):
        """Transfer all data"""
        logger.info("Starting full data transfer")
        return self.transfer_batch_copy(mode='full')

    def verify_transfer(self, date_filter: Optional[str] = None) -> bool:
        """Verify the transfer by comparing row counts"""
        try:
            source_query = f"SELECT COUNT(*) FROM {self.source_db_schema}.{self.table_name}"
            warehouse_query = f"SELECT COUNT(*) FROM {self.dest_db_schema}.{self.warehouse_table}"
            
            if date_filter:
                source_query += f" WHERE {date_filter}"
                warehouse_query += f" WHERE {date_filter}"
            
            with self.get_connection(self.source_config) as source_conn:
                with source_conn.cursor() as cursor:
                    cursor.execute(source_query)
                    source_count = cursor.fetchone()[0]
            
            with self.get_connection(self.dest_config) as dest_conn:
                with dest_conn.cursor() as cursor:
                    cursor.execute(warehouse_query)
                    warehouse_count = cursor.fetchone()[0]
            
            logger.info(f"Verification - Source: {source_count:,}, Warehouse: {warehouse_count:,}")
            
            return source_count == warehouse_count
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

def main():
    """Main execution function"""
    transfer = PostgreSQLDataTransfer()
    transfer.create_warehouse_table_if_not_exists(None)
    
    # Choose transfer mode
    mode = os.getenv('TRANSFER_MODE', 'daily')  # 'daily', 'full', or 'custom'
    
    success = False
    
    if mode == 'daily':
        success = transfer.daily_incremental_transfer()
    elif mode == 'full':
        success = transfer.full_transfer()
    elif mode == 'custom':
        # Custom date range
        date_filter = "created_at >= '2024-01-01' AND created_at < '2024-02-01'"
        success = transfer.transfer_batch_copy(date_filter, mode='incremental')
    
    if success:
        logger.info("Data transfer completed successfully!")
        # Optionally verify the transfer
        if os.getenv('VERIFY_TRANSFER', 'false').lower() == 'true':
            if transfer.verify_transfer():
                logger.info("Transfer verification passed!")
            else:
                logger.warning("Transfer verification failed!")
    else:
        logger.error("Data transfer failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()


# requirements.txt content
"""
psycopg2-binary==2.9.9
pandas==2.1.4
python-dotenv==1.0.0
"""
