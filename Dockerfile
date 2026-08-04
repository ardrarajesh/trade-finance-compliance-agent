# One image runs either the API or the UI (the command is chosen in compose).
FROM python:3.11-slim

# Keep Python lean and unbuffered for clean container logs.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better layer caching: deps change less than code).
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the source and install the package.
COPY src ./src
COPY data ./data
COPY ui ./ui
RUN pip install -e .

EXPOSE 8000 8501

# Default command runs the API; compose overrides it for the UI service.
CMD ["uvicorn", "tradefin.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
