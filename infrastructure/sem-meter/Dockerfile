FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY circuit_config.py .
COPY sem_consumer.py .

CMD ["python", "-u", "sem_consumer.py"]
