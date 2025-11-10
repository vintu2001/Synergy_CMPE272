"""
Vercel serverless entry point for FastAPI application.
"""
from app.main import app

# Vercel will use this as the entry point
handler = app

