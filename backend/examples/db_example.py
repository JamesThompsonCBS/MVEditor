from ..utils.db_utils import (
    add_database_connection,
    remove_database_connection,
    list_database_connections,
    test_database_connection,
    update_database_connection
)
from ..core.database import DatabaseConnectionManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_usage():
    """Example usage of the database connection system."""
    
    # Add a new database connection
    success = add_database_connection(
        name="development",
        host="172.16.8.13",
        port=31438,  # Default Universe port
        account="DEVELOPMENT",
        username="jthompson",
        password="Alarmswitch843",
        timeout=30
    )
    
    if success:
        logger.info("Added development database connection")
        
        # Test the connection
        if test_database_connection("development"):
            logger.info("Successfully tested development connection")
            
            # List all connections
            connections = list_database_connections()
            logger.info(f"Current connections: {connections}")
            
            # Use the connection
            db_manager = DatabaseConnectionManager()
            with db_manager.connection("development") as conn:
                # Example: List VOC
                result = conn.execute("LIST VOC")
                logger.info("VOC listing successful")
                
                # Example: Read a record
                try:
                    record = conn.read("CUSTOMERS", "1001")
                    logger.info(f"Read record: {record}")
                except Exception as e:
                    logger.error(f"Error reading record: {str(e)}")
            
            # Update connection settings
            update_database_connection(
                "development",
                timeout=45,
                max_connections=30
            )
            
            # Remove the connection
            if remove_database_connection("development"):
                logger.info("Successfully removed development connection")
        else:
            logger.error("Failed to test development connection")
    else:
        logger.error("Failed to add development connection")

if __name__ == "__main__":
    example_usage() 