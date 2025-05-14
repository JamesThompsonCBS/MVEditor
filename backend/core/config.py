from typing import Dict, Optional, List
from pydantic_settings import BaseSettings
from pydantic import SecretStr
import json
from pathlib import Path
import logging
import secrets

logger = logging.getLogger(__name__)

class DatabaseConfig(BaseSettings):
    """Database connection configuration for a single server."""
    name: str
    host: str
    port: int
    account: str
    username: str
    password: SecretStr
    timeout: int = 30
    max_connections: int = 20
    min_connections: int = 5
    is_active: bool = True

    class Config:
        env_prefix = "DB_"

class Settings(BaseSettings):
    # Database settings
    DB_HOST: str = "localhost"
    DB_USER: str = "username"
    DB_PASSWORD: str = "password"
    DB_ACCOUNT: str = "XDEMO"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]  # Frontend URL
    
    # JWT settings
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate a secure key
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = True

class DatabaseManager:
    """Manages multiple database connections."""
    _instance = None
    _connections: Dict[str, DatabaseConfig] = {}
    _config_file: Path = Path(__file__).parent / "database_config.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load database configurations from the config file."""
        logger.info(f"Loading database configuration from: {self._config_file}")
        if self._config_file.exists():
            with open(self._config_file, 'r') as f:
                configs = json.load(f)
                for name, config in configs.items():
                    self._connections[name] = DatabaseConfig(**config)
                logger.info(f"Loaded {len(self._connections)} database configurations")
        else:
            logger.error(f"Database configuration file not found: {self._config_file}")

    def _save_config(self) -> None:
        """Save database configurations to the config file."""
        configs = {
            name: {
                **config.model_dump(exclude={'password'}),
                'password': config.password.get_secret_value()
            }
            for name, config in self._connections.items()
        }
        
        # Ensure the directory exists
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self._config_file, 'w') as f:
            json.dump(configs, f, indent=4)

    def add_connection(self, name: str, config: DatabaseConfig) -> None:
        """Add a new database connection configuration."""
        self._connections[name] = config
        self._save_config()

    def remove_connection(self, name: str) -> None:
        """Remove a database connection configuration."""
        if name in self._connections:
            del self._connections[name]
            self._save_config()

    def get_connection(self, name: str) -> Optional[DatabaseConfig]:
        """Get a database connection configuration by name."""
        return self._connections.get(name)

    def get_active_connections(self) -> Dict[str, DatabaseConfig]:
        """Get all active database connections."""
        return {name: config for name, config in self._connections.items() 
                if config.is_active}

    def update_connection(self, name: str, **kwargs) -> None:
        """Update an existing database connection configuration."""
        if name in self._connections:
            current_config = self._connections[name]
            updated_config = current_config.model_copy(update=kwargs)
            self._connections[name] = updated_config
            self._save_config()

# Create a .gitignore entry for the config file
def ensure_config_ignored():
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        if "database_config.json" not in content:
            with open(gitignore_path, 'a') as f:
                f.write("\n# Database configuration\nbackend/core/database_config.json\n")

ensure_config_ignored() 