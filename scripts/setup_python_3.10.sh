#!/bin/bash

# Setup Python 3.10.7 for the project

set -e

echo "🐍 Setting up Python 3.10.7 for Synergy Project..."

# Check if pyenv is installed
if command -v pyenv &> /dev/null; then
    echo "✅ pyenv found"
    PYENV_AVAILABLE=true
else
    echo "⚠️  pyenv not found"
    PYENV_AVAILABLE=false
fi

# Check if Python 3.10 is available
if command -v python3.10 &> /dev/null; then
    PYTHON_310_AVAILABLE=true
    PYTHON_310_PATH=$(which python3.10)
    echo "✅ Python 3.10 found at: $PYTHON_310_PATH"
else
    PYTHON_310_AVAILABLE=false
    echo "⚠️  Python 3.10 not found"
fi

# Method 1: Use pyenv (if available)
if [ "$PYENV_AVAILABLE" = true ]; then
    echo ""
    echo "📦 Using pyenv to install Python 3.10.7..."
    
    # Check if 3.10.7 is already installed
    if pyenv versions --bare | grep -q "^3.10.7$"; then
        echo "✅ Python 3.10.7 already installed via pyenv"
    else
        echo "Installing Python 3.10.7 via pyenv..."
        pyenv install 3.10.7
    fi
    
    # Set local version
    cd "$(dirname "$0")/.."
    pyenv local 3.10.7
    echo "✅ Set Python 3.10.7 as local version"
    
    # Verify
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    echo "Current Python version: $PYTHON_VERSION"
    
    # Recreate venv
    echo ""
    echo "🔄 Recreating virtual environment..."
    cd backend
    if [ -d "venv" ]; then
        echo "Removing old virtual environment..."
        rm -rf venv
    fi
    
    python -m venv venv
    source venv/bin/activate
    
    echo "✅ Virtual environment created with Python $(python --version)"
    
    echo ""
    echo "📦 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "To activate the virtual environment:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    
# Method 2: Use system Python 3.10 (if available)
elif [ "$PYTHON_310_AVAILABLE" = true ]; then
    echo ""
    echo "📦 Using system Python 3.10..."
    
    cd "$(dirname "$0")/.."
    cd backend
    
    if [ -d "venv" ]; then
        echo "Removing old virtual environment..."
        rm -rf venv
    fi
    
    python3.10 -m venv venv
    source venv/bin/activate
    
    echo "✅ Virtual environment created with Python $(python --version)"
    
    echo ""
    echo "📦 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo ""
    echo "✅ Setup complete!"
    
# Method 3: Install pyenv
else
    echo ""
    echo "❌ Python 3.10 not found and pyenv not available"
    echo ""
    echo "Please install Python 3.10.7 using one of these methods:"
    echo ""
    echo "Option 1: Install pyenv (Recommended)"
    echo "  brew install pyenv"
    echo "  Then run this script again"
    echo ""
    echo "Option 2: Install Python 3.10 via Homebrew"
    echo "  brew install python@3.10"
    echo "  Then run this script again"
    echo ""
    echo "Option 3: Use Docker (No local Python needed)"
    echo "  cd infrastructure/docker"
    echo "  docker-compose -f docker-compose.microservices.yml up -d"
    echo ""
    exit 1
fi

