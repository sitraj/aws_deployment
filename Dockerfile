FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create directory for SSL certificates
RUN mkdir -p /app/ssl

# Make health check script executable
RUN chmod +x scripts/healthcheck.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose both HTTP and HTTPS ports
EXPOSE 8080 443

# Health check using our custom script
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ./scripts/healthcheck.sh

# Run the application
CMD ["python", "app.py"] 