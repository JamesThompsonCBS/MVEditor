from typing import Optional, Dict
import uopy
from .config import DatabaseManager, DatabaseConfig
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Manages active database connections using UOPY."""
    _instance = None
    _connections: Dict[str, uopy.Session] = {}
    _config_manager = DatabaseManager()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
        return cls._instance

    def _create_connection(self, config: DatabaseConfig) -> uopy.Session:
        """Create a new Universe database session using uopy.connect."""
        try:
            logger.info(f"Attempting to connect to {config.host} with account '{config.account}'")
            session = uopy.connect(
                host=config.host,
                user=config.username,
                password=config.password.get_secret_value(),
                account=config.account
            )
            logger.info(f"Successfully created session to {config.host} with account '{config.account}'")
            return session
        except Exception as e:
            logger.error(f"Failed to create database session to {config.host} with account '{config.account}': {str(e)}")
            raise

    def get_connection(self, name: str) -> Optional[uopy.Session]:
        """Get an active database session by name."""
        if name not in self._connections:
            config = self._config_manager.get_connection(name)
            if config and config.is_active:
                try:
                    self._connections[name] = self._create_connection(config)
                except Exception as e:
                    logger.error(f"Failed to establish session to {name}: {str(e)}")
                    return None
            else:
                logger.warning(f"No active configuration found for database: {name}")
                return None
        return self._connections.get(name)

    def close_connection(self, name: str) -> None:
        """Close a database session."""
        if name in self._connections:
            try:
                self._connections[name].close()
                del self._connections[name]
            except Exception as e:
                logger.error(f"Error closing session {name}: {str(e)}")

    def close_all_connections(self) -> None:
        """Close all active database sessions."""
        for name in list(self._connections.keys()):
            self.close_connection(name)

    @contextmanager
    def connection(self, name: str):
        """Context manager for database sessions."""
        conn = None
        try:
            conn = self.get_connection(name)
            if conn is None:
                raise ConnectionError(f"Could not establish session to {name}")
            yield conn
        except Exception as e:
            logger.error(f"Error in database session {name}: {str(e)}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                    if name in self._connections:
                        del self._connections[name]
                except Exception as e:
                    logger.error(f"Error closing session {name}: {str(e)}")

    def __del__(self):
        """Cleanup when the manager is destroyed."""
        self.close_all_connections()

# Create a global instance of the connection manager
db_manager = DatabaseConnectionManager()

@contextmanager
def get_database_connection(name: str = "default"):
    """Get a database connection using the connection manager.
    
    Args:
        name: Name of the database connection to use (defaults to "default")
    
    Yields:
        uopy.Session: The database session
        
    Raises:
        ConnectionError: If the connection cannot be established
    """
    with db_manager.connection(name) as session:
        yield session

# Example usage:
"""
# Initialize the connection manager
db_manager = DatabaseConnectionManager()

# Using a connection
with db_manager.connection("development") as ses:
    # Use the session
    cmd = uopy.Command("LIST VOC")
    cmd.run()
    print(cmd.response)
    
# Or get a persistent session
ses = db_manager.get_connection("development")
try:
    cmd = uopy.Command("LIST VOC")
    cmd.run()
    print(cmd.response)
finally:
    db_manager.close_connection("development")
""" 