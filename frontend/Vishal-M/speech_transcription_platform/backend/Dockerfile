FROM python:3.11-slim

WORKDIR /app

# Install system dependencies: build tools, postgres client, curl
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     libpq-dev     curl     && apt-get clean     && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create necessary directories if they don't exist in the image
RUN mkdir -p temp_audio logs

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Specify PYTHONPATH if your app structure needs it (usually not for simple FastAPI)
# ENV PYTHONPATH=/app

EXPOSE 8000

# Healthcheck to verify the API is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3     CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application using Uvicorn with multiple workers
# Recommended for production instead of --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
