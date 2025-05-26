# Simple Dockerfile for agent_registry service
FROM python:3.13-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service file
COPY service.py .

# Expose the port
EXPOSE 9401

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9401/health || exit 1

# Run the service
CMD ["python", "service.py"]