# D:/Repos/o.m.e.g.a/backend/src/omega/services/mcp_registry/Dockerfile

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service code
COPY service.py .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PORT=9402
ENV MONGODB_URL=mongodb://omega:omegapass@mongo:27017/omega?authSource=admin
ENV MONGODB_NAME=omega
ENV HEARTBEAT_TIMEOUT=60
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run the service
CMD ["python", "service.py"]