# CRITICAL BUGS - QUICK FIX CHECKLIST

## 🔴 CRITICAL: Must Fix IMMEDIATELY (Blocks Everything)

### Bug #1: Frontend Using Wrong API Port (8001 instead of 8000)
**Status:** WILL BREAK ALL API CALLS
**Files to Fix:**
- `frontend/src/app/page.tsx` - Line 60
- `frontend/src/app/login/page.tsx` - Line 22  
- `frontend/src/app/register/page.tsx` - Line 68
- `frontend/src/app/schedule/page.tsx` - Line 53
- `frontend/src/app/booking/tatkal/page.tsx` - Line 46

**Fix:** Replace all instances of `http://localhost:8001/api/` with `http://localhost:8000/api/`

```diff
- const response = await fetch("http://localhost:8001/api/auth/login", {
+ const response = await fetch("http://localhost:8000/api/auth/login", {
```

---

### Bug #2: Missing Import in Backend Agents
**Status:** WILL CRASH WHEN PERCEIVE AGENT RUNS
**File:** `backend/pral_agents.py` - Line 1 (top of file)

**Fix:** Add missing import
```python
# Add at top of file
import random
```

---

### Bug #3: Missing JSON Response Error Handling
**Status:** Frontend can't distinguish API errors from success
**File:** `backend/main_api.py` - Line 510

**Fix:** Change this function:
```python
# BEFORE (Wrong - returns 200 with error field)
@app.get("/api/trains/search")
async def search_trains(...):
    if not trains_data or len(trains_data) == 0:
        return {
            "error": "Train data not yet loaded",
            "trains": []
        }

# AFTER (Correct - raises proper exception)
@app.get("/api/trains/search")
async def search_trains(...):
    if not trains_data or len(trains_data) == 0:
        raise HTTPException(
            status_code=503, 
            detail="Train data not yet loaded"
        )
```

---

### Bug #4: Missing Null Checks on Frontend
**Status:** WILL CRASH DASHBOARD ON LOAD
**File:** `frontend/src/app/page.tsx` - Lines 100-157

**Fix:** Add proper null boundary check
```javascript
// BEFORE (Unsafe)
if (loading) {
    return <LoadingUI />;
}
<h1>{user?.full_name}!</h1>  // user could still be null!

// AFTER (Safe)
if (loading) {
    return <LoadingUI />;
}
if (!user || !stats) {
    return <div>Loading failed. Please refresh.</div>;
}
<h1>{user.full_name}!</h1>  // Guaranteed to exist
```

---

### Bug #5: Missing Environment Variable
**Status:** Will silently fail to connect to database
**Files:** 
- `frontend/.env.local` (Create if doesn't exist)
- `backend/.env` (Update if needed)

**Fix:** Add these lines
```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

# backend/.env
MONGODB_URL=mongodb+srv://your_user:your_pass@your_cluster.mongodb.net/tatkal_booking
JWT_SECRET=your_secret_key_change_in_production
```

---

### Bug #6: Uninitialized Variables in Payment Booking
**Status:** Missing payment redirect URL
**File:** `backend/main_api.py` - Line 815-860

**Fix:** Add payment URL to response
```python
# Add before return statement
payment_info = {
    "booking_id": booking_id,
    "pnr": pnr,
    "amount": total_amount,
    "redirect_url": f"/payment/{booking_id}",  # Add this
    "confirmation_url": f"/confirmation/{booking_id}",  # Add this
}

return {
    "success": True,
    "message": "Booking confirmed and saved",
    "redirect_url": f"/payment/{booking_id}",  # Add this line
    "confirmation_url": f"/confirmation/{booking_id}",  # Add this line
    **booking_record,
}
```

---

### Bug #7: Tatkal Booking Silent Failure
**Status:** Booking scheduled but frontend doesn't know when it's done
**File:** `backend/main_api.py` - Line 1065-1100

**Fix:** Add WebSocket or polling endpoint
```python
@app.get("/api/bookings/tatkal/{booking_id}/poll")
async def poll_tatkal_status(booking_id: str, poll_count: int = 0):
    """Poll endpoint for Tatkal booking status updates"""
    booking = bookings_db.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Not found")
    
    status = booking.get("status", "SCHEDULED")
    return {
        "booking_id": booking_id,
        "status": status,
        "pnr": booking.get("pnr"),
        "message": f"Status: {status}",
        "should_poll_again": status in ["SCHEDULED", "PROCESSING"]
    }
```

And update frontend to poll:
```javascript
// frontend/src/app/booking/tatkal/page.tsx
const pollStatus = async () => {
    const response = await fetch(
        `http://localhost:8000/api/bookings/tatkal/${tatkalId}/poll`
    );
    const data = await response.json();
    
    if (data.status === "CONFIRMED") {
        showSuccess("Booking confirmed!");
        // Redirect to confirmation page
    } else if (data.should_poll_again) {
        setTimeout(pollStatus, 2000);  // Poll every 2 seconds
    }
};

useEffect(() => {
    if (isScheduled) {
        pollStatus();
    }
}, [isScheduled]);
```

---

### Bug #8: Missing Random Module Import
**Status:** Agent will crash at runtime
**File:** `backend/pral_agents.py` - Line 1

**Fix:**
```python
# Add at top
import random
from datetime import datetime
from typing import List, Dict, Any
import asyncio
import json
```

---

### Bug #9: Silent MongoDB Failure
**Status:** No error if MongoDB is down, data lost
**File:** `backend/main_api.py` - Line 100

**Fix:** Validate MongoDB at startup
```python
@app.on_event("startup")
async def startup_event():
    global users_collection, bookings_collection, sessions_collection
    
    print("\n" + "="*60)
    print("🚀 STARTING TATKAL BOOKING SYSTEM")
    print("="*60)
    
    # Connect to MongoDB WITH VALIDATION
    print("\n📡 Connecting to MongoDB Atlas...")
    await MongoDBClient.connect_db()
    
    # CRITICAL: Verify collections exist
    try:
        users_collection = MongoDBClient.get_collection("users")
        bookings_collection = MongoDBClient.get_collection("bookings")
        sessions_collection = MongoDBClient.get_collection("sessions")
        
        # Test write capability
        await users_collection.find_one({})  # Test query
        
        print("✅ MongoDB collections initialized:")
        print("   • users")
        print("   • bookings")  
        print("   • sessions")
    except Exception as e:
        print(f"❌ CRITICAL: MongoDB initialization failed: {e}")
        print("   System will run in DEMO MODE ONLY - NO DATA PERSISTENCE")
        print("   Please fix your MONGODB_URL in .env file")
        # Don't silently continue - at least warn
        # raise RuntimeError("MongoDB initialization failed") # Optional
```

---

## 🟠 HIGH PRIORITY: Fix Next

### Bug #10: Missing Passenger Validation
```python
# In backend/main_api.py create_booking_record()
def validate_passengers(passengers):
    """Validate each passenger has required fields"""
    if not isinstance(passengers, list) or len(passengers) == 0:
        raise HTTPException(status_code=400, detail="At least 1 passenger required")
    
    for idx, p in enumerate(passengers):
        if not p.get("name") or not p.get("name").strip():
            raise HTTPException(
                status_code=400, 
                detail=f"Passenger {idx+1}: name is required"
            )
        try:
            age = int(p.get("age", 0))
            if age < 1 or age > 120:
                raise ValueError("Invalid age")
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail=f"Passenger {idx+1}: age must be 1-120"
            )

# Then use in route
passengers = request.get("passengers", [])
validate_passengers(passengers)
```

---

### Bug #11: Missing Refund Logic
```python
# In backend/main_api.py cancel_booking()
def calculate_refund_amount(booking: Dict, days_before_departure: int) -> tuple[float, float]:
    """Calculate refund and charges based on cancellation policy"""
    total_fare = booking.get("total_fare", 0)
    
    if days_before_departure >= 30:
        refund = total_fare  # Full refund
        charges = 0
    elif days_before_departure >= 7:
        refund = total_fare * 0.75  # 75% refund
        charges = total_fare * 0.25
    elif days_before_departure >= 1:
        refund = total_fare * 0.50  # 50% refund
        charges = total_fare * 0.50
    else:
        refund = 0  # No refund if within 24 hours
        charges = total_fare
    
    return refund, charges

# Use in cancellation endpoint
from datetime import datetime
departure_date = datetime.strptime(booking["departure_date"], "%Y-%m-%d")
days_left = (departure_date - datetime.now()).days
refund_amount, cancellation_charges = calculate_refund_amount(booking, days_left)
```

---

### Bug #12: Missing CORS for Correct Port
```python
# In backend/config.py update ALLOWED_ORIGINS
ALLOWED_ORIGINS = [
    "http://localhost:3000",       # ✅ Primary frontend
    "http://localhost:3001",       # ✅ Next.js dev server
    "http://127.0.0.1:3000",       # ✅ Alternative localhost
    "http://localhost:8000",       # ✅ Self-reference for same-origin debugging
    # Remove: "http://localhost:8001" (wrong port!)
]
```

---

## Timeline for Fixes

**STOP AND FIX IN THIS ORDER:**
1. ⏰ Bug #1 (Port mismatch) - 2 minutes
2. ⏰ Bug #2 (Missing import) - 1 minute  
3. ⏰ Bug #3 (Error handling) - 5 minutes
4. ⏰ Bug #4 (Null checks) - 5 minutes
5. ⏰ Bug #5 (Env variables) - 3 minutes
---

**Total Time to Fix CRITICAL Issues: ~16 minutes**

Then test:
```bash
# Terminal 1
cd backend && python main_api.py

# Terminal 2  
cd frontend && npm run dev

# Terminal 3
# Visit http://localhost:3000 and try logging in, searching trains, booking
```

