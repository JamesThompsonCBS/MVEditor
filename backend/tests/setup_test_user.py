import uopy
import logging
from ..core.config import DatabaseManager, DatabaseConfig
from ..core.database import DatabaseConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_user():
    """Set up a test user in the Universe database."""
    try:
        # Get database connection
        db_manager = DatabaseConnectionManager()
        with db_manager.connection("default") as conn:
            # Create test user
            username = "test_user"
            password = "test_password"
            
            # Check if user exists
            cmd = uopy.Command(f"LIST USER {username}")
            cmd.run()
            
            if not cmd.response:
                # Create user
                create_cmd = uopy.Command(f"CREATE.USER {username} {password}")
                create_cmd.run()
                logger.info(f"Created test user: {username}")
            else:
                # Update password
                update_cmd = uopy.Command(f"CHANGE.PASSWORD {username} {password}")
                update_cmd.run()
                logger.info(f"Updated test user password: {username}")
            
            # Create necessary files if they don't exist
            files_to_create = [
                "MVEDITOR.SESSIONS",
                "MVEDITOR.USERS"
            ]
            
            for file_name in files_to_create:
                cmd = uopy.Command(f"LIST {file_name}")
                cmd.run()
                if not cmd.response:
                    create_cmd = uopy.Command(f"CREATE.FILE {file_name}")
                    create_cmd.run()
                    logger.info(f"Created file: {file_name}")
            
            logger.info("Test user setup completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Failed to set up test user: {str(e)}")
        return False

if __name__ == "__main__":
    setup_test_user() 