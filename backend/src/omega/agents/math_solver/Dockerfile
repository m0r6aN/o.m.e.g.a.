# Standardized Dockerfile for OMEGA Agents/Services/Tools
FROM python:3.13.2-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire OMEGA source code
COPY . .

# Install OMEGA in development mode
RUN pip install -e .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' omega && \
    chown -R omega:omega /app
USER omega

# Health check endpoint (all agents/services should have this)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-9002}/health || exit 1

# Default command - to be overridden in docker-compose
CMD ["python", "-m", "omega.cli.agent"]