FROM python:3.12-slim

# tried alpine but had issues with psycopg2 compilation
# FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# TODO: maybe add a non-root user later for security
# RUN adduser --disabled-password --gecos '' appuser
# USER appuser

COPY app.py .
COPY templates/ templates/
COPY static/ static/

EXPOSE 8080

# tried gunicorn but overkill for demo
# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
CMD ["python", "app.py"]
