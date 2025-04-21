FROM python:3.11-alpine

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
ENV PATH=/root/.local/bin:$PATH \
    PORT=5000 \
    WORKDIR=file \
    SYNC_COOLDOWN=300 \
    MAX_RETRY=3 \
    GUNICORN_WORKERS=4 \
    GUNICORN_TIMEOUT=120
EXPOSE $PORT

CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "$GUNICORN_WORKERS", "--timeout", "$GUNICORN_TIMEOUT", "app:app"]