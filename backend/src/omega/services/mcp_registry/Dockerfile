# backend/src/omega/services/mcp_registry/Dockerfile

FROM python:3.13.2-slim

WORKDIR /app

COPY service.py .

RUN pip install fastapi uvicorn redis pydantic

CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "9401"]