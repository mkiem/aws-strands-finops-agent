#!/bin/bash

# Build WebSocket API Lambda packages
# Following project rules for deployment package creation

set -e

echo "Building WebSocket API Lambda packages..."

# Get absolute path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"

# Create build directory
mkdir -p "$BUILD_DIR"

# Function to build Lambda package
build_lambda_package() {
    local function_name=$1
    local source_dir="$SCRIPT_DIR/$2"
    
    echo "Building $function_name..."
    
    # Create temporary directory
    temp_dir=$(mktemp -d)
    
    # Copy source files
    cp -r "$source_dir"/* "$temp_dir/"
    
    # Install dependencies
    if [ -f "$temp_dir/requirements.txt" ]; then
        pip install -r "$temp_dir/requirements.txt" -t "$temp_dir/"
    fi
    
    # Remove unnecessary files
    find "$temp_dir" -name "*.pyc" -delete
    find "$temp_dir" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Create zip package
    cd "$temp_dir"
    zip -r "$BUILD_DIR/${function_name}.zip" . -x "*.git*" "*.DS_Store*" "requirements.txt"
    cd - > /dev/null
    
    # Cleanup
    rm -rf "$temp_dir"
    
    echo "✅ $function_name package created: $BUILD_DIR/${function_name}.zip"
}

# Build all Lambda packages
build_lambda_package "websocket-connection-manager" "connection_manager"
build_lambda_package "websocket-message-handler" "message_handler"
build_lambda_package "websocket-background-processor" "progress_notifier"

echo "🎉 All WebSocket API Lambda packages built successfully!"
echo "📦 Packages location: $BUILD_DIR"
ls -la "$BUILD_DIR"
