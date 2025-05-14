from ..core.config import DatabaseManager, DatabaseConfig
from ..core.database import DatabaseConnectionManager
from pydantic import SecretStr
import logging
from typing import Optional, Dict, List
import uopy

logger = logging.getLogger(__name__)

def add_database_connection(
    name: str,
    host: str,
    port: int,
    account: str,
    username: str,
    password: str,
    timeout: int = 30,
    max_connections: int = 20,
    min_connections: int = 5,
    is_active: bool = True
) -> bool:
    """
    Add a new database connection configuration.
    
    Args:
        name: Unique identifier for the connection
        host: Database server hostname
        port: Database server port
        account: Universe account name
        username: Database username
        password: Database password
        timeout: Connection timeout in seconds
        max_connections: Maximum number of connections
        min_connections: Minimum number of connections
        is_active: Whether the connection is active
    
    Returns:
        bool: True if connection was added successfully
    """
    try:
        config = DatabaseConfig(
            name=name,
            host=host,
            port=port,
            account=account,
            username=username,
            password=SecretStr(password),
            timeout=timeout,
            max_connections=max_connections,
            min_connections=min_connections,
            is_active=is_active
        )
        
        manager = DatabaseManager()
        manager.add_connection(name, config)
        logger.info(f"Successfully added database connection: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to add database connection {name}: {str(e)}")
        return False

def remove_database_connection(name: str) -> bool:
    """
    Remove a database connection configuration.
    
    Args:
        name: Name of the connection to remove
    
    Returns:
        bool: True if connection was removed successfully
    """
    try:
        manager = DatabaseManager()
        manager.remove_connection(name)
        
        # Also close the connection if it's active
        db_manager = DatabaseConnectionManager()
        db_manager.close_connection(name)
        
        logger.info(f"Successfully removed database connection: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to remove database connection {name}: {str(e)}")
        return False

def list_database_connections() -> List[Dict]:
    """
    List all configured database connections.
    
    Returns:
        List of dictionaries containing connection information
    """
    try:
        manager = DatabaseManager()
        connections = []
        
        for name, config in manager._connections.items():
            conn_info = {
                "name": name,
                "host": config.host,
                "port": config.port,
                "account": config.account,
                "username": config.username,
                "timeout": config.timeout,
                "max_connections": config.max_connections,
                "min_connections": config.min_connections,
                "is_active": config.is_active
            }
            connections.append(conn_info)
        
        return connections
    except Exception as e:
        logger.error(f"Failed to list database connections: {str(e)}")
        return []

def test_database_connection(name: str) -> bool:
    """
    Test a database connection.
    
    Args:
        name: Name of the connection to test
    
    Returns:
        bool: True if connection test was successful
    """
    try:
        db_manager = DatabaseConnectionManager()
        with db_manager.connection(name) as ses:
            # Try a simple command to test the connection
            cmd = uopy.Command("LIST VOC", session=ses)
            cmd.run()
            logger.info(f"Successfully tested database connection: {name}")
            return True
    except Exception as e:
        logger.error(f"Failed to test database connection {name}: {str(e)}")
        return False

def update_database_connection(name: str, **kwargs) -> bool:
    """
    Update an existing database connection configuration.
    
    Args:
        name: Name of the connection to update
        **kwargs: Connection parameters to update
    
    Returns:
        bool: True if connection was updated successfully
    """
    try:
        manager = DatabaseManager()
        manager.update_connection(name, **kwargs)
        
        # If the connection is active, close it so it will be recreated with new settings
        db_manager = DatabaseConnectionManager()
        db_manager.close_connection(name)
        
        logger.info(f"Successfully updated database connection: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to update database connection {name}: {str(e)}")
        return False 