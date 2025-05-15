# Planning Document for Browser-Based IDE

## Project Overview

This project aims to develop a user-friendly, browser-based Integrated Development Environment (IDE) inspired by the features and functionality of [https://vscode.dev/](https://vscode.dev/). The IDE will support MVBasic, provide collaboration tools, and facilitate an efficient coding experience for developers of all skill levels.

## Objectives

1. **User-Friendly Interface**: Design a clean and intuitive user interface that resembles traditional IDEs, enabling users to navigate and utilize features with ease.
2. **Real-Time Collaboration**: Implement features that allow multiple users to work on the same project simultaneously, similar to tools like Google Docs.
3. **Integrated Version Control**: Utilize Git functionality for seamless version control, allowing users to manage changes and collaborate effectively and efficiently. The GIT folder should be cached on the server, storing a shadow copy of the updated record. Synchronization between the Universe Database and the Git shadow copy will be managed using pre-commit and post-commit hooks to ensure changes are logged and updated consistently. In the event of a conflict, users will be prompted with a merge interface to resolve discrepancies before committing manually. Use the pattern of server root `./gitcache/{DatabaseAccount}/{FILENAME}/{RECORD.ID}`.
4. **Customizable Environment**: Allow users to personalize their coding environment (themes, font sizes, key bindings, etc.).
5. **Code Storage**: Enable users to save their projects on the Universe Database, with versioning managed through record history tables and concurrency control enforced by locking mechanisms during edit sessions, ensuring easy access from any device. Utilize Uopy to access folders and source code.
6. **Testing and Debugging Tools**: These debugging features will operate by interfacing with the server where MVBasic code is executed. The execution flow will be monitored server-side, with breakpoint triggers communicating back to the client in real-time via WebSockets. Users will inspect variables and control flow through a synchronized console using xterm.js. This setup provides a seamless server-connected debugging interface.

## Features List

1. **Code Editor**:

   - Syntax highlighting
   - Code completion
   - Error highlighting
   - Code snippets and templates
   - Multi-file project management
   - Support for editing multiple files/records using tabs in the header
2. **Collaboration**:

   - Live coding sessions with multiple users
   - Chat functionality for communication
   - Change tracking and visibility of user cursors
   - Session awareness: Notify users when others are editing the same file and display real-time cursor positions.
   - Conflict resolution: Present merge tools when concurrent changes are detected.
3. **Customizable Settings**:

   - Theme selection (light/dark mode)
   - Font settings
   - Key binding customization
4. **File Management**:

   - Utilize Uopy to access files and directories. The Universe file workspace will hold workgroups with a table of database `FILENAME` and `RECORD.ID`. The `FILENAME` will represent a directory, and the `RECORD.ID` will represent a file.
   - Project file upload/download
   - Directory creation and file organization
   - Metadata tracking: Display file creation/modification timestamps and last modified user for each file in the sidebar or header pane.
5. **Testing/Debugging**:

   - Console output for logging
   - Breakpoints and step-through execution
6. **Hosting and Deployment**:

   - Options for hosting web projects directly from the IDE
   - Integration with platforms like AWS Fargate or DigitalOcean App Platform (more suitable for long-running Docker containers)

## Technical Stack

- **Communication Layer**: WebSockets (used for real-time collaboration and debugging communication) and Uopy for database access
- **Frontend**: Vanilla JavaScript (Monaco Editor for enhanced editor features and maintainability)
- **Backend**: Python with FastAPI
- **Database**: Universe Database
- **Authentication**: Database authentication
- **Code Execution**: Docker containers or serverless functions for running code

## Development Timeline

1. **Phase 1: Setup**

   - Set up a virtual Python environment and create a `requirements.txt` file.
2. **Phase 2: Development**

   - Set up the frontend and backend environments.
   - Implement core features (code editor, file management).
   - Develop collaboration tools and version control.
3. **Phase 3: Testing**

   - Implement an automated testing suite for core functionalities (editor, Git sync, collaboration)
   - Run cross-browser compatibility checks
   - Conduct user testing and gather feedback
   - Fix bugs and optimize performance
4. **Phase 4: Launch**

   - Deploy the application using Docker.

## Database Structure

### File Management System
The database files are managed through a centralized configuration system that defines their structure, purpose, and creation parameters. Each file is defined in the configuration with:
- Standardized purpose mapping
- Creation and removal commands
- File attributes and metadata
- Version tracking
- Access control settings

Files are automatically created during account initialization using the configuration settings. The system supports:
- Dynamic file creation based on configuration
- Standardized file purposes
- Automatic X record management for release information
- File validation and error handling
- Version tracking through X records

### Core Files Structure
The following files are managed through the configuration system and created during account initialization:

FILENAME: MVEDITOR.WORKSPACE
Purpose: Workspace Management
Attributes:
- ID: Workspace ID
- NAME: Workspace Name
- OWNER: User ID
- CREATED: Timestamp
- MODIFIED: Timestamp
- STATUS: Active/Archived
- MEMBERS: Multi-value list of user IDs
- SETTINGS: Multi-value list of workspace settings
- SHARD: Shard ID (for horizontal scaling)

FILENAME: MVEDITOR.FILES
- ID: File ID
- WORKSPACE: Workspace ID
- FILENAME: Universe File Name
- RECORD.ID: Record ID
- CONTENT: File Content
- VERSION: Version Number
- LOCKED.BY: User ID
- LOCKED.AT: Timestamp
- HISTORY: Multi-value list of version history
- ENCRYPTED: Boolean flag for sensitive content
- INDEX: Multi-value list of searchable content

FILENAME: MVEDITOR.HISTORY
- ID: History ID
- FILE: File ID
- VERSION: Version Number
- CONTENT: File Content
- USER: User ID
- TIMESTAMP: Timestamp
- COMMENT: Change Comment
- HASH: Content hash for verification
- PARENT: Parent version ID

FILENAME: MVEDITOR.PERMISSIONS
- ID: Permission ID
- USER: User ID
- WORKSPACE: Workspace ID
- ACCESS: Read/Write/Admin
- FILES: Multi-value list of file permissions
- EXPIRES: Permission expiration timestamp
- GRANTED_BY: User who granted permission

FILENAME: MVEDITOR.SESSIONS
- ID: Session ID
- USER: User ID
- TOKEN: JWT Token
- CREATED: Timestamp
- EXPIRES: Timestamp
- IP_ADDRESS: Client IP
- USER_AGENT: Browser Info
- STATUS: Active/Expired/Revoked
- LAST_ACTIVITY: Timestamp

FILENAME: MVEDITOR.SETTINGS
- ID: Settings ID
- USER: User ID
- THEME: User theme preference
- KEYBINDINGS: Custom keybindings
- EDITOR_SETTINGS: Editor preferences
- NOTIFICATIONS: Notification settings
- LANGUAGE: UI language preference

FILENAME: MVEDITOR.COLLABORATION
- ID: Collaboration ID
- FILE: File ID
- USERS: Multi-value list of active users
- CURSORS: Multi-value list of cursor positions
- CHAT: Multi-value list of chat messages
- STATUS: Active/Inactive
- CREATED: Timestamp
- LAST_ACTIVITY: Timestamp

FILENAME: MVEDITOR.GIT
- ID: Git Operation ID
- FILE: File ID
- OPERATION: Commit/Push/Pull
- USER: User ID
- TIMESTAMP: Timestamp
- STATUS: Success/Failed
- MESSAGE: Git operation message
- BRANCH: Git branch name
- CONFLICTS: Multi-value list of conflicts

FILENAME: MVEDITOR.AUDIT
- ID: Audit ID
- TIMESTAMP: Timestamp
- USER: User ID
- ACTION: Action performed
- RESOURCE: Affected resource
- DETAILS: Action details
- IP_ADDRESS: Client IP
- STATUS: Success/Failed

FILENAME: MVEDITOR.LOGS
- ID: Log ID
- TIMESTAMP: Timestamp
- LEVEL: Error/Warning/Info
- USER: User ID
- ACTION: Action performed
- DETAILS: Error details
- STACK_TRACE: Stack trace if applicable
- SEVERITY: Critical/High/Medium/Low
- RESOLVED: Boolean flag

FILENAME: MVEDITOR.CACHE
- ID: Cache ID
- RESOURCE: Resource identifier
- CONTENT: Cached content
- CREATED: Timestamp
- EXPIRES: Timestamp
- HITS: Access count
- SIZE: Content size
- TYPE: Cache type

FILENAME: MVEDITOR.TESTS
- ID: Test ID
- FILE: File ID
- NAME: Test name
- TYPE: Unit/Integration/E2E
- STATUS: Pass/Fail/Skipped
- RESULT: Test result
- DURATION: Execution time
- COVERAGE: Coverage percentage

FILENAME: MVEDITOR.DOCS
- ID: Doc ID
- TITLE: Documentation title
- CONTENT: Documentation content
- CATEGORY: Doc category
- VERSION: Doc version
- AUTHOR: User ID
- CREATED: Timestamp
- MODIFIED: Timestamp
- TAGS: Multi-value list of tags

### File Creation Process
1. Configuration Loading:
   - Load file definitions from `database_config.json`
   - Validate file configurations
   - Map file purposes to standardized types
   - Prepare creation commands

2. Account Initialization:
   - Create files based on configuration
   - Apply standardized attributes
   - Set up X records for version tracking
   - Validate file creation
   - Handle errors and rollback if needed

3. File Management:
   - Track file status and versions
   - Manage file access and permissions
   - Handle file modifications
   - Maintain audit logs
   - Support file removal when needed

### File Purpose Standardization
Each file has a standardized purpose defined in the configuration:
- WORKSPACE: Workspace management and organization
- FILES: File system and content management
- HISTORY: Version history and change tracking
- PERMISSIONS: Access control and user rights
- SESSIONS: User session management
- SETTINGS: System and user preferences
- COLLABORATION: Real-time collaboration features
- GIT: Version control integration
- AUDIT: System audit logging
- LOGS: Application logging
- CACHE: Performance optimization
- TESTS: Testing and validation
- DOCS: Documentation management

## System Configuration

### Connection Management
MAX_CONNECTIONS = 20
MIN_CONNECTIONS = 5
CONNECTION_TIMEOUT = 30
IDLE_TIMEOUT = 300
RETRY_ATTEMPTS = 3
CONNECTION_POOL_MONITOR_INTERVAL = 60

### Session Management
SESSION_TIMEOUT = 3600  # 1 hour
MAX_SESSIONS_PER_USER = 3
SESSION_CLEANUP_INTERVAL = 300  # 5 minutes
JWT_EXPIRATION = 3600  # 1 hour
JWT_REFRESH_THRESHOLD = 300  # 5 minutes

### Security Settings
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = 900  # 15 minutes
PASSWORD_EXPIRY_DAYS = 90
ENCRYPTION_ALGORITHM = "AES-256-GCM"

### Cache Configuration
CACHE_MAX_SIZE = 1000  # records
CACHE_TTL = 3600  # 1 hour
CACHE_CLEANUP_INTERVAL = 300  # 5 minutes
CACHE_MEMORY_LIMIT = 512  # MB

### Git Integration
GIT_CACHE_PATH = "./gitcache/{DatabaseAccount}/{FILENAME}/{RECORD.ID}"
GIT_SYNC_INTERVAL = 300  # 5 minutes
GIT_MAX_RETRIES = 3
GIT_CONFLICT_RESOLUTION_TIMEOUT = 300  # 5 minutes

### Error Codes
ERR_CONNECTION_FAILED = "UOPY001"
ERR_LOCK_FAILED = "UOPY002"
ERR_RECORD_NOT_FOUND = "UOPY003"
ERR_PERMISSION_DENIED = "UOPY004"
ERR_CONCURRENT_MODIFICATION = "UOPY005"
ERR_RATE_LIMIT_EXCEEDED = "UOPY006"
ERR_SESSION_EXPIRED = "UOPY007"
ERR_INVALID_TOKEN = "UOPY008"
ERR_GIT_CONFLICT = "UOPY009"
ERR_CACHE_OVERFLOW = "UOPY010"

### Event Types
EVENT_TYPES = {
    'CURSOR_MOVE': 'cursor.move',
    'TEXT_CHANGE': 'text.change',
    'FILE_SAVE': 'file.save',
    'LOCK_ACQUIRE': 'lock.acquire',
    'LOCK_RELEASE': 'lock.release',
    'USER_JOIN': 'user.join',
    'USER_LEAVE': 'user.leave',
    'COLLABORATION_START': 'collab.start',
    'COLLABORATION_END': 'collab.end',
    'GIT_SYNC': 'git.sync',
    'SESSION_EXPIRE': 'session.expire',
    'ERROR_OCCURRED': 'error.occurred'
}

### Monitoring and Maintenance
HEALTH_CHECK_INTERVAL = 60  # seconds
BACKUP_INTERVAL = 86400  # 24 hours
BACKUP_RETENTION_DAYS = 30
MAINTENANCE_WINDOW_START = "02:00"  # UTC
MAINTENANCE_WINDOW_DURATION = 120  # minutes
PERFORMANCE_METRICS_INTERVAL = 300  # 5 minutes

## [UPDATE] Database Configuration System
- Implemented a new configuration management system using Pydantic models
- Created a centralized configuration class (`DatabaseConfig`) to manage all database settings
- Standardized file purposes through a mapping system
- Added proper type validation and error handling
- Implemented X record management for release information
- Configuration is now loaded at application startup and managed globally

### Configuration Structure
1. File Configuration (`FileConfig`):
   - Manages individual file settings
   - Includes filename, description, create/remove commands
   - Maps to standardized purposes (workspace, files, history, etc.)

2. Account Configuration (`DatabaseAccount`):
   - Manages database connection settings
   - Includes connection pooling parameters
   - Handles active/inactive status

3. Release Information (`ReleaseInfo`):
   - Manages version information
   - Stores release dates and notes
   - Used for X record creation in VOC

### Configuration Loading
- Configuration is loaded from `database_config.json`
- File purposes are automatically mapped during loading
- Global configuration instance is maintained
- Proper error handling and logging implemented

## Implementation Guidelines

### Security Implementation
1. Authentication:
   - Implement JWT-based authentication
   - Use secure password hashing (bcrypt)
   - Implement rate limiting
   - Enable IP-based session tracking
   - Implement audit logging

2. Data Protection:
   - Encrypt sensitive data at rest
   - Use TLS for all communications
   - Implement proper access controls
   - Regular security audits
   - Automated vulnerability scanning

### Performance Optimization
1. Caching Strategy:
   - Implement LRU cache for frequently accessed records
   - Cache workspace metadata
   - Cache file listings
   - Implement cache invalidation
   - Monitor cache hit rates

2. Connection Pooling:
   - Implement connection reuse
   - Monitor pool health
   - Implement connection timeouts
   - Handle connection failures
   - Implement retry logic

### Backup and Recovery
1. Backup Procedures:
   - Daily automated backups
   - Point-in-time recovery
   - Backup verification
   - Offsite backup storage
   - Backup retention management

2. Recovery Procedures:
   - Automated recovery testing
   - Disaster recovery planning
   - Data integrity verification
   - Recovery time objectives
   - Recovery point objectives

### Monitoring and Maintenance
1. System Health:
   - Real-time monitoring
   - Performance metrics
   - Resource utilization
   - Error tracking
   - Alert management

2. Maintenance:
   - Scheduled maintenance windows
   - Automated cleanup
   - Performance optimization
   - Security updates
   - Database maintenance

## Conclusion

This enhanced planning document provides a comprehensive framework for developing a robust, secure, and scalable browser-based IDE. The additional features and configurations will ensure the system's reliability, performance, and maintainability while providing a superior user experience.
