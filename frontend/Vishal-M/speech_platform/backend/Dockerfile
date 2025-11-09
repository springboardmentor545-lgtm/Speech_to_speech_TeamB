FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user
WORKDIR $HOME/app

COPY --chown=user:user . .

# Ensure 'uploads' and 'exports' directories exist and are writable
RUN mkdir -p /var/data/uploads && mkdir -p /var/data/exports &&     chown -R user:user /var/data
# Symlink to locations within the home dir for easier access if needed
RUN ln -s /var/data/uploads $HOME/app/uploads &&     ln -s /var/data/exports $HOME/app/exports

EXPOSE 8000
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
