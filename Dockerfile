FROM python:3-slim

ARG DEBIAN_FRONTEND="noninteractive"

RUN pip install pipenv

ADD . /app
WORKDIR /app

RUN apt-get update \
    && apt-get install --yes git \
    && rm -rf /var/lib/apt/lists/*

# We are installing a dependency here directly into our app source dir
RUN pip install --target=/app -r /app/requirements.txt

CMD ['python', "/app/main.py"]