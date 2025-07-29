#!/usr/bin/env python3
"""
SSL Connection Test Script for AWS RDS
This script helps diagnose SSL connection issues with AWS RDS instances.
"""

import psycopg2
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_connection(host, port, database, user, password, ssl_mode='require'):
    """Test database connection with different SSL modes"""
    
    config = {
        'host': host,
        'port': port,
        'database': database,
        'user': user,
        'password': password,
        'sslmode': ssl_mode,
        'connect_timeout': 30,
        'application_name': 'ssl-test'
    }
    
    logger.info(f"Testing connection to {host}:{port} with SSL mode: {ssl_mode}")
    
    try:
        conn = psycopg2.connect(**config)
        
        # Test the connection
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"✅ Connection successful! PostgreSQL version: {version}")
            
            # Test SSL status
            cursor.execute("SHOW ssl")
            ssl_status = cursor.fetchone()[0]
            logger.info(f"SSL Status: {ssl_status}")
            
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        logger.error(f"❌ Connection failed with SSL mode '{ssl_mode}': {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function to test connections"""
    
    # Get connection details from environment
    source_host = os.getenv('SOURCE_HOST')
    source_port = os.getenv('SOURCE_PORT', '5432')
    source_db = os.getenv('SOURCE_DB')
    source_user = os.getenv('SOURCE_USER')
    source_password = os.getenv('SOURCE_PASSWORD')
    
    if not all([source_host, source_db, source_user, source_password]):
        logger.error("Missing required environment variables. Please check your .env file.")
        sys.exit(1)
    
    logger.info("=== AWS RDS SSL Connection Test ===")
    logger.info(f"Host: {source_host}")
    logger.info(f"Database: {source_db}")
    logger.info(f"User: {source_user}")
    
    # Test different SSL modes
    ssl_modes = ['prefer', 'require', 'verify-ca', 'verify-full']
    
    for ssl_mode in ssl_modes:
        logger.info(f"\n--- Testing SSL mode: {ssl_mode} ---")
        success = test_connection(
            source_host, source_port, source_db, 
            source_user, source_password, ssl_mode
        )
        
        if success:
            logger.info(f"✅ SSL mode '{ssl_mode}' works! Use this in your configuration.")
            break
    else:
        logger.error("❌ All SSL modes failed. Please check your network and RDS configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main() 