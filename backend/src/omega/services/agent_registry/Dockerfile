# OMEGA Agent Registry - Minimal Service
FROM python:3.12.3-slim

# Set working directory
WORKDIR /app

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.0 \
    redis==5.0.1 \
    pydantic==2.8.0

# Copy service code
COPY service.py /app/service.py

# Create non-root user
RUN groupadd -r omega && useradd -r -g omega omega
RUN chown -R omega:omega /app
USER omega

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9401/health', timeout=5)" || exit 1

# Expose port
EXPOSE 9401

# Run the service
CMD ["python", "service.py"]