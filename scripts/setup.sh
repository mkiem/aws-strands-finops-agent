#!/bin/bash

# FinOps Agent Setup Script
# This script sets up the FinOps Agent development environment

set -e

echo "🚀 FinOps Agent Setup Script"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on supported OS
check_os() {
    print_status "Checking operating system..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    print_status "Detected OS: $OS"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python version: $PYTHON_VERSION"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+"
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    print_status "Node.js version: $NODE_VERSION"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_warning "AWS CLI is not installed. Please install AWS CLI for deployment."
    else
        AWS_VERSION=$(aws --version)
        print_status "AWS CLI version: $AWS_VERSION"
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install Git."
        exit 1
    fi
}

# Setup Python environment
setup_python() {
    print_status "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        print_status "Installing Python dependencies..."
        pip install -r requirements.txt
    else
        print_warning "requirements.txt not found"
    fi
    
    # Install development dependencies
    print_status "Installing development dependencies..."
    pip install pytest pytest-cov flake8 black isort
}

# Setup Node.js environment
setup_nodejs() {
    print_status "Setting up Node.js environment..."
    
    if [ -d "finops-ui" ]; then
        cd finops-ui
        print_status "Installing Node.js dependencies..."
        npm install
        cd ..
    else
        print_warning "finops-ui directory not found"
    fi
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.template" ]; then
            cp .env.template .env
            print_status "Created .env file from template"
            print_warning "Please edit .env file with your AWS configuration"
        else
            print_warning ".env.template not found"
        fi
    else
        print_status ".env file already exists"
    fi
}

# Verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Check Python environment
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_status "Python virtual environment: ✓"
        
        # Check if we can import key modules
        python3 -c "import boto3" 2>/dev/null && print_status "boto3: ✓" || print_warning "boto3: ✗"
    fi
    
    # Check Node.js environment
    if [ -d "finops-ui/node_modules" ]; then
        print_status "Node.js dependencies: ✓"
    else
        print_warning "Node.js dependencies: ✗"
    fi
}

# Main setup function
main() {
    echo
    print_status "Starting FinOps Agent setup..."
    echo
    
    check_os
    check_prerequisites
    setup_python
    setup_nodejs
    setup_environment
    verify_installation
    
    echo
    print_status "Setup completed successfully! 🎉"
    echo
    print_status "Next steps:"
    echo "  1. Edit .env file with your AWS configuration"
    echo "  2. Configure AWS CLI: aws configure"
    echo "  3. Run tests: source venv/bin/activate && pytest"
    echo "  4. Start development: cd finops-ui && npm start"
    echo
    print_status "For more information, see the README.md file"
}

# Run main function
main "$@"
