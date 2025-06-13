# Multi-stage build for lean, mean, agent machines! 🚀
FROM python:3.12.3-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- PRODUCTION STAGE ---
FROM python:3.12.3-slim AS production

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory and Python path
WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user for security (because we're not cowboys)
RUN groupadd -r omega && useradd -r -g omega omega

# Copy only what we need (more surgical than `COPY . .`)
COPY --chown=omega:omega omega/ ./omega/

# Switch to non-root user
USER omega

# Health check with proper error handling
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT}/health', timeout=5)" || exit 1

# Dynamic port exposure based on environment
EXPOSE ${PORT}
EXPOSE ${MCP_PORT}

# Graceful shutdown signal handling
STOPSIGNAL SIGTERM

# Run as module with proper signal handling
CMD ["python", "-m", "omega.agents.${AGENT_NAME}.agent"]