"""
Database Schemas for Hotel Booking App

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Hashed password")

class Hotel(BaseModel):
    name: str = Field(..., description="Hotel name")
    city: str = Field(..., description="City where the hotel is located")
    description: str = Field(..., description="Short description")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    price_per_night: float = Field(..., ge=0, description="Price per night in USD")
    rating: float = Field(4.5, ge=0, le=5, description="Average rating")

class Booking(BaseModel):
    user_email: EmailStr = Field(..., description="Email of the user booking")
    hotel_id: str = Field(..., description="ID of the booked hotel")
    check_in: date = Field(..., description="Check-in date")
    check_out: date = Field(..., description="Check-out date")
    guests: int = Field(..., ge=1, le=10, description="Number of guests")
    special_requests: Optional[str] = Field(None, description="Optional notes")

class ContactMessage(BaseModel):
    name: str = Field(...)
    email: EmailStr = Field(...)
    message: str = Field(..., min_length=5)
