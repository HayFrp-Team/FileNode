FROM python:3.11-alpine

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
ENV PATH=/root/.local/bin:$PATH \
    PORT=5000 \
    WORKDIR=/app/files \
    SYNC_COOLDOWN=300 \
    MAX_RETRY=3 \
    UVICORN_WORKERS=4
EXPOSE $PORT
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port $PORT --workers $UVICORN_WORKERS"]
