from typing import Dict, Optional, List
from pydantic_settings import BaseSettings
from pydantic import SecretStr, validator
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

    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

    @validator('host')
    def validate_host(cls, v):
        if not v:
            raise ValueError('Host cannot be empty')
        return v

    class Config:
        env_prefix = "DB_"

class Settings(BaseSettings):
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend URL
        "http://localhost:8000",  # Backend URL
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    # JWT settings
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
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
            try:
                with open(self._config_file, 'r') as f:
                    configs = json.load(f)
                    for name, config in configs.items():
                        self._connections[name] = DatabaseConfig(**config)
                logger.info(f"Loaded {len(self._connections)} database configurations")
            except Exception as e:
                logger.error(f"Error loading database configuration: {str(e)}")
                self._connections = {}
        else:
            logger.warning(f"Database configuration file not found: {self._config_file}")
            self._connections = {}

    def _save_config(self) -> None:
        """Save database configurations to the config file."""
        try:
            configs = {
                name: {
                    **config.model_dump(exclude={'password'}),
                    'password': '********'  # Don't save actual passwords
                }
                for name, config in self._connections.items()
            }
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, 'w') as f:
                json.dump(configs, f, indent=4)
            logger.info(f"Saved {len(configs)} database configurations")
        except Exception as e:
            logger.error(f"Error saving database configuration: {str(e)}")
            raise

    def add_connection(self, name: str, config: DatabaseConfig) -> None:
        self._connections[name] = config
        self._save_config()

    def remove_connection(self, name: str) -> None:
        if name in self._connections:
            del self._connections[name]
            self._save_config()

    def get_connection(self, name: str) -> Optional[DatabaseConfig]:
        return self._connections.get(name)

    def get_active_connections(self) -> Dict[str, DatabaseConfig]:
        return {name: config for name, config in self._connections.items() if config.is_active}

    def update_connection(self, name: str, **kwargs) -> None:
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