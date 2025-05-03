# agents/project_architect/Dockerfile
FROM python:3.13.2-slim

WORKDIR /app

# Copy requirements
COPY src/omega/agents/project_architect/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy omega package structure
COPY src/omega /app/omega

# Copy agent code
COPY src/omega/agents/project_architect /app/agent

# Set environment variables
ENV PORT=9016
ENV MCP_PORT=9017
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV REGISTRY_URL=http://registry:9401

# Add OpenAI API key env var (this will be overridden at runtime)
ENV OPENAI_API_KEY=""

# Run the agent
CMD ["python", "agent.py"]