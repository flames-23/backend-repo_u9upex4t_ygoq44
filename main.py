import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Hotel, Booking, ContactMessage

app = FastAPI(title="Hotel Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Util to convert ObjectId to string

def serialize_doc(doc):
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    # Convert dates to isoformat if present
    for k, v in list(doc.items()):
        if hasattr(v, "isoformat"):
            try:
                doc[k] = v.isoformat()
            except Exception:
                pass
    return doc


@app.get("/")
def read_root():
    return {"message": "Hotel Booking API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# Auth - basic email login (demo): create or return user tokenless
class LoginRequest(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    password: str

@app.post("/auth/login")
def login(req: LoginRequest):
    # For demo: store user with password hash placeholder
    user_data = {
        "name": req.name or req.email.split("@")[0],
        "email": req.email,
        "password_hash": "demo-hash",  # In real app, hash the password
    }
    try:
        # Upsert-like behavior: if user exists, return it; else create
        existing = db["user"].find_one({"email": req.email}) if db else None
        if not existing:
            create_document("user", user_data)
            existing = db["user"].find_one({"email": req.email}) if db else user_data
        return {"user": {"name": existing.get("name", user_data["name"]), "email": req.email}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Seed hotels (idempotent)
SAMPLE_HOTELS = [
    Hotel(
        name="Seaside Paradise Resort",
        city="Miami",
        description="Oceanfront resort with private beach, pool, and spa.",
        images=[
            "https://images.unsplash.com/photo-1501117716987-c8e3f71b1e47",
            "https://images.unsplash.com/photo-1559599238-0f8c2f66a7e3"
        ],
        price_per_night=219.0,
        rating=4.6
    ),
    Hotel(
        name="Urban Chic Hotel",
        city="New York",
        description="Boutique hotel in the heart of the city with skyline views.",
        images=[
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
            "https://images.unsplash.com/photo-1509057199576-632a47484ece"
        ],
        price_per_night=299.0,
        rating=4.7
    ),
    Hotel(
        name="Mountain Escape Lodge",
        city="Denver",
        description="Cozy lodge with mountain views, hiking access, and hot tubs.",
        images=[
            "https://images.unsplash.com/photo-1505691938895-1758d7feb511",
            "https://images.unsplash.com/photo-1507679799987-c73779587ccf"
        ],
        price_per_night=189.0,
        rating=4.5
    )
]

@app.post("/hotels/seed")
def seed_hotels():
    try:
        if not db:
            raise Exception("Database not configured")
        for h in SAMPLE_HOTELS:
            exists = db["hotel"].find_one({"name": h.name})
            if not exists:
                create_document("hotel", h)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hotels")
def list_hotels(city: Optional[str] = None) -> List[dict]:
    try:
        flt = {"city": city} if city else {}
        hotels = get_documents("hotel", flt, None)
        return [serialize_doc(h) for h in hotels]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BookingRequest(BaseModel):
    user_email: EmailStr
    hotel_id: str
    check_in: date
    check_out: date
    guests: int
    special_requests: Optional[str] = None

@app.post("/bookings")
def create_booking(req: BookingRequest):
    try:
        # Validate hotel exists
        if not db:
            raise Exception("Database not configured")
        hotel = db["hotel"].find_one({"_id": ObjectId(req.hotel_id)})
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")
        booking = Booking(**req.model_dump())
        booking_id = create_document("booking", booking)
        return {"id": booking_id, "message": "Booking confirmed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/contact")
def contact(message: ContactMessage):
    try:
        mid = create_document("contactmessage", message)
        return {"id": mid, "status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
