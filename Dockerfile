FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -r appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./

# Set ownership for the app user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check using the /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]