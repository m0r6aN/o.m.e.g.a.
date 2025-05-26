FROM python:3.13.2-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY ./omega/tools/code_analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire omega package needed for the tool
COPY ../../../omega /app/omega

COPY ./omega/tools/code_analyzer/tool.py .

# Expose ports
EXPOSE 9208

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9208/health || exit 1

# Run the agent
# Python will look for modules in the current directory (/app) and in PYTHONPATH.
# Since /app/omega will exist, "from omega.core..." should work.
CMD ["python", "tool.py"]