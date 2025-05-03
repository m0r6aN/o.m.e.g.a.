FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=9008
ENV MCP_PORT=9009
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379

CMD ["python", "agent.py"]