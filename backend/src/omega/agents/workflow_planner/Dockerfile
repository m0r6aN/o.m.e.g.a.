FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=9004
ENV MCP_PORT=9005
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379

CMD ["python", "agent.py"]