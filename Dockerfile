# Use an official Python runtime as the base image
FROM python:3.13.5-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=0

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  nodejs \
  npm \
  nginx \
  netcat-traditional \
  curl \
  # Add these for PostgreSQL support
  libpq-dev \
  gcc \
  # Cleanup in same layer to reduce image size
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip

# Copy requirements first for better Docker layer caching
COPY requirements.txt dev_requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
  && pip install --no-cache-dir -r dev_requirements.txt \
  && pip install gunicorn

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Copy the Django project files into the container
COPY . .

# Copy and set up entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/sites-available/default

# Create a volume for persistent data
VOLUME ["/app/db", "/app/media", "/app/logs"]

# Health check (remove for now until we get basic functionality working)
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost/health/ || exit 1

# Expose the port Nginx will run on
EXPOSE 80

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
