# Minimal Dockerfile for OMEGA Test Agent
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
EXPOSE 9014
EXPOSE 9015

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9014/health || exit 1

# Run the agent
CMD ["python", "agent.py"]