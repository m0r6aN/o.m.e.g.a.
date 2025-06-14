# OMEGA Orchestrator Agent - Enterprise Edition 🚀
# Multi-stage build for maximum security and minimal size

# --- STAGE 1: DEPENDENCY BUILDER ---
FROM python:3.12.3-slim as dependencies

# Install build dependencies for compilation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment for isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for optimal layer caching
COPY requirements.txt .

# Install Python dependencies with optimization flags
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# --- STAGE 2: RUNTIME ENVIRONMENT ---
FROM python:3.12.3-slim as runtime

# Security: Create non-root user
RUN groupadd -r omega && useradd -r -g omega -s /bin/bash omega

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    psutil \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set optimal Python settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=omega:omega omega/ ./omega/

# Create directories for logs and data with proper permissions
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chown -R omega:omega /app

# Switch to non-root user for security
USER omega

# Health check with comprehensive validation
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "\
import requests, sys, os, json; \
try: \
    port = os.getenv('PORT', '9000'); \
    r = requests.get(f'http://localhost:{port}/health', timeout=5); \
    health = r.json(); \
    if r.status_code == 200 and health.get('status') in ['healthy', 'degraded']: \
        print(f'✅ Orchestrator healthy: {health.get(\"agent_id\")}'); \
        sys.exit(0); \
    else: \
        print(f'❌ Orchestrator unhealthy: {health}'); \
        sys.exit(1); \
except Exception as e: \
    print(f'❌ Health check failed: {e}'); \
    sys.exit(1)"

# Expose ports for API and MCP
EXPOSE 9000 9001

# Graceful shutdown handling
STOPSIGNAL SIGTERM

# Set default environment variables
ENV AGENT_NAME=orchestrator \
    PORT=9000 \
    MCP_PORT=9001 \
    LOG_LEVEL=info

# Professional module execution with proper signal handling
CMD ["python", "-m", "omega.agents.orchestrator.agent"]

# --- METADATA ---
LABEL maintainer="OMEGA Dream Team <omega@legendary.dev>"
LABEL version="2.0.0"
LABEL description="OMEGA Orchestrator Agent - Central Command"
LABEL agent.name="orchestrator"
LABEL agent.type="coordination"
LABEL agent.capabilities="workflow_orchestration,task_delegation,progress_monitoring"
LABEL org.opencontainers.image.title="OMEGA Orchestrator Agent"
LABEL org.opencontainers.image.description="Central command agent for coordinating complex multi-agent workflows"
LABEL org.opencontainers.image.version="2.0.0"
LABEL org.opencontainers.image.vendor="OMEGA Framework"
LABEL org.opencontainers.image.licenses="MIT"