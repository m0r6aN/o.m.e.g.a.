FROM python:3.13.2-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=9018
ENV MCP_PORT=9019   
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV REGISTRY_URL=http://registry:9401
# Add OpenAI API key env var (this will be overridden at runtime)
ENV OPENAI_API_KEY=""

# Run the agent
CMD ["python", "agent.py"]