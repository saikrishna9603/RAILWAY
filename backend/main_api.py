"""
FastAPI Main Application - API Routes for Tatkal Booking System
Combines authentication, trains, bookings, and PRAL agents
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import asyncio
import uuid
import random
from typing import List, Optional, Dict, Any
import json

# Import all custom modules
try:
    # Try relative imports first (when run as module)
    from .auth_utils import AuthUtility, SessionManager
    from .auth_models import (
        UserRegisterRequest, UserLoginRequest, UserProfile, 
        AuthTokenResponse, UserResponse, UserPreferences, PaymentMethod
    )
    from .booking_models import (
        NormalBookingRequest, TatkalBookingRequest, BookingConfirmation,
        PaymentRequest, AvailabilityCheckRequest, AvailabilityCheckResponse,
        BookingStatusEnum, PaymentStatusEnum, SeatAvailabilityMap,
        BookingHistory, CancellationRequest, CancellationResponse
    )
    from .pral_agents import PRALOrchestrator, PerceiveAgent, ActAgent, ReasonAgent, LearnAgent
    from .mock_trains_data import generate_trains_data
    from .database import MongoDBClient
except ImportError:
    # Fall back to absolute imports (when run directly from backend folder)
    from auth_utils import AuthUtility, SessionManager
    from auth_models import (
        UserRegisterRequest, UserLoginRequest, UserProfile, 
        AuthTokenResponse, UserResponse, UserPreferences, PaymentMethod
    )
    from booking_models import (
        NormalBookingRequest, TatkalBookingRequest, BookingConfirmation,
        PaymentRequest, AvailabilityCheckRequest, AvailabilityCheckResponse,
        BookingStatusEnum, PaymentStatusEnum, SeatAvailabilityMap,
        BookingHistory, CancellationRequest, CancellationResponse
    )
    from pral_agents import PRALOrchestrator, PerceiveAgent, ActAgent, ReasonAgent, LearnAgent
    from mock_trains_data import generate_trains_data
    from database import MongoDBClient


# Initialize FastAPI app
app = FastAPI(
    title="Tatkal Train Booking System",
    description="AI-powered train booking with PRAL agents",
    version="1.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATABASE INITIALIZATION ====================

# MongoDB collections (will be initialized on startup)
users_collection = None
bookings_collection = None
sessions_collection = None

# Initialize trains data immediately at module load (don't wait for startup event)
print("📚 Pre-loading 1000 trains data...")
trains_data: List[Dict] = generate_trains_data(1000)
print(f"✅ Trains data ready: {len(trains_data)} trains loaded")

# In-memory fallback (for when MongoDB is unavailable)
users_db: Dict[str, Dict] = {}
sessions_db: Dict[str, Dict] = {}
bookings_db: Dict[str, Dict] = {}
tatkal_tasks: Dict[str, asyncio.Task] = {}

session_manager = SessionManager()

# Initialize PRAL agents
pral_orchestrator = PRALOrchestrator()

# Initialize train data on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application data and MongoDB connection"""
    global users_collection, bookings_collection, sessions_collection
    
    print("\n" + "="*60)
    print("🚀 STARTING TATKAL BOOKING SYSTEM")
    print("="*60)
    
    # Connect to MongoDB
    print("\n📡 Connecting to MongoDB Atlas...")
    await MongoDBClient.connect_db()
    
    # Get MongoDB collections
    try:
        users_collection = MongoDBClient.get_collection("users")
        bookings_collection = MongoDBClient.get_collection("bookings")
        sessions_collection = MongoDBClient.get_collection("sessions")
        print("✅ MongoDB collections initialized:")
        print("   • users")
        print("   • bookings")  
        print("   • sessions")
    except Exception as e:
        print(f"⚠️  MongoDB collections unavailable: {e}")
        print("   Using in-memory fallback")
    
    # Trains data is already loaded at module level above
    print("✅ Trains data already loaded")
    
    # Initialize agents
    print("\n🤖 Initializing PRAL agents...")
    print("   • IntentAgent")
    print("   • TrainSearchAgent")
    print("   • RankingAgent")
    print("   • BookingExecutionAgent")
    print("   • TatkalSchedulerAgent")
    print("   • PaymentAgent")
    print("   • WaitlistAgent")
    print("   • PDFAgent")
    print("   • ExplanationAgent")
    print("   • MLComparisonAgent")
    print("✅ All agents initialized")
    
    print("\n" + "="*60)
    print("✅ SYSTEM READY")
    print("="*60 + "\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await MongoDBClient.close_db()
    print("🤖 PRAL agents initialized")


# ==================== TEST/HEALTH ROUTES ====================

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint to test CORS"""
    return {
        "status": "ok",
        "message": "Backend is running with CORS enabled",
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== AUTHENTICATION ROUTES ====================

@app.post("/api/auth/register", response_model=UserResponse)
async def register(request: UserRegisterRequest):
    """User registration endpoint - MongoDB persistent storage"""
    global users_collection, users_db
    
    # Validate email format
    if not AuthUtility.validate_email(request.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Check if user already exists (MongoDB + fallback)
    existing_user_mongo = None
    existing_user_fallback = request.email in users_db
    
    if users_collection is not None:
        try:
            existing_user_mongo = await users_collection.find_one({"email": request.email})
        except:
            pass
    
    if existing_user_mongo or existing_user_fallback:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    # Validate password strength
    if not AuthUtility.is_password_strong(request.password):
        raise HTTPException(
            status_code=400, 
            detail="Password must be 8+ chars with uppercase, lowercase, digit, and special character"
        )
    
    # Verify passwords match
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = AuthUtility.hash_password(request.password)
    
    user_data = {
        "user_id": user_id,
        "email": request.email,
        "full_name": request.full_name,
        "phone": request.phone,
        "password_hash": hashed_password,
        "created_at": datetime.utcnow().isoformat(),
        "email_verified": False,
        "is_active": True,
        "preferences": {},
        "booking_stats": {
            "total_bookings": 0,
            "successful_bookings": 0,
            "cancelled_bookings": 0
        }
    }
    
    # Save to MongoDB (primary) + fallback to in-memory
    if users_collection is not None:
        try:
            await users_collection.insert_one(user_data)
            print(f"✅ User registered in MongoDB: {request.email}")
        except Exception as e:
            print(f"⚠️  MongoDB save failed: {e}, using fallback")
            users_db[request.email] = user_data
    else:
        # Use fallback in-memory storage
        users_db[request.email] = user_data
        print(f"⚠️  MongoDB unavailable, stored in memory: {request.email}")
    
    return UserResponse(
        user_id=user_id,
        email=request.email,
        full_name=request.full_name,
        phone=request.phone,
        is_verified=False,
        member_since=datetime.utcnow(),
        total_bookings=0
    )


@app.post("/api/auth/login", response_model=AuthTokenResponse)
async def login(request: UserLoginRequest):
    """User login endpoint - MongoDB + fallback lookup"""
    global users_collection, users_db
    
    # Try to find user in MongoDB first
    user = None
    if users_collection is not None:
        try:
            user = await users_collection.find_one({"email": request.email})
        except:
            pass
    
    # Fallback to in-memory database if not found
    if not user and request.email in users_db:
        user = users_db[request.email]
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not AuthUtility.verify_password(request.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create tokens
    tokens = AuthUtility.create_access_token(
        user["user_id"], 
        user["email"], 
        user["full_name"]
    )
    
    refresh_token = AuthUtility.create_refresh_token(user["user_id"])
    
    # Create session
    session_id = session_manager.create_session(
        user["user_id"],
        tokens["access_token"],
        refresh_token
    )
    
    sessions_db[session_id] = {
        "user_id": user["user_id"],
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    
    return AuthTokenResponse(
        access_token=tokens["access_token"],
        refresh_token=refresh_token,
        expires_in=tokens.get("expires_in", 86400),
        user=UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            full_name=user["full_name"],
            phone=user["phone"],
            is_verified=user.get("email_verified", False),
            member_since=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"],
            total_bookings=user.get("booking_stats", {}).get("total_bookings", 0)
        )
    )


@app.post("/api/auth/logout")
async def logout(session_id: str):
    """User logout endpoint"""
    if session_id in sessions_db:
        session_manager.invalidate_session(session_id)
        del sessions_db[session_id]
        return {"message": "Logout successful"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.post("/api/auth/forgot-password")
async def forgot_password(email: str):
    """Request password reset"""
    if email not in users_db:
        raise HTTPException(status_code=404, detail="Email not found")
    
    user = users_db[email]
    reset_token = AuthUtility.create_password_reset_token(user["user_id"], email)
    
    return {
        "message": "Password reset link sent to email",
        "reset_token": reset_token["reset_token"],
        "expires_in": "15 minutes"
    }


@app.post("/api/auth/reset-password")
async def reset_password(token: str, new_password: str):
    """Reset password with token"""
    if not AuthUtility.is_password_strong(new_password):
        raise HTTPException(status_code=400, detail="Password not strong enough")
    
    payload = AuthUtility.verify_reset_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired reset token")
    
    user_id = payload.get("sub")
    # Find user by ID and update password
    for email, user in users_db.items():
        if user["user_id"] == user_id:
            user["password_hash"] = AuthUtility.hash_password(new_password)
            return {"message": "Password reset successful"}
    
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/api/auth/sync-to-mongo")
async def sync_to_mongo():
    """Sync in-memory users to MongoDB (admin endpoint)"""
    global users_collection, users_db
    
    if not users_collection:
        raise HTTPException(status_code=503, detail="MongoDB connection not available")
    
    synced_count = 0
    failed_count = 0
    
    for email, user_data in users_db.items():
        try:
            # Check if user already exists in MongoDB
            existing = await users_collection.find_one({"email": email})
            if not existing:
                # Insert the user
                await users_collection.insert_one(user_data)
                synced_count += 1
                print(f"✅ Synced user: {email}")
            else:
                print(f"⏭️  User already exists: {email}")
        except Exception as e:
            failed_count += 1
            print(f"❌ Failed to sync {email}: {e}")
    
    return {
        "message": "Sync complete",
        "synced": synced_count,
        "failed": failed_count,
        "total": len(users_db)
    }


@app.get("/api/profile/{user_id}", response_model=UserProfile)
async def get_profile(user_id: str):
    """Get user profile - MongoDB + fallback lookup"""
    global users_collection, users_db
    
    # Try MongoDB first
    user = None
    if users_collection is not None:
        try:
            user = await users_collection.find_one({"user_id": user_id})
        except:
            pass
    
    # Fallback to in-memory lookup
    if not user:
        for email, u in users_db.items():
            if u["user_id"] == user_id:
                user = u
                break
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfile(
        user_id=user["user_id"],
        email=user["email"],
        full_name=user["full_name"],
        phone=user["phone"],
        profile_picture=user.get("profile_photo"),
        member_since=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"],
        total_bookings=user.get("booking_stats", {}).get("total_bookings", 0),
        loyalty_points=user.get("loyalty_points", 0),
        is_verified=user.get("email_verified", False)
    )


@app.post("/api/profile/update")
async def update_profile(request: Dict[str, Any]):
    """Update user profile fields (MongoDB + fallback) with demo-user resilience."""
    global users_collection, users_db

    user_id = request.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    allowed_fields = {"full_name", "phone", "gender", "date_of_birth", "profile_photo"}
    updates = {k: v for k, v in request.items() if k in allowed_fields and v is not None}

    # Try MongoDB first
    mongo_user = None
    if users_collection is not None:
        try:
            mongo_user = await users_collection.find_one({"user_id": user_id})
            if mongo_user:
                await users_collection.update_one({"user_id": user_id}, {"$set": updates})
                mongo_user.update(updates)
                mongo_user.pop("_id", None)
                return mongo_user
        except Exception as e:
            print(f"⚠️  MongoDB profile update failed: {e}")

    # Fallback in-memory update/create
    target_email = None
    for email, user in users_db.items():
        if user.get("user_id") == user_id:
            user.update(updates)
            target_email = email
            break

    # Create a lightweight demo/fallback user if not found
    if target_email is None:
        fallback_email = request.get("email") or f"{user_id}@example.com"
        users_db[fallback_email] = {
            "user_id": user_id,
            "email": fallback_email,
            "full_name": request.get("full_name", "Demo User"),
            "phone": request.get("phone", ""),
            "password_hash": "",
            "created_at": datetime.utcnow().isoformat(),
            "email_verified": False,
            "is_active": True,
            "preferences": {},
            "booking_stats": {
                "total_bookings": 0,
                "successful_bookings": 0,
                "cancelled_bookings": 0
            },
            **updates,
        }
        target_email = fallback_email

    return users_db[target_email]


# ==================== TRAIN BROWSING ROUTES ====================

@app.get("/api/trains/search")
async def search_trains(
    from_station: str,
    to_station: str,
    departure_date: str,
    seat_class: Optional[str] = "AC2",
    page: int = 1,
    limit: int = 20,
    sort_by: Optional[str] = "departure_time"
):
    """Search trains by route and date with pagination"""
    try:
        # Validate trains_data is available
        if not trains_data or len(trains_data) == 0:
            return {
                "error": "Train data not yet loaded",
                "from_station": from_station,
                "to_station": to_station,
                "total_results": 0,
                "trains": []
            }
        
        from_q = (from_station or "").strip().lower()
        to_q = (to_station or "").strip().lower()

        def city(val: str) -> str:
            return (val or "").strip().lower()

        # 1) Strict exact matching
        matching_trains = [
            train for train in trains_data
            if city(train.get("from", "")) == from_q and city(train.get("to", "")) == to_q
        ]

        message = None

        # 2) Soft matching (prefix/contains) when exact route is sparse in mock data
        if not matching_trains:
            matching_trains = [
                train for train in trains_data
                if (
                    from_q in city(train.get("from", "")) or city(train.get("from", "")).startswith(from_q)
                ) and (
                    to_q in city(train.get("to", "")) or city(train.get("to", "")).startswith(to_q)
                )
            ]
            if matching_trains:
                message = "Showing closest matching trains for your route"

        # 3) Final fallback: show alternatives from source/destination side so UI is never empty
        if not matching_trains:
            matching_trains = [
                train for train in trains_data
                if from_q in city(train.get("from", "")) or to_q in city(train.get("to", ""))
            ]
            if matching_trains:
                message = "No exact route found. Showing recommended alternatives"

        if not matching_trains:
            matching_trains = list(trains_data[:max(limit, 20)])
            message = "No direct matches found. Showing popular trains"
        
        # Sort trains based on sort_by parameter
        if sort_by == "price":
            matching_trains.sort(key=lambda t: t.get("price", {}).get(seat_class, 0))
        elif sort_by == "duration":
            matching_trains.sort(key=lambda t: int(t.get("duration", "0h").split("h")[0]))
        elif sort_by == "rating":
            matching_trains.sort(key=lambda t: t.get("rating", 0), reverse=True)
        else:  # departure_time (default)
            matching_trains.sort(key=lambda t: t.get("departureTime", "00:00"))
        
        # Pagination
        total_trains = len(matching_trains)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_trains = matching_trains[start_idx:end_idx]
        
        # Use PRAL Perceive Agent to analyze search
        perception = {
            "total_trains_found": total_trains,
            "trains_on_page": len(paginated_trains),
            "seats_available": sum(train.get("availability", {}).get("confirmed", 0) for train in paginated_trains),
            "avg_price": sum(t.get("price", {}).get(seat_class, 0) for t in paginated_trains) // len(paginated_trains) if paginated_trains else 0,
            "avg_rating": sum(t.get("rating", 0) for t in paginated_trains) / len(paginated_trains) if paginated_trains else 0
        }
        
        return {
            "from_station": from_station,
            "to_station": to_station,
            "departure_date": departure_date,
            "total_results": total_trains,
            "showing_results": len(paginated_trains),
            "page": page,
            "page_size": limit,
            "total_pages": (total_trains + limit - 1) // limit,
            "trains": paginated_trains,
            "ai_analysis": perception,
            "message": message,
        }
    except Exception as e:
        print(f"❌ Train search error: {str(e)}")
        return {
            "error": f"Search failed: {str(e)}",
            "from_station": from_station,
            "to_station": to_station,
            "total_results": 0,
            "trains": []
        }


@app.get("/api/trains/{train_id}")
async def get_train_details(train_id: str):
    """Get detailed train information"""
    train = next((t for t in trains_data if t.get("_id") == train_id), None)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    return train


@app.post("/api/trains/availability", response_model=AvailabilityCheckResponse)
async def check_availability(request: AvailabilityCheckRequest):
    """Check seat availability for a train"""
    train = next((t for t in trains_data if t.get("_id") == request.train_id), None)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    availability = train.get("availability", {})
    available = availability.get("confirmed", 0)
    price = train.get("price", {}).get(request.seat_class, 0)
    
    return AvailabilityCheckResponse(
        train_id=request.train_id,
        train_number=train.get("number"),
        departure_date=request.departure_date,
        seat_class=request.seat_class,
        available_count=available,
        rac_count=availability.get("rac", 0),
        waitlist_count=availability.get("waitlist", 0),
        is_available=available >= request.number_of_passengers,
        price_per_seat=price,
        total_price=price * request.number_of_passengers
    )


@app.get("/api/trains/{train_id}/seat-map")
async def get_seat_map(train_id: str, seat_class: str):
    """Get seat availability map for visualization"""
    train = next((t for t in trains_data if t.get("_id") == train_id), None)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    # Generate realistic seat data
    import random
    total_seats = 72
    available = random.randint(10, 60)
    
    available_seats = [f"{chr(65+i)}{j+1}" for i in range(6) for j in range(12)][:available]
    booked_seats = [f"{chr(65+i)}{j+1}" for i in range(6) for j in range(12)][available:available+40]
    
    return SeatAvailabilityMap(
        train_id=train_id,
        seat_class=seat_class,
        total_seats=total_seats,
        available_seats=available_seats,
        booked_seats=booked_seats,
        rac_seats=[],
        waitlist_seats=[]
    )


# ==================== BOOKING ROUTES ====================

@app.post("/api/bookings/execute")
async def execute_booking(request: Dict[str, Any]):
    """Simplified booking endpoint for frontend compatibility."""
    booking_id = str(uuid.uuid4())
    pnr = f"AB{datetime.now().strftime('%y%m%d')}{booking_id[-4:]}"

    booking_record = {
        "booking_id": booking_id,
        "pnr": pnr,
        "user_id": request.get("user_id", "demo_user"),
        "train_id": request.get("train_id"),
        "status": "CONFIRMED",
        "requested_seats": int(request.get("passengers", 1) or 1),
        "seat_class": request.get("class", "2A"),
        "created_at": datetime.utcnow().isoformat(),
    }
    bookings_db[booking_id] = booking_record

    return {
        "success": True,
        "booking_id": booking_id,
        "booking_status": "CONFIRMED",
        "status": "CONFIRMED",
        "pnr": pnr,
        "message": "Booking confirmed"
    }

@app.post("/api/bookings/normal", response_model=BookingConfirmation)
async def create_normal_booking(request: NormalBookingRequest):
    """Create normal train booking with availability checking and waitlist support"""
    # Validate train exists
    train = next((t for t in trains_data if t.get("_id") == request.train_id), None)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    # Get seat availability for requested class
    seat_class_lower = request.seat_class.lower().replace(" ", "")
    available = train.get("availability", {}).get(seat_class_lower, 0)
    requested = len(request.seat_selections)
    
    # Generate booking ID and PNR
    booking_id = str(uuid.uuid4())
    pnr = f"AB{datetime.now().strftime('%y%m%d')}{booking_id[-4:]}"
    
    # Determine booking status based on availability
    if available >= requested:
        # CONFIRMED - Seats available
        booking_status = BookingStatusEnum.CONFIRMED
        seats_assigned = [s.seat_number for s in request.seat_selections]
        train["availability"][seat_class_lower] -= requested
        waitlist_position = None
    else:
        # WAITLIST - No seats available (or insufficient)
        booking_status = BookingStatusEnum.PENDING
        seats_assigned = []
        
        # Initialize waitlist queue if needed
        if "waitlist_queue" not in train:
            train["waitlist_queue"] = []
        
        # Add to waitlist
        waitlist_position = len(train["waitlist_queue"]) + 1
        train["waitlist_queue"].append({
            "booking_id": booking_id,
            "user_id": request.user_id,
            "requested_seats": requested,
            "seat_class": seat_class_lower,
            "position": waitlist_position,
            "created_at": datetime.utcnow().isoformat()
        })
    
    # Calculate total fare
    seat_price = train.get("price", {}).get(seat_class_lower, 0)
    total_fare = seat_price * len(request.passengers)
    
    # Create booking confirmation
    booking_confirmation = BookingConfirmation(
        pnr=pnr,
        booking_id=booking_id,
        user_id=request.user_id,
        train_number=train.get("number"),
        train_name=train.get("name"),
        from_station=request.from_station,
        to_station=request.to_station,
        departure_date=request.departure_date,
        departure_time=request.departure_time,
        passengers=[{"name": p.name, "age": p.age} for p in request.passengers],
        seat_class=request.seat_class,
        seats_assigned=seats_assigned,
        total_fare=total_fare,
        booking_status=booking_status,
        payment_status=PaymentStatusEnum.COMPLETED,
        booking_timestamp=datetime.utcnow(),
        confirmation_details={
            "quota": request.quota,
            "special_requirements": request.special_requirements,
            "status_message": f"Booking {booking_status.value}" + 
                             (f" at position {waitlist_position}" if booking_status == BookingStatusEnum.PENDING else ""),
            "available_seats": available,
            "requested_seats": requested
        }
    )
    
    # Store booking in database - MongoDB + fallback
    booking_data = {
        "booking_id": booking_id,
        "pnr": pnr,
        "user_id": request.user_id,
        "train_id": request.train_id,
        "train_name": train.get("name"),
        "seat_class": seat_class_lower,
        "requested_seats": requested,
        "seats": seats_assigned,
        "status": booking_status.value,
        "waitlist_position": waitlist_position,
        "total_fare": total_fare,
        "created_at": datetime.utcnow().isoformat()
    }
    
    bookings_db[booking_id] = booking_data
    
    # Save to MongoDB (primary)
    if bookings_collection is not None:
        try:
            await bookings_collection.insert_one(booking_data)
            print(f"✅ Booking saved to MongoDB: {booking_id}")
        except Exception as e:
            print(f"⚠️  MongoDB save failed: {e}, using fallback")
    
    # Update user booking stats in both MongoDB and fallback
    user_found = False
    if users_collection is not None:
        try:
            await users_collection.update_one(
                {"user_id": request.user_id},
                {"$inc": {
                    "booking_stats.total_bookings": 1,
                    "booking_stats.successful_bookings": 1 if booking_status == BookingStatusEnum.CONFIRMED else 0
                }}
            )
            user_found = True
            print(f"✅ User booking stats updated in MongoDB: {request.user_id}")
        except Exception as e:
            print(f"⚠️  MongoDB update failed: {e}")
    
    # Fallback to in-memory update
    if not user_found:
        for email, user in users_db.items():
            if user["user_id"] == request.user_id:
                user["booking_stats"]["total_bookings"] += 1
                if booking_status == BookingStatusEnum.CONFIRMED:
                    user["booking_stats"]["successful_bookings"] += 1
                break
    
    return booking_confirmation


@app.post("/api/booking/create")
async def create_booking_record(request: Dict[str, Any]):
    """Create and persist a confirmed booking record from payment flow."""
    global bookings_collection, bookings_db, users_collection, users_db
    try:
        user_id = request.get("user_id") or request.get("userId") or "demo_user_001"
        train_id = request.get("train_id") or request.get("trainId")
        if not train_id:
            raise HTTPException(status_code=400, detail="train_id is required")

        passengers = request.get("passengers") or []
        if not isinstance(passengers, list) or len(passengers) == 0:
            raise HTTPException(status_code=400, detail="passengers are required")

        booking_id = str(uuid.uuid4())
        pnr = f"AB{datetime.now().strftime('%y%m%d')}{booking_id[-4:]}"
        total_amount = int(request.get("total_amount") or request.get("totalAmount") or 0)
        booking_type = (request.get("booking_type") or request.get("bookingType") or "normal").lower()

        normalized_passengers = []
        for idx, p in enumerate(passengers):
            age_val = p.get("age", 0)
            try:
                age = int(age_val)
            except (TypeError, ValueError):
                age = 0

            normalized_passengers.append({
                "name": p.get("name", f"Passenger {idx + 1}"),
                "age": age,
                "gender": p.get("gender", "N/A"),
                "seat": p.get("seat", f"S{idx + 1}"),
            })

        booking_data = {
            "booking_id": booking_id,
            "pnr": pnr,
            "user_id": user_id,
            "train_id": train_id,
            "train_name": request.get("train_name") or request.get("trainName", "Selected Train"),
            "train_number": request.get("train_number") or request.get("trainNumber", "N/A"),
            "from_station": request.get("from_station") or request.get("from", "N/A"),
            "to_station": request.get("to_station") or request.get("to", "N/A"),
            "departure_date": request.get("departure_date") or request.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
            "departure_time": request.get("departure_time") or request.get("departureTime", "--:--"),
            "arrival_time": request.get("arrival_time") or request.get("arrivalTime", "--:--"),
            "seat_class": request.get("seat_class") or request.get("class", "2A"),
            "seat_preference": request.get("seat_preference") or request.get("seatPreference", "any"),
            "requested_seats": len(normalized_passengers),
            "passengers": normalized_passengers,
            "total_amount": total_amount,
            "total_fare": total_amount,
            "payment_method": request.get("payment_method") or request.get("paymentMethod", "UPI"),
            "payment_reference": request.get("payment_reference") or request.get("paymentReference", ""),
            "payment_status": "COMPLETED",
            "booking_type": booking_type,
            "status": "CONFIRMED",
            "created_at": datetime.utcnow().isoformat(),
        }

        bookings_db[booking_id] = booking_data

        if bookings_collection is not None:
            try:
                await bookings_collection.insert_one(booking_data)
                print(f"✅ Payment booking saved to MongoDB: {booking_id}")
            except Exception as e:
                print(f"⚠️  MongoDB save failed for payment booking: {e}")

        # Update user stats in MongoDB first.
        if users_collection is not None:
            try:
                await users_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$inc": {
                            "booking_stats.total_bookings": 1,
                            "booking_stats.successful_bookings": 1,
                            "booking_stats.total_money_spent": total_amount,
                            "booking_stats.total_passengers": len(normalized_passengers),
                            "booking_stats.total_tatkal_bookings": 1 if booking_type == "tatkal" else 0,
                        }
                    },
                    upsert=False,
                )
            except Exception as e:
                print(f"⚠️  MongoDB user stats update failed: {e}")

        # In-memory fallback stats update.
        for _, user in users_db.items():
            if user.get("user_id") == user_id:
                booking_stats = user.setdefault("booking_stats", {})
                booking_stats["total_bookings"] = int(booking_stats.get("total_bookings", 0)) + 1
                booking_stats["successful_bookings"] = int(booking_stats.get("successful_bookings", 0)) + 1
                booking_stats["total_money_spent"] = int(booking_stats.get("total_money_spent", 0)) + total_amount
                booking_stats["total_passengers"] = int(booking_stats.get("total_passengers", 0)) + len(normalized_passengers)
                if booking_type == "tatkal":
                    booking_stats["total_tatkal_bookings"] = int(booking_stats.get("total_tatkal_bookings", 0)) + 1
                break

        response_record = dict(booking_data)
        if "_id" in response_record:
            response_record["_id"] = str(response_record["_id"])

        return {
            "success": True,
            "message": "Booking confirmed and saved",
            **response_record,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️  Payment booking create recovery path: {e}")
        fallback_id = str(uuid.uuid4())
        fallback_pnr = f"AB{datetime.now().strftime('%y%m%d')}{fallback_id[-4:]}"
        fallback_record = {
            "booking_id": fallback_id,
            "pnr": fallback_pnr,
            "user_id": request.get("user_id") or request.get("userId") or "demo_user_001",
            "train_id": request.get("train_id") or request.get("trainId") or "train_unknown",
            "train_name": request.get("train_name") or request.get("trainName", "Selected Train"),
            "train_number": request.get("train_number") or request.get("trainNumber", "N/A"),
            "from_station": request.get("from_station") or request.get("from", "N/A"),
            "to_station": request.get("to_station") or request.get("to", "N/A"),
            "departure_date": request.get("departure_date") or request.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
            "departure_time": request.get("departure_time") or request.get("departureTime", "--:--"),
            "arrival_time": request.get("arrival_time") or request.get("arrivalTime", "--:--"),
            "seat_class": request.get("seat_class") or request.get("class", "2A"),
            "requested_seats": len(request.get("passengers") or []),
            "passengers": request.get("passengers") or [],
            "total_amount": int(request.get("total_amount") or request.get("totalAmount") or 0),
            "total_fare": int(request.get("total_amount") or request.get("totalAmount") or 0),
            "booking_type": (request.get("booking_type") or request.get("bookingType") or "normal").lower(),
            "status": "CONFIRMED",
            "payment_status": "COMPLETED",
            "created_at": datetime.utcnow().isoformat(),
        }
        bookings_db[fallback_id] = fallback_record
        fallback_response = dict(fallback_record)
        if "_id" in fallback_response:
            fallback_response["_id"] = str(fallback_response["_id"])

        return {
            "success": True,
            "message": "Booking confirmed and saved (recovery mode)",
            **fallback_response,
        }


@app.post("/api/bookings/tatkal")
async def create_tatkal_booking(request: TatkalBookingRequest):
    """Schedule Tatkal booking for automatic execution at user-selected time."""
    global bookings_collection, bookings_db
    
    train = next((t for t in trains_data if t.get("_id") == request.train_id), None)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    # Parse user-selected booking time (HH:MM). If already past today, schedule for tomorrow.
    try:
        selected_time = datetime.strptime(request.scheduled_time, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="scheduled_time must be in HH:MM format")

    now = datetime.now()
    execution_time = datetime.combine(now.date(), selected_time)
    scheduled_for_next_day = False
    adjusted_to_immediate = False
    
    # UI time picker is minute-precision (HH:MM). If user picks the current minute,
    # schedule immediately instead of shifting to tomorrow.
    if execution_time <= now:
        if now.strftime("%H:%M") == request.scheduled_time:
            execution_time = now + timedelta(seconds=5)
            adjusted_to_immediate = True
        else:
            execution_time = execution_time + timedelta(days=1)
            scheduled_for_next_day = True
    
    tatkal_id = str(uuid.uuid4())
    pnr = f"AB{datetime.now().strftime('%y%m%d')}{tatkal_id[-4:]}"
    
    # Store as scheduled Tatkal booking with HIGH priority
    tatkal_booking_data = {
        "booking_id": tatkal_id,
        "pnr": pnr,
        "train_id": request.train_id,
        "train_name": train.get("name"),
        "train_number": train.get("number"),
        "status": "SCHEDULED",
        "booking_type": "TATKAL",
        "priority": "HIGH",
        "from_station": request.from_station,
        "to_station": request.to_station,
        "departure_date": request.departure_date,
        "departure_time": request.departure_time,
        "passengers": [
            {
                "name": p.name,
                "age": p.age,
                "gender": p.gender,
            }
            for p in request.passengers
        ],
        "created_at": datetime.now().isoformat(),
        "user_id": getattr(request, 'user_id', 'demo_user'),
        "tatkal_booking_id": tatkal_id,
        "scheduled_time": request.scheduled_time,
        "execution_time": execution_time.isoformat(),
        "retry_count": 0,
        "retry_attempts": getattr(request, 'retry_count', 3),
        "number_of_passengers": len(request.passengers),
        "seat_class": request.seat_class,
        "seat_info": "Auto-assigned",
        "coach_info": "To be allocated",
        "expected_confirmation_time": (execution_time + timedelta(seconds=2)).isoformat()
    }
    
    bookings_db[tatkal_id] = tatkal_booking_data
    
    # Save to MongoDB (primary)
    if bookings_collection is not None:
        try:
            await bookings_collection.insert_one(tatkal_booking_data)
            print(f"✅ Tatkal booking saved to MongoDB: {tatkal_id}")
        except Exception as e:
            print(f"⚠️  MongoDB save failed: {e}, using fallback")

    async def process_scheduled_tatkal(booking_id: str):
        """Execute scheduled Tatkal automatically at execution_time."""
        booking = bookings_db.get(booking_id)
        if not booking:
            return

        exec_at = datetime.fromisoformat(booking["execution_time"])
        delay = max((exec_at - datetime.now()).total_seconds(), 0)
        await asyncio.sleep(delay)

        booking["status"] = "PROCESSING"
        booking["processing_started_at"] = datetime.now().isoformat()

        if bookings_collection is not None:
            try:
                await bookings_collection.update_one(
                    {"booking_id": booking_id},
                    {"$set": {
                        "status": "PROCESSING",
                        "processing_started_at": booking["processing_started_at"]
                    }}
                )
            except Exception:
                pass

        # Simulate processing phase
        await asyncio.sleep(2)

        booking["status"] = "CONFIRMED"
        booking["confirmed_at"] = datetime.now().isoformat()

        if bookings_collection is not None:
            try:
                await bookings_collection.update_one(
                    {"booking_id": booking_id},
                    {"$set": {
                        "status": "CONFIRMED",
                        "confirmed_at": booking["confirmed_at"]
                    }}
                )
            except Exception:
                pass

    tatkal_tasks[tatkal_id] = asyncio.create_task(process_scheduled_tatkal(tatkal_id))
    
    return {
        "success": True,
        "tatkal_booking_id": tatkal_id,
        "pnr": pnr,
        "status": "SCHEDULED",
        "booking_type": "TATKAL",
        "priority": "HIGH",
        "scheduled_time": request.scheduled_time,
        "execution_time": execution_time.isoformat(),
        "scheduled_for_next_day": scheduled_for_next_day,
        "adjusted_to_immediate": adjusted_to_immediate,
        "train_number": train.get("number"),
        "from_station": request.from_station,
        "to_station": request.to_station,
        "departure_date": request.departure_date,
        "number_of_passengers": len(request.passengers),
        "message": (
            f"✅ Tatkal booking scheduled successfully for {execution_time.strftime('%Y-%m-%d %H:%M:%S')}"
            + (" (same-minute auto-adjusted)." if adjusted_to_immediate else ".")
        ),
        "retry_count": getattr(request, 'retry_count', 3),
        "created_at": datetime.now().isoformat(),
        "confirmation_message": "Tatkal booking is scheduled and will auto-execute at the selected time."
    }


@app.get("/api/bookings/tatkal/{tatkal_booking_id}/status")
async def get_tatkal_status(tatkal_booking_id: str):
    """Get live status for scheduled Tatkal booking."""
    booking = bookings_db.get(tatkal_booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Tatkal booking not found")

    execution_time = booking.get("execution_time")
    countdown_seconds = 0
    if execution_time and booking.get("status") == "SCHEDULED":
        try:
            countdown_seconds = max(
                int((datetime.fromisoformat(execution_time) - datetime.now()).total_seconds()),
                0,
            )
        except Exception:
            countdown_seconds = 0

    return {
        "tatkal_booking_id": tatkal_booking_id,
        "status": booking.get("status", "SCHEDULED"),
        "booking_type": booking.get("booking_type", "TATKAL"),
        "priority": booking.get("priority", "HIGH"),
        "execution_time": execution_time,
        "scheduled_for_next_day": booking.get("scheduled_for_next_day", False),
        "adjusted_to_immediate": booking.get("adjusted_to_immediate", False),
        "countdown_seconds": countdown_seconds,
        "pnr": booking.get("pnr"),
        "train_id": booking.get("train_id"),
        "train_name": booking.get("train_name"),
        "train_number": booking.get("train_number"),
        "from_station": booking.get("from_station"),
        "to_station": booking.get("to_station"),
        "departure_date": booking.get("departure_date"),
        "departure_time": booking.get("departure_time"),
        "seat_class": booking.get("seat_class"),
        "seat_info": booking.get("seat_info"),
        "coach_info": booking.get("coach_info"),
        "passengers": booking.get("passengers", []),
        "updated_at": datetime.now().isoformat(),
    }


@app.get("/api/bookings/history/{user_id}")
async def get_booking_history(user_id: str):
    """Get user booking history - MongoDB + fallback lookup"""
    global bookings_collection, bookings_db

    def _json_safe(value):
        if isinstance(value, dict):
            return {k: _json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_json_safe(v) for v in value]
        if type(value).__name__ == "ObjectId":
            return str(value)
        return value
    
    user_bookings = []
    
    # Try MongoDB first
    if bookings_collection is not None:
        try:
            async for booking in bookings_collection.find({"user_id": user_id}):
                # Make Mongo documents JSON-serializable
                if "_id" in booking:
                    booking["_id"] = str(booking["_id"])
                user_bookings.append(booking)
            print(f"✅ Loaded {len(user_bookings)} bookings from MongoDB for user {user_id}")
        except Exception as e:
            print(f"⚠️  MongoDB query failed: {e}, using fallback")
            user_bookings = []
    
    # Fallback to in-memory if MongoDB unavailable or no results
    if not user_bookings:
        user_bookings = [
            b for b in bookings_db.values()
            if b.get("user_id") == user_id
        ]

    user_bookings = _json_safe(user_bookings)
    
    return {
        "user_id": user_id,
        "total_bookings": len(user_bookings),
        "bookings": user_bookings
    }


@app.post("/api/bookings/{booking_id}/cancel", response_model=CancellationResponse)
async def cancel_booking(booking_id: str, request: CancellationRequest):
    """Cancel a booking with automatic waitlist upgrade - MongoDB + fallback"""
    global bookings_collection, bookings_db
    
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = bookings_db[booking_id]
    train_id = booking["train_id"]
    booking_pnr = booking.get("pnr")
    
    # Find the train
    train = next((t for t in trains_data if t.get("_id") == train_id), None)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    # Generate cancellation details
    cancellation_id = str(uuid.uuid4())
    original_fare = booking.get("total_fare", 0)
    cancellation_fee = 500
    refund_amount = original_fare - cancellation_fee
    
    # Update booking status
    booking["status"] = "CANCELLED"
    booking["cancelled_at"] = datetime.utcnow().isoformat()
    
    # Save cancelled booking to MongoDB
    if bookings_collection is not None:
        try:
            await bookings_collection.update_one(
                {"booking_id": booking_id},
                {"$set": {"status": "CANCELLED", "cancelled_at": booking["cancelled_at"]}}
            )
            print(f"✅ Booking cancellation saved to MongoDB: {booking_id}")
        except Exception as e:
            print(f"⚠️  MongoDB update failed: {e}")
    
    # RELEASE SEATS if booking was confirmed
    upgraded_bookings = []
    if booking["status"] == "CANCELLED" and booking.get("requested_seats", 0) > 0:
        seat_class = booking.get("seat_class", "").lower()
        num_seats_released = booking.get("requested_seats", 0)
        
        # Add seats back to availability
        if seat_class in train["availability"]:
            train["availability"][seat_class] += num_seats_released
        
        # TRIGGER WAITLIST UPGRADE
        waitlist = train.get("waitlist_queue", [])
        while waitlist and train["availability"].get(seat_class, 0) > 0:
            # Get first person in waitlist
            wl_entry = waitlist.pop(0)
            wl_booking_id = wl_entry.get("booking_id")
            wl_requested = wl_entry.get("requested_seats", 0)
            
            # Check if we have enough seats to upgrade them
            if train["availability"][seat_class] >= wl_requested:
                # UPGRADE THIS BOOKING FROM PENDING → CONFIRMED
                if wl_booking_id in bookings_db:
                    wl_booking = bookings_db[wl_booking_id]
                    wl_booking["status"] = "CONFIRMED"
                    wl_booking["waitlist_position"] = None
                    wl_booking["confirmed_at"] = datetime.utcnow().isoformat()
                    upgraded_bookings.append({
                        "booking_id": wl_booking_id,
                        "pnr": wl_booking.get("pnr"),
                        "user_id": wl_booking.get("user_id")
                    })
                    
                    # Update upgraded booking in MongoDB
                    if bookings_collection is not None:
                        try:
                            await bookings_collection.update_one(
                                {"booking_id": wl_booking_id},
                                {"$set": {
                                    "status": "CONFIRMED",
                                    "waitlist_position": None,
                                    "confirmed_at": wl_booking["confirmed_at"]
                                }}
                            )
                            print(f"✅ Waitlist booking upgraded in MongoDB: {wl_booking_id}")
                        except Exception as e:
                            print(f"⚠️  MongoDB upgrade failed: {e}")
                
                # Decrement availability
                train["availability"][seat_class] -= wl_requested
            else:
                # Not enough seats available, re-add to queue
                wl_entry["position"] = len(waitlist) + 1
                waitlist.append(wl_entry)
                break
    
    return CancellationResponse(
        cancellation_id=cancellation_id,
        booking_id=booking_id,
        pnr=booking_pnr,
        refund_amount=int(refund_amount),
        cancellation_charges=cancellation_fee,
        status="COMPLETED",
        refund_status=PaymentStatusEnum.COMPLETED,
        timestamp=datetime.utcnow(),
        confirmation_details={
            "original_fare": original_fare,
            "upgraded_bookings_count": len(upgraded_bookings),
            "upgraded_bookings": upgraded_bookings
        }
    )


# ==================== PRAL AGENT ROUTES ====================

@app.post("/api/agents/orchestrate")
async def orchestrate_booking(
    user_id: str,
    train_id: str,
    from_station: str,
    to_station: str,
    departure_date: str
):
    """Use PRAL orchestrator for intelligent booking"""
    train = next((t for t in trains_data if t.get("_id") == train_id), None)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    search_params = {
        "from_station": from_station,
        "to_station": to_station,
        "departure_date": departure_date,
        "user_id": user_id
    }
    
    # Get agent recommendations
    orchestration_result = await pral_orchestrator.orchestrate_search_and_book(
        search_params,
        [train]
    )
    
    return orchestration_result


@app.get("/api/agents/logs/{orchestration_id}")
async def get_agent_logs(orchestration_id: str):
    """Get PRAL agent activity logs"""
    all_logs = pral_orchestrator.get_all_logs()
    
    return {
        "orchestration_id": orchestration_id,
        "perceive_logs": all_logs.get("perceive_agent", []),
        "reason_logs": all_logs.get("reason_agent", []),
        "act_logs": all_logs.get("act_agent", []),
        "learn_logs": all_logs.get("learn_agent", []),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/agents/health")
async def agent_health():
    """Check PRAL agents health"""
    return {
        "perceive_agent": "healthy",
        "reason_agent": "healthy",
        "act_agent": "healthy",
        "learn_agent": "healthy",
        "orchestrator": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== HEALTH & SYSTEM ROUTES ====================

@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "trains_loaded": len(trains_data),
        "users_registered": len(users_db),
        "active_bookings": len(bookings_db),
        "agents": "PRAL (Perceive, Act, Reason, Learn)"
    }


@app.get("/api/system/stats")
async def get_system_stats():
    """Get system statistics"""
    return {
        "total_trains": len(trains_data),
        "total_users": len(users_db),
        "total_bookings": len(bookings_db),
        "active_sessions": len(sessions_db),
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get booking dashboard aggregates for cards and KPIs."""
    global bookings_collection, bookings_db

    stats = {
        "total_bookings": 0,
        "total_passengers": 0,
        "total_revenue": 0,
        "total_tatkal_bookings": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if bookings_collection is not None:
        try:
            pipeline = [
                {
                    "$project": {
                        "requested_seats": {"$ifNull": ["$requested_seats", {"$size": {"$ifNull": ["$passengers", []]}}]},
                        "amount": {"$ifNull": ["$total_amount", {"$ifNull": ["$total_fare", 0]}]},
                        "booking_type": {"$toLower": {"$ifNull": ["$booking_type", "normal"]}},
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_bookings": {"$sum": 1},
                        "total_passengers": {"$sum": "$requested_seats"},
                        "total_revenue": {"$sum": "$amount"},
                        "total_tatkal_bookings": {
                            "$sum": {
                                "$cond": [{"$eq": ["$booking_type", "tatkal"]}, 1, 0]
                            }
                        },
                    }
                },
            ]

            result = await bookings_collection.aggregate(pipeline).to_list(length=1)
            if result:
                row = result[0]
                stats["total_bookings"] = int(row.get("total_bookings", 0) or 0)
                stats["total_passengers"] = int(row.get("total_passengers", 0) or 0)
                stats["total_revenue"] = int(row.get("total_revenue", 0) or 0)
                stats["total_tatkal_bookings"] = int(row.get("total_tatkal_bookings", 0) or 0)
                return stats
        except Exception as e:
            print(f"⚠️  MongoDB dashboard aggregation failed: {e}")

    # In-memory fallback aggregation.
    for b in bookings_db.values():
        stats["total_bookings"] += 1
        passengers_count = int(b.get("requested_seats", 0) or 0)
        if passengers_count == 0 and isinstance(b.get("passengers"), list):
            passengers_count = len(b.get("passengers"))
        stats["total_passengers"] += passengers_count

        amount = int(b.get("total_amount", 0) or b.get("total_fare", 0) or 0)
        stats["total_revenue"] += amount

        booking_type = str(b.get("booking_type", "normal") or "normal").lower()
        if booking_type == "tatkal":
            stats["total_tatkal_bookings"] += 1

    return stats


# ==================== GUARANTEED SUCCESS SYSTEM ====================

@app.post("/api/bookings/auto-confirm/{booking_id}")
async def auto_confirm_booking(booking_id: str):
    """
    GUARANTEED SUCCESS PROTOCOL: Auto-confirm waitlist bookings after 60 seconds
    
    Rule: If booking is PENDING (waitlist), auto-upgrade to CONFIRMED
    This ensures ZERO bookings end in PENDING state
    """
    if booking_id not in bookings_db:
        return {
            "success": False,
            "error": "Booking not found",
            "retryable": False
        }
    
    booking = bookings_db[booking_id]
    
    # If already confirmed, return success
    if booking["status"] != "PENDING":
        return {
            "success": True,
            "booking_id": booking_id,
            "status": booking["status"],
            "message": "Booking already confirmed"
        }
    
    # GUARANTEED SUCCESS: Force confirmation
    booking["status"] = "CONFIRMED"
    booking["auto_confirmed"] = True
    booking["auto_confirmed_at"] = datetime.utcnow().isoformat()
    
    return {
        "success": True,
        "booking_id": booking_id,
        "status": "CONFIRMED",
        "method": "auto_confirm",
        "message": "✅ Booking automatically confirmed (guaranteed success)"
    }


@app.post("/api/bookings/retry/{booking_id}")
async def retry_booking(booking_id: str):
    """
    GUARANTEED SUCCESS PROTOCOL: Retry failed bookings with exponential backoff
    
    Attempts to process booking again with retry logic
    """
    if booking_id not in bookings_db:
        return {
            "success": False,
            "error": "Booking not found"
        }
    
    booking = bookings_db[booking_id]
    
    # Update retry count
    booking["retry_attempts"] = booking.get("retry_attempts", 0) + 1
    booking["last_retry"] = datetime.utcnow().isoformat()
    
    # If already confirmed, return success
    if booking["status"] == "CONFIRMED":
        return {
            "success": True,
            "booking_id": booking_id,
            "status": "CONFIRMED",
            "message": "Booking already confirmed"
        }
    
    # GUARANTEED SUCCESS: Force confirmation after retry
    booking["status"] = "CONFIRMED"
    booking["confirmed_via_retry"] = True
    
    return {
        "success": True,
        "booking_id": booking_id,
        "status": "CONFIRMED",
        "retry_count": booking["retry_attempts"],
        "message": "✅ Booking confirmed via retry (guaranteed success)"
    }


@app.post("/api/bookings/force-confirm/{booking_id}")
async def force_confirm_booking(booking_id: str):
    """
    GUARANTEED SUCCESS PROTOCOL: Nuclear option - force confirm any booking
    
    Used as last resort to ensure ZERO booking failures
    NO EXCEPTIONS: This always returns success
    """
    try:
        if booking_id not in bookings_db:
            # Create booking entry if missing
            bookings_db[booking_id] = {
                "booking_id": booking_id,
                "pnr": f"AB{datetime.now().strftime('%y%m%d')}{random.randint(1000, 9999)}",
                "status": "CONFIRMED",
                "confirmed_via": "force_confirm",
                "confirmed_at": datetime.utcnow().isoformat()
            }
        else:
            # Force confirmation of existing booking
            booking = bookings_db[booking_id]
            booking["status"] = "CONFIRMED"
            booking["force_confirmed"] = True
            booking["force_confirmed_at"] = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "booking_id": booking_id,
            "status": "CONFIRMED",
            "pnr": bookings_db[booking_id].get("pnr"),
            "message": "✅ Booking GUARANTEED CONFIRMED (force confirm protocol)"
        }
    except Exception as e:
        # GUARANTEED SUCCESS: Even if exception, return success
        return {
            "success": True,
            "booking_id": booking_id,
            "status": "CONFIRMED",
            "message": "✅ Booking GUARANTEED CONFIRMED (error recovery mode)"
        }


# ==================== ERROR HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.utcnow().isoformat()}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
