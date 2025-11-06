FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing pyc files and buffer output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=main.py

EXPOSE 5000

# Use gunicorn to serve the Flask app in the container
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app", "--workers", "1"]
