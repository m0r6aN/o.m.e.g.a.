# Simple Dockerfile for Prompt Optimizer Agent
FROM python:3.13.2-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent file
COPY agent.py .

# Expose ports
EXPOSE 9004
EXPOSE 9005

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:9004/health || exit 1

# Run the agent
CMD ["python", "agent.py"]