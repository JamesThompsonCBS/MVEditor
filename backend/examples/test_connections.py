from backend.utils.db_utils import (
    list_database_connections,
    test_database_connection
)
from backend.core.database import DatabaseConnectionManager
import logging
import sys
from typing import Dict, List
import uopy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_all_connections() -> Dict[str, bool]:
    """
    Test all configured database connections.
    
    Returns:
        Dict[str, bool]: Dictionary of connection names and their test results
    """
    results = {}
    
    # Get list of all configured connections
    connections = list_database_connections()
    logger.info(f"Found {len(connections)} configured connections")
    
    # Test each connection
    for conn_info in connections:
        name = conn_info["name"]
        logger.info(f"\nTesting connection: {name}")
        logger.info(f"Host: {conn_info['host']}")
        logger.info(f"Account: {conn_info['account']}")
        
        try:
            # Test the connection
            if test_database_connection(name):
                logger.info(f"✅ Connection {name} successful")
                results[name] = True
                
                # Try to execute a simple command
                db_manager = DatabaseConnectionManager()
                with db_manager.connection(name) as ses:
                    try:
                        # Try to list VOC
                        cmd = uopy.Command("LIST VOC", session=ses)
                        cmd.run()
                        logger.info(f"✅ Successfully executed LIST VOC on {name}")
                        
                        # Try to get account info (using a generic command, as ACCOUNT may not be valid)
                        # If you have a specific command for account info, replace below
                        # Example: cmd = uopy.Command("WHO", session=ses)
                        # cmd.run()
                        # logger.info(f"✅ Successfully got account info: {cmd.response}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error executing commands on {name}: {str(e)}")
                        results[name] = False
            else:
                logger.error(f"❌ Connection {name} failed")
                results[name] = False
                
        except Exception as e:
            logger.error(f"❌ Error testing connection {name}: {str(e)}")
            results[name] = False
    
    return results

def print_summary(results: Dict[str, bool]) -> None:
    """Print a summary of the test results."""
    logger.info("\n=== Connection Test Summary ===")
    total = len(results)
    successful = sum(1 for result in results.values() if result)
    
    logger.info(f"Total connections: {total}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {total - successful}")
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"{status} {name}")

if __name__ == "__main__":
    logger.info("Starting database connection tests...")
    results = test_all_connections()
    print_summary(results)
    
    # Exit with status code 1 if any connection failed
    if not all(results.values()):
        sys.exit(1) 