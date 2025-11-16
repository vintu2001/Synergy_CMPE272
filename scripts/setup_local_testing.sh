#!/bin/bash

# Setup script for local microservices testing

set -e

echo "🚀 Setting up local microservices testing environment..."

# Step 1: Check if ChromaDB is initialized
echo ""
echo "📦 Step 1: Checking ChromaDB initialization..."
if [ ! -d "services/decision-simulation/vector_stores/chroma_db" ]; then
    echo "   ChromaDB not found. Initializing..."
    
    if [ ! -d "backend" ]; then
        echo "   ❌ Error: backend directory not found!"
        exit 1
    fi
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "   Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "   Installing dependencies..."
    pip install -q -r requirements.txt
    
    # Ingest documents
    echo "   Ingesting knowledge base documents..."
    python kb/ingest_documents.py
    
    # Copy ChromaDB to decision-simulation service
    echo "   Copying ChromaDB to decision-simulation service..."
    mkdir -p ../services/decision-simulation/vector_stores
    cp -r vector_stores/chroma_db ../services/decision-simulation/vector_stores/
    
    cd ..
    echo "   ✅ ChromaDB initialized successfully!"
else
    echo "   ✅ ChromaDB already exists. Skipping initialization."
fi

# Step 2: Check environment file
echo ""
echo "📝 Step 2: Checking environment configuration..."
if [ ! -f "infrastructure/docker/.env" ]; then
    echo "   Creating .env file template..."
    cat > infrastructure/docker/.env << EOF
# AWS Configuration
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DYNAMODB_TABLE_NAME=aam_requests
AWS_SQS_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/123456789/request-queue

# Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Admin API Key
ADMIN_API_KEY=test-admin-key
EOF
    echo "   ⚠️  Please edit infrastructure/docker/.env with your actual credentials!"
else
    echo "   ✅ .env file exists."
fi

# Step 3: Check frontend configuration
echo ""
echo "🌐 Step 3: Checking frontend configuration..."
if [ ! -f "frontend/.env.local" ]; then
    echo "   Creating frontend .env.local..."
    echo "VITE_API_BASE_URL=http://localhost:8001" > frontend/.env.local
    echo "   ✅ Frontend configured to use Request Management Service (port 8001)"
else
    echo "   ✅ Frontend .env.local exists."
fi

# Step 4: Summary
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit infrastructure/docker/.env with your AWS and Gemini credentials"
echo "2. Start services:"
echo "   cd infrastructure/docker"
echo "   docker-compose -f docker-compose.microservices.yml up -d"
echo "3. Start frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo "4. Open http://localhost:5173 in your browser"
echo ""
echo "For detailed instructions, see LOCAL_TESTING_GUIDE.md"

