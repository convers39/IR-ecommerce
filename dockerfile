FROM python:3.8.6-slim-buster

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y netcat-openbsd gcc && \
    apt-get clean

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

RUN addgroup --system user && adduser --system --no-create-home --group user && \
    chown -R user:user /usr/src/app && chmod -R 755 /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install --upgrade pip \
    pip install -r requirements.txt

USER user

COPY . /usr/src/app
