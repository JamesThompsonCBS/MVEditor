# MVEditor

A browser-based IDE for MultiValue (Universe) development, inspired by VS Code.

## Features

- Browser-based IDE for MVBasic development
- Real-time collaboration
- Git integration with server-side caching
- Integrated debugging tools
- Customizable environment

## Development Setup

### Prerequisites

- Python 3.13 or higher
- Universe Database access
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/MVEditor.git
cd MVEditor
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your configuration:
```env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
```

### Project Structure

```
MVEditor/
├── backend/           # FastAPI backend
│   ├── api/          # API endpoints
│   ├── core/         # Core functionality
│   ├── models/       # Database models
│   └── utils/        # Utility functions
├── frontend/         # Frontend application
│   ├── src/         # Source files
│   ├── public/      # Static files
│   └── dist/        # Build output
├── tests/           # Test suite
├── venv/            # Virtual environment
├── .env             # Environment variables
├── .gitignore       # Git ignore file
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Development

1. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend
npm install
npm run dev
```

## Testing

Run the test suite:
```bash
pytest
```

## License

[Your chosen license]

## Contributing

[Your contribution guidelines] 