#!/bin/bash

echo "🧹 Starting Docker cleanup..."

# Stop all running containers
echo "Stopping all running containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "No running containers to stop"

# Remove all containers
echo "Removing all containers..."
docker rm $(docker ps -aq) 2>/dev/null || echo "No containers to remove"

# Remove all images
echo "Removing all images..."
docker rmi $(docker images -q) 2>/dev/null || echo "No images to remove"

# Remove all volumes
echo "Removing all volumes..."
docker volume rm $(docker volume ls -q) 2>/dev/null || echo "No volumes to remove"

# Remove all networks (except default ones)
echo "Removing custom networks..."
docker network rm $(docker network ls -q --filter type=custom) 2>/dev/null || echo "No custom networks to remove"

# Clean up build cache
echo "Cleaning build cache..."
docker builder prune -af

# Clean up system (removes unused data)
echo "Running system prune..."
docker system prune -af --volumes

# Show disk usage after cleanup
echo "📊 Docker disk usage after cleanup:"
docker system df

echo "✅ Docker cleanup completed!"
