FROM python:3.8

ENV PYTHONUNBUFFERED 1
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade \
        pip \
        setuptools
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./src/objects/TheHiveConnector.py /app/objects/TheHiveConnector.py
COPY ./src/objects/QRadarConnector.py /app/objects/QRadarConnector.py
COPY ./src/settings.py /app/settings.py
COPY ./src/dramatiq_tasks /app/dramatiq_tasks

CMD dramatiq dramatiq_tasks.tasks
