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

COPY ./entrypoints /app
COPY ./requirements.txt /tmp/requirements.txt
COPY ./thirdparty /tmp/thirdparty
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN pip install --no-cache-dir /tmp/thirdparty/pyninox/

COPY ./src /app
