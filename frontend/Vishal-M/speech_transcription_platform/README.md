# Speech to Speech Team B Transcription Platform

A comprehensive speech-to-text application with Azure Cognitive Services integration.

## Requirements

- Python 3.10 (Required)
- Node.js (Latest LTS version)
- PostgreSQL (Production) / SQLite (Development)
- Azure Cognitive Services Account

## Quick Setup Commands

Here are all the commands needed to get started quickly (Windows PowerShell):

```powershell
# Clone and navigate to the project
cd E:\Speech_to_speech_TeamB\frontend\Vishal-M\speech_transcription_platform

# Backend Setup
python -m venv .venv
.\.venv\Scripts\activate
cd backend
pip install -r requirements.txt

# Start Backend Server (in terminal 1)
uvicorn app.main:app --reload --port 8000

# Frontend Setup (in terminal 2)
cd E:\Speech_to_speech_TeamB\frontend\Vishal-M\speech_transcription_platform\frontend
npm install
npm run dev

# Access the application
# Backend API: http://localhost:8000
# Frontend: http://localhost:5173
```

## Architecture

- **Backend**: FastAPI with async/await, SQLAlchemy ORM, comprehensive error handling
- **Frontend**: React 18 with Vite, TailwindCSS, modern component architecture
- **Database**: PostgreSQL with migration support (SQLite for development)
- **Infrastructure**: Docker-ready, health checks, monitoring endpoints

## Features

- Batch audio file transcription with queue management
- Real-time speech recognition with WebSocket streaming
- Multi-language auto-detection (English, Hindi)
- Persistent transcript storage with full CRUD operations
- CSV export with proper UTF-8 BOM encoding
- Comprehensive error handling and logging
- Rate limiting and security headers
- Production-ready deployment configurations

## Quick Start

### Backend Setup

1. Navigate to the project directory:
```bash
cd speech_transcription_platform
```

2. Create and activate Python virtual environment:
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\activate
# On Unix/MacOS:
source .venv/bin/activate
```

3. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy example env file
cp backend/.env.example backend/.env

# Edit the new backend/.env file with your credentials.
# NEVER commit the .env file to version control.

# Required variables:
SPEECH_KEY=your_azure_speech_key
SERVICE_REGION=your_azure_region
DATABASE_URL=sqlite:///./sql_app.db  # For development
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the backend server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: http://localhost:8000

### Frontend Setup

1. Open a new terminal and navigate to frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Create frontend environment file:
```bash
# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env
```

4. Start the development server:
```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

## Production Deployment

See `deployment/` directory for Docker, Kubernetes, and cloud deployment configurations.

## API Documentation

- OpenAPI/Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| SPEECH_KEY | Azure Speech API Key | Yes |
| SERVICE_REGION | Azure Service Region | Yes |
| DATABASE_URL | PostgreSQL connection string | Production only |
| LOG_LEVEL | Logging level (DEBUG/INFO/WARNING/ERROR) | No |
| CORS_ORIGINS | Allowed CORS origins | Production only |

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test
```

## Troubleshooting

### Common Issues

1. **Python Version Mismatch**
   ```powershell
   # Check Python version
   python --version
   # Should show Python 3.10.x
   ```

2. **Node.js Command Not Found**
   ```powershell
   # Check Node.js installation
   node --version
   npm --version
   ```

3. **Virtual Environment Issues**
   ```powershell
   # If venv creation fails, ensure Python is in PATH
   # Deactivate and recreate if needed
   deactivate
   python -m venv .venv --clear
   ```

4. **Port Already in Use**
   ```powershell
   # For backend (PowerShell)
   Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
   # For frontend
   Get-Process -Id (Get-NetTCPConnection -LocalPort 5173).OwningProcess
   ```

5. **Node Modules Issues**
   ```powershell
   # Clean install of node modules
   cd frontend
   rm -r -force node_modules
   rm package-lock.json
   npm install
   ```

## License

Proprietary - Speech to Speech Team B License
