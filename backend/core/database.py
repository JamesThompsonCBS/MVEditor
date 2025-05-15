from typing import Optional, Dict, Any
import uopy
import logging
import json
from contextlib import contextmanager
import os
from datetime import datetime
from .database_config import DatabaseConfig, initialize_config, get_config, FileConfig

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Manages active database connections using UOPY."""
    _instance = None
    _connections: Dict[str, uopy.Session] = {}
    _config: Optional[DatabaseConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
            cls._instance._config = initialize_config()
        return cls._instance

    def _create_connection(self, account_name: str) -> uopy.Session:
        """Create a new Universe database session using uopy.connect."""
        try:
            account = self._config.accounts[account_name]
            logger.info(f"Attempting to connect to {account.host} with account '{account.account}'")
            session = uopy.connect(
                host=account.host,
                user=account.username,
                password=account.password,
                account=account.account
            )
            logger.info(f"Successfully created session to {account.host} with account '{account.account}'")
            return session
        except Exception as e:
            logger.error(f"Failed to create database session to {account_name}: {str(e)}")
            raise

    def get_connection(self, name: str) -> Optional[uopy.Session]:
        """Get an active database session by name."""
        if name not in self._connections:
            account = self._config.accounts.get(name)
            if account and account.is_active:
                try:
                    self._connections[name] = self._create_connection(name)
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

def create_universe_file(file_config: FileConfig, session: uopy.Session) -> None:
    """Create a Universe file if it doesn't exist."""
    try:
        # Try to open the file to check if it exists
        file = uopy.File(file_config.filename, session)
        logger.info(f"File {file_config.filename} already exists")
        return
    except uopy.UOError:
        # File doesn't exist, create it
        try:
            cmd = uopy.Command(file_config.create_cmd)
            cmd.run()
            logger.info(f"Created file {file_config.filename} using command: {file_config.create_cmd}")
            output = cmd.response if cmd.response else "No output"
            logger.info(f"Command output: {output}")
        except Exception as e:
            logger.error(f"Failed to create file {file_config.filename}: {str(e)}")
            raise

def initialize_account(connection_name: str = "default"):
    """Initialize the Universe account by creating all required MVEditor files."""
    try:
        config = get_config()
        
        with DatabaseConnectionManager().connection(connection_name) as session:
            # Create required files
            for file_config in config.files.values():
                try:
                    create_universe_file(file_config, session)
                except Exception as e:
                    msg = f"Error initializing file '{file_config.filename}': {str(e)}"
                    logger.error(msg)
                    raise

            # Create release information X record in VOC
            try:
                x_record = config.get_release_x_record()
                
                # Write the X record to VOC
                cmd = uopy.Command("WRITE VOC MVEDITOR.RELEASE X")
                cmd.run()
                
                # Write each line of the X record
                for i, value in enumerate(x_record, 1):
                    cmd = uopy.Command(f"WRITE VOC MVEDITOR.RELEASE {i} {value}")
                    cmd.run()
                
                logger.info("Created release information X record MVEDITOR.RELEASE in VOC")
            except Exception as e:
                logger.error(f"Error creating release information X record: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"Error initializing account: {str(e)}")
        raise

# Create a global instance of the connection manager
db_manager = DatabaseConnectionManager()

@contextmanager
def get_database_connection(name: str = "default"):
    """Get a database connection using the connection manager."""
    with db_manager.connection(name) as session:
        yield session

# (Assume database_management.json is located in the same directory as database.py.)
DB_MANAGEMENT_PATH = os.path.join(os.path.dirname(__file__), "database_management.json")

def load_db_management():
    """Load (or "gather") the [files] node (and [releaseInfo]) from database_management.json (or raise an error if the file is not found or invalid)."""
    try:
         with open(DB_MANAGEMENT_PATH, "r") as f:
             data = json.load(f)
             if "files" not in data:
                 raise KeyError("[files] node not found in database_management.json.")
             return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f'Failed to load (or "gather") database_management.json: {str(e)}')
        raise

def create_universe_file(file_name: str, session, create_cmd: str = None):
    """
    Create a UniVerse file (using CREATE.FILE or ICREATE.FILE) if it does not exist.
    (If create_cmd is supplied, it is used (for example, "CREATE.FILE ..") (otherwise, a default (or "gathered" from database_management.json) is used).)
    (Instead of using LIST VOC, we try to open (using uopy.File) the file (for example, "F = uopy.File(file_name, session=session)").)
    (If the open fails (for example, if the file does not exist or the account is not initialized), a warning is logged.)
    (Echo (log) the command output (or "No output") as before.)
    Args:
        file_name (str): The name of the file to create (or "gathered" from "files"[key]["filename"]).
        session (uopy.Session): The active UOPY session.
        create_cmd (str, optional): The command (for example, "CREATE.FILE ..") (or "gathered" from "files"[key]["create_cmd"]).
    """
    try:
         F = uopy.File(file_name, session=session)
         logger.info(f'UniVerse file "{file_name}" already exists (opened).')
         return
    except Exception as e:
         logger.warning(f'Open (uopy.File) for {file_name} failed (account may not be initialized): {str(e)}')
         pass
    try:
         if create_cmd is None:
             create_cmd = f'CREATE.FILE {file_name} 18,11,4 18,11,4 "MVEditor Support file"'
         create_cmd_obj = uopy.Command(create_cmd)
         create_cmd_obj.run()
         logger.info(f'Created UniVerse file "{file_name}" (using CREATE.FILE).')
         if create_cmd_obj.response:
             logger.info(f'Command output for {file_name}:\n{create_cmd_obj.response}')
         else:
             logger.info(f'No output for {file_name}.')
    except Exception as e:
         logger.error(f'Failed to create UniVerse file "{file_name}": {str(e)}')
         raise

def initialize_account(connection_name: str = "default"):
    """
    Initialize the Universe account by creating all required MVEditor files (using CREATE.FILE) if they do not exist.
    (Instead of hardcoding the required filenames (and create_cmd), we "gather" (or "load") the "files" node (and "releaseInfo") from database_management.json (or raise an error if the file is not found or invalid).)
    (Loop over "files" (or "files.keys()") and call create_universe_file (or a helper) with "filename" and "create_cmd" (or "remove_cmd") "gathered" from "files"[key].)
    (Echo (log) the command output (or "No output") as before.)
    (If the account is not initialized (or VOC file is not present), a warning is logged.)
    (Instead of using LIST VOC, we try to open (using uopy.File) each file.)
    Args:
        connection_name (str): The database connection name to use.
    """
    try:
        db_management = load_db_management()
        required_files = db_management["files"]
    except Exception as e:
        logger.error(f'Error loading database_management.json: {str(e)}')
        raise KeyError('"files" node not found in database_management.json')
    with db_manager.connection(connection_name) as session:
        for (key, file_info) in required_files.items():
            try:
                create_universe_file(file_info["filename"], session, create_cmd=file_info.get("create_cmd"))
            except Exception as e:
                logger.error(f'Error initializing file "{file_info["filename"]}": {str(e)}')

# Example usage:

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
