# registry_service/Dockerfile

FROM python:alpine3.21

WORKDIR /app

COPY registry_service_app.py .

RUN pip install fastapi uvicorn redis pydantic

CMD ["uvicorn", "registry_service_app:app", "--host", "0.0.0.0", "--port", "8500"]