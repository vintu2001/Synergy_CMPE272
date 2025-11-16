#!/bin/bash

# Quick fix: Use Homebrew to install Python 3.10 if available

set -e

echo "🔧 Quick Fix: Setting up Python 3.10..."

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install it first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Install Python 3.10
echo "📦 Installing Python 3.10 via Homebrew..."
brew install python@3.10

# Verify
if command -v python3.10 &> /dev/null; then
    echo "✅ Python 3.10 installed: $(python3.10 --version)"
    
    # Recreate venv
    cd "$(dirname "$0")/.."
    cd backend
    
    if [ -d "venv" ]; then
        echo "Removing old virtual environment..."
        rm -rf venv
    fi
    
    echo "Creating new virtual environment with Python 3.10..."
    python3.10 -m venv venv
    source venv/bin/activate
    
    echo "✅ Virtual environment created: $(python --version)"
    
    echo ""
    echo "📦 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo ""
    echo "✅ Done! Virtual environment is ready."
    echo ""
    echo "To activate:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
else
    echo "❌ Failed to install Python 3.10"
    exit 1
fi

