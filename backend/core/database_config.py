from typing import Dict, Any, Optional, ClassVar
from pydantic import BaseModel, Field
from datetime import datetime
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FileConfig(BaseModel):
    """Configuration for a single MVEditor file."""
    filename: str
    description: str
    create_cmd: str
    remove_cmd: str
    purpose: str = Field(description="The purpose/type of the file (e.g., 'workspace', 'users', 'sessions')")

class ReleaseInfo(BaseModel):
    """Release information for MVEditor."""
    version: str
    release_date: str
    release_notes: str

class DatabaseAccount(BaseModel):
    """Configuration for a single database account."""
    name: str
    host: str
    port: int
    account: str
    username: str
    password: str
    timeout: int = 30
    max_connections: int = 20
    min_connections: int = 5
    is_active: bool = True

class DatabaseConfig(BaseModel):
    """Main configuration class for MVEditor database settings."""
    accounts: Dict[str, DatabaseAccount]
    files: Dict[str, FileConfig]
    release: ReleaseInfo

    FILE_PURPOSES: ClassVar[dict] = {
        'WORKSPACE': 'workspace_management',
        'FILES': 'file_management',
        'HISTORY': 'version_history',
        'PERMISSIONS': 'user_permissions',
        'SESSIONS': 'user_sessions',
        'SETTINGS': 'system_settings',
        'COLLABORATION': 'collaboration',
        'GIT': 'version_control',
        'AUDIT': 'audit_logs',
        'LOGS': 'system_logs',
        'CACHE': 'system_cache',
        'TESTS': 'test_data',
        'DOCS': 'documentation'
    }

    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> 'DatabaseConfig':
        """Load configuration from JSON file."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "database_config.json")
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                
                # Map file purposes
                for key, file_info in data.get("files", {}).items():
                    if key in cls.FILE_PURPOSES:
                        file_info["purpose"] = cls.FILE_PURPOSES[key]
                
                return cls(**data)
        except Exception as e:
            logger.error("Failed to load database configuration: %s", str(e))
            raise

    def get_file_by_purpose(self, purpose: str) -> Optional[FileConfig]:
        """Get file configuration by its purpose."""
        for file_config in self.files.values():
            if file_config.purpose == purpose:
                return file_config
        return None

    def get_active_accounts(self) -> Dict[str, DatabaseAccount]:
        """Get all active database accounts."""
        return {name: acc for name, acc in self.accounts.items() if acc.is_active}

    def get_file_config(self, filename: str) -> Optional[FileConfig]:
        """Get file configuration by filename."""
        for file_config in self.files.values():
            if file_config.filename == filename:
                return file_config
        return None

    def get_release_x_record(self) -> list:
        """Get the X record format for release information."""
        return [
            "X",  # Record type
            self.release.version,
            self.release.release_date,
            self.release.release_notes,
            datetime.utcnow().strftime("%Y-%m-%d")  # current date
        ]

# Create a global instance of the configuration
db_config: Optional[DatabaseConfig] = None

def initialize_config(config_path: Optional[str] = None) -> DatabaseConfig:
    """Initialize the global database configuration."""
    global db_config
    if db_config is None:
        db_config = DatabaseConfig.load_from_file(config_path)
    return db_config

def get_config() -> DatabaseConfig:
    """Get the global database configuration."""
    if db_config is None:
        raise RuntimeError("Database configuration not initialized. Call initialize_config() first.")
    return db_config 