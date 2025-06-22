#!/bin/bash

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "Using Docker..."
    CONTAINER_ENGINE="docker"
# If Docker is not available, check for Podman
elif command -v podman &> /dev/null; then
    echo "Docker not found. Using Podman..."
    CONTAINER_ENGINE="podman"
else
    echo "Error: Neither Docker nor Podman is installed."
    exit 1
fi

# Build the image
echo "Building image with $CONTAINER_ENGINE..."
$CONTAINER_ENGINE build -t npmsync .

# Run the container
echo "Running container with $CONTAINER_ENGINE..."
$CONTAINER_ENGINE run npmsync

# Note: Add additional parameters as needed
# For example: $CONTAINER_ENGINE run -p 8000:8000 npmsync
