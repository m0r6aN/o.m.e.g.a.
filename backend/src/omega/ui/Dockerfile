# ui/Dockerfile

# Use Python 3.13 slim as the base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser

# Copy requirements.txt first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Set environment variables
ENV PORT=9601
ENV REGISTRY_URL=http://registry:9401
ENV ORCHESTRATOR_URL=http://orchestrator:9000
ENV HOST=0.0.0.0
ENV LOG_LEVEL=info

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 9601

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:9601/health || exit 1

# Run the application
CMD ["python", "app.py"]