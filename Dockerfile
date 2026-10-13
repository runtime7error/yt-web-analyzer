FROM python:3.12-slim

# Instala ffmpeg para conversão e junção de áudio e vídeo
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py ./

EXPOSE 8000

ENV PORT=8000
CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
