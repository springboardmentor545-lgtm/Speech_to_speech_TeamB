# 🎙️ AI Speech Platform (Transcription & Translation)

This is a full-stack web application that provides a complete solution for AI-powered speech transcription and translation. It's built with a React frontend and a FastAPI backend, leveraging Azure AI services for high-accuracy processing.

The project is divided into two main functional milestones:

* **Milestone 1:** Focuses on speech-to-text. It allows users to upload audio/video files or make live recordings, which are then transcribed to text and stored in a database.
* **Milestone 2:** Adds a translation layer. It takes the transcribed text, translates it into a target language, and provides a set of analytics and quality metrics (like BLEU score and latency).

---

## ✨ Features

* **File Upload:** Transcribe audio and video files (`.mp3`, `.wav`, `.mp4`, `.webm`, etc.).
* **Live Recording:** Record audio directly in the browser and submit it for transcription (and translation in M2).
* **Database Storage:** All transcripts are saved to a SQL database (SQLite/PostgreSQL).
* **Transcript Management:** View a persistent history of all transcription jobs.
* **CSV Export:** Download all your transcript data in a single CSV file.
* **Text-to-Translation:** Instantly translate transcribed text into 12+ languages.
* **Glossary:** Apply custom terminology rules (e.g., "AI" → "IA") before translation.
* **Translation Analytics:** View real-time metrics on translation quality and performance.

---

## 🛠️ Tech Stack

This project uses a modern, high-performance stack for both the frontend and backend.

| Area            | Technology              | Purpose                                                        |
| :-------------- | :---------------------- | :------------------------------------------------------------- |
| **Frontend**    | **React 18**            | Building the user interface.                                   |
|                 | **Vite**                | Next-generation frontend tooling (dev server, build tool).     |
|                 | **Tailwind CSS**        | A utility-first CSS framework for rapid UI design.             |
|                 | `react-dropzone`        | For drag-and-drop file uploads.                                |
|                 | `lucide-react`          | A clean and simple icon library.                               |
| **Backend**     | **Python 3.10+**        | The core programming language.                                 |
|                 | **FastAPI**             | A high-performance web framework for building APIs.            |
|                 | **Uvicorn**             | The ASGI server that runs the FastAPI application.             |
|                 | **SQLAlchemy**          | The ORM (Object Relational Mapper) for database interaction.   |
|                 | **Pydantic**            | For data validation and settings management (used by FastAPI). |
|                 | `websockets`            | For the (now-removed) real-time transcription channel.         |
| **AI Services** | **Azure AI Speech**     | Powers all Speech-to-Text (STT) functionality.                 |
|                 | **Azure AI Translator** | Powers all text-to-text translation.                           |
| **Database**    | **SQLite**              | Default database for easy development.                         |
|                 | **PostgreSQL**          | Supported for production (via `DATABASE_URL`).                 |

---

## 📂 Project Structure

The repository is organized as a monorepo with two main packages:

* `/frontend`: A modern React application (built with Vite).

  * `src/pages`: Main components for `Milestone1.jsx` and `Milestone2.jsx`.
  * `src/components`: Reusable UI components (cards, tabs, buttons).
  * `src/hooks`: All complex state management and logic (e.g., `useMilestone2Logic.js`).
  * `src/utils`: Helpers for API calls (`api.js`), constants, etc.

* `/backend`: A Python-based FastAPI application.

  * `run.py`: The entry point to start the server (`python run.py`).
  * `app/`: The main application package.
  * `app/main.py`: Creates the FastAPI `app` instance.
  * `app/api/`: Contains all API route definitions (`endpoints_m1.py`, `endpoints_m2.py`).
  * `app/services/`: All business logic (e.g., `transcription_file.py`, `translation.py`).
  * `app/tasks/`: Asynchronous background tasks (like file processing).
  * `app/database.py`, `app/models.py`, `app/schemas.py`: Define the DB connection, tables, and data shapes.

---

## 🚀 Getting Started

### 1. Environment Variables

This project requires API keys from Microsoft Azure.

**In the `/backend` directory, create a file named `.env`** and add your Azure keys:

```
DATABASE_URL="sqlite:///./speech_platform.db"
AZURE_SPEECH_KEY="YOUR_AZURE_SPEECH_KEY"
AZURE_SPEECH_REGION="YOUR_AZURE_SPEECH_REGION"
AZURE_TRANSLATOR_KEY="YOUR_AZURE_TRANSLATOR_KEY"
AZURE_TRANSLATOR_REGION="YOUR_AZURE_TRANSLATOR_REGION"
AZURE_TRANSLATOR_ENDPOINT="YOUR_AZURE_TRANSLATOR_ENDPOINT"
```

### 2. Run the Backend (FastAPI)

```
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

### 3. Run the Frontend (React)

```
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser to use the application.
