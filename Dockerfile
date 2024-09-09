FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY /flask /app

RUN pip install --no-cache-dir -r requirements.txt


ENV FLASK_APP=app.py

EXPOSE 3000
CMD ["flask", "run", "--host=0.0.0.0", "--port=3000"]
