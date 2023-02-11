FROM python:3-slim
RUN apk git
ADD . /app
WORKDIR /app

# We are installing a dependency here directly into our app source dir
RUN pip install --target=/app -r /app/requirements.txt

ENV PYTHONPATH /app
CMD ["/app/main.py"]