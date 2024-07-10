# Use an official Python runtime as the base image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG 0

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  nodejs \
  npm \
  nginx

# Install Python dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dev_requirements.txt .
RUN pip install --no-cache-dir -r dev_requirements.txt

# Install Gunicorn
RUN pip install gunicorn

# Copy the Django project files into the container
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/sites-available/default

# Expose the port Nginx will run on
EXPOSE 80

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
