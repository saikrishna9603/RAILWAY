"""
FastAPI Backend Configuration
MongoDB Atlas Integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

# Allowed CORS origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "https://tatkal.vercel.app",  # Vercel frontend
    "https://*.vercel.app",  # All Vercel preview deployments
    "https://*.onrender.com",  # Render domains
]

# Initialize FastAPI app
app = FastAPI(
    title="Tatkal Booking API",
    description="Multi-agent AI train booking system backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"]
)

# MongoDB Atlas connection string
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
)

# Database settings
DB_NAME = "tatkal_booking"
COLLECTIONS = {
    "trains": "trains",
    "bookings": "bookings",
    "users": "users",
    "search_logs": "search_logs",
    "agent_activities": "agent_activities",
}

print("[OK] FastAPI Backend Initialized")
print("[OK] MongoDB URL configured")
print("[OK] CORS enabled for frontend")
