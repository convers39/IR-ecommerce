FROM python:3.8.6-slim-buster

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y netcat-openbsd gcc && \
    apt-get clean

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

RUN addgroup --system admin && adduser --system --no-create-home --group admin && \
    chown -R admin:admin /usr && chmod -R 755 /usr

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install --upgrade pip \
    pip install -r requirements.txt

USER admin

COPY . /usr/src/app

# ENV TERM xterm
# ENV ZSH_THEME agnoster
# RUN wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true
# CMD [ "zsh" ]