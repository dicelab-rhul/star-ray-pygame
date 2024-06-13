#!/bin/bash

# Run unit tests
echo "Running unit tests..."
python -m unittest discover -s test

# Check if tests passed
if [ $? -ne 0 ]; then
    echo "Unit tests failed. Aborting build."
    exit 1
fi

# Build the package
echo "Building package..."
python -m build --wheel

# Check if the build was successful
if [ $? -ne 0 ]; then
    echo "Build failed."
    exit 1
fi

echo "Build successful."
