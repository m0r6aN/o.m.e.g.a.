# tools/calculator/Dockerfile

# Use Python 3.9 slim as the base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos "" appuser

# Copy requirements.txt first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables with defaults
ENV PORT=9201
ENV REGISTRY_URL=http://registry:9401
ENV HOST=localhost
ENV LOG_LEVEL=info

# Change ownership to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Run the application
CMD ["python", "tool.py"]