
FROM python:alpine

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip && \
    pip install -r backend/requirements.txt

CMD ["echo", "Override me in docker-compose"]
