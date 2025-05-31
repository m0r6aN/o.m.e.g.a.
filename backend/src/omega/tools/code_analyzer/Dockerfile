# D:/Repos/o.m.e.g.a/backend/src/omega/tools/code_analyzer/Dockerfile

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY ./omega/tools/code_analyzer/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the tool code
COPY ./omega/tools/code_analyzer/tool.py .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV MCP_PORT=9209
ENV REGISTRY_URL=http://mcp_registry:9402
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${MCP_PORT}/health || exit 1

# Expose ports
EXPOSE ${MCP_PORT}

# Run the tool
CMD ["python", "tool.py"]