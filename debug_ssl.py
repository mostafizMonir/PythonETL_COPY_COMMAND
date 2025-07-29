#!/usr/bin/env python3
"""
SSL Debug Script for AWS RDS
Provides detailed debugging information for SSL connection issues.
"""

import psycopg2
import os
import sys
import logging
import ssl
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_network_connectivity(host, port):
    """Test basic network connectivity"""
    logger.info(f"Testing network connectivity to {host}:{port}")
    
    try:
        sock = socket.create_connection((host, port), timeout=10)
        logger.info("✅ Network connectivity: SUCCESS")
        sock.close()
        return True
    except Exception as e:
        logger.error(f"❌ Network connectivity: FAILED - {e}")
        return False

def test_ssl_connection(host, port, database, user, password, ssl_mode='require'):
    """Test SSL connection with detailed error reporting"""
    
    config = {
        'host': host,
        'port': port,
        'database': database,
        'user': user,
        'password': password,
        'sslmode': ssl_mode,
        'connect_timeout': 30,
        'application_name': 'ssl-debug'
    }
    
    logger.info(f"Testing SSL connection with mode: {ssl_mode}")
    logger.info(f"Connection config: {host}:{port}/{database} (user: {user})")
    
    try:
        conn = psycopg2.connect(**config)
        
        # Test basic connection
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"✅ Connection successful! PostgreSQL version: {version}")
            
            # Check SSL status
            cursor.execute("SHOW ssl")
            ssl_status = cursor.fetchone()[0]
            logger.info(f"SSL Status: {ssl_status}")
            
            # Check SSL parameters
            cursor.execute("SHOW ssl_ciphers")
            ssl_ciphers = cursor.fetchone()[0]
            logger.info(f"SSL Ciphers: {ssl_ciphers}")
            
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        logger.error(f"❌ Operational Error: {e}")
        logger.error(f"Error code: {e.pgcode}")
        logger.error(f"Error message: {e.pgerror}")
        return False
        
    except psycopg2.InterfaceError as e:
        logger.error(f"❌ Interface Error: {e}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

def main():
    """Main debugging function"""
    
    # Get connection details
    source_host = os.getenv('SOURCE_HOST')
    source_port = int(os.getenv('SOURCE_PORT', '5432'))
    source_db = os.getenv('SOURCE_DB')
    source_user = os.getenv('SOURCE_USER')
    source_password = os.getenv('SOURCE_PASSWORD')
    
    if not all([source_host, source_db, source_user, source_password]):
        logger.error("Missing required environment variables")
        sys.exit(1)
    
    logger.info("=== AWS RDS SSL Debug Report ===")
    logger.info(f"Host: {source_host}")
    logger.info(f"Port: {source_port}")
    logger.info(f"Database: {source_db}")
    logger.info(f"User: {source_user}")
    
    # Test network connectivity first
    if not test_network_connectivity(source_host, source_port):
        logger.error("Network connectivity failed. Check:")
        logger.error("1. Security groups allow your IP")
        logger.error("2. RDS instance is running")
        logger.error("3. Network connectivity from your location")
        sys.exit(1)
    
    # Test different SSL modes
    ssl_modes = ['prefer', 'require', 'verify-ca', 'verify-full']
    
    for ssl_mode in ssl_modes:
        logger.info(f"\n--- Testing SSL mode: {ssl_mode} ---")
        success = test_ssl_connection(
            source_host, source_port, source_db,
            source_user, source_password, ssl_mode
        )
        
        if success:
            logger.info(f"✅ SSL mode '{ssl_mode}' works!")
            logger.info(f"Recommendation: Use SSL_MODE={ssl_mode} in your .env file")
            break
    else:
        logger.error("❌ All SSL modes failed!")
        logger.error("Troubleshooting steps:")
        logger.error("1. Check RDS SSL configuration")
        logger.error("2. Verify security group rules")
        logger.error("3. Check if RDS requires specific SSL certificates")
        logger.error("4. Try connecting from AWS console to verify RDS is accessible")
        sys.exit(1)

if __name__ == "__main__":
    main() 