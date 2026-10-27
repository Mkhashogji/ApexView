# F1 Engineering API Dockerfile
FROM python:3.11-slim@sha256:90744cff8f32887f075c47d747a173ff333e9e98801667af93c357fa9f5e28ff

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY apps/api/pyproject.toml apps/api/constraints.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir pip==26.2.1 && \
    pip install --no-cache-dir -c constraints.txt .

# Copy application code
COPY apps/api/app /app/app

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Create non-root user for security
RUN useradd -m -u 1000 apiuser

# Create cache directories with proper ownership
RUN mkdir -p /app/data/cache/parquet /app/data/cache/sqlite && \
    chown -R apiuser:apiuser /app

USER apiuser

# Expose port
EXPOSE 8000

# Health check using built-in urllib instead of requests
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
