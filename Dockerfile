FROM python:3.9.2-slim-buster
RUN apt-get update && apt-get install -y wget \
    && apt-get install -y --no-install-recommends gcc libffi-dev musl-dev ffmpeg aria2 python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/
RUN pip install --upgrade pip -r requirements.txt
CMD gunicorn app:app & python3 main.py
