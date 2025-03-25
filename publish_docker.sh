#!/bin/bash

# Clean the compressor cache
rm -rf ./static/CACHE

# Set variables
DOCKER_USERNAME="xhenxhe"
APP_NAME="envelopebudget"
TAG="latest"
DATE_TAG=$(date +"%Y%m%d")

# Full image names
IMAGE_NAME="$DOCKER_USERNAME/$APP_NAME:$TAG"
DATE_IMAGE_NAME="$DOCKER_USERNAME/$APP_NAME:$DATE_TAG"

# Enable buildx
echo "🔧 Setting up Docker buildx..."
docker buildx create --name multiarch-builder --use

# Build and push for multiple architectures
echo "🔨 Building and pushing Docker image for multiple architectures..."
docker buildx build --platform linux/amd64,linux/arm64 \
  -t $IMAGE_NAME \
  -t $DATE_IMAGE_NAME \
  --push \
  .

# Check if build and push was successful
if [ $? -ne 0 ]; then
  echo "❌ Docker build and push failed. Exiting."
  exit 1
fi

echo "✅ Multi-architecture images successfully built and pushed to Docker Hub as $IMAGE_NAME and $DATE_IMAGE_NAME"

# Verify the multi-arch images
echo "🔍 Verifying multi-architecture support..."
docker buildx imagetools inspect $IMAGE_NAME
docker buildx imagetools inspect $DATE_IMAGE_NAME

echo "🎉 Process completed successfully!"
