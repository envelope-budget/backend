#!/bin/bash

# Set variables
DOCKER_USERNAME="xhenxhe"
APP_NAME="envelopebudget"
TAG="latest"

# Full image name
IMAGE_NAME="$DOCKER_USERNAME/$APP_NAME:$TAG"

# Enable buildx
echo "🔧 Setting up Docker buildx..."
docker buildx create --name multiarch-builder --use

# Build and push for multiple architectures
echo "🔨 Building and pushing Docker image for multiple architectures..."
docker buildx build --platform linux/amd64,linux/arm64 \
  -t $IMAGE_NAME \
  --push \
  .

# Check if build and push was successful
if [ $? -ne 0 ]; then
    echo "❌ Docker build and push failed. Exiting."
    exit 1
fi

echo "✅ Multi-architecture image successfully built and pushed to Docker Hub as $IMAGE_NAME"

# Verify the multi-arch image
echo "🔍 Verifying multi-architecture support..."
docker buildx imagetools inspect $IMAGE_NAME

echo "🎉 Process completed successfully!"
