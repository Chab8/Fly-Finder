"""API response shapes for stores and commercial products."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import AvailabilityStatus


class StoreInfo(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    website: str
    country: str
    currency: str
    description: str | None
    affiliate_program: bool
    shipping_countries: list[str]
    is_demo: bool


class ProductPatternLink(BaseModel):
    fly_pattern_id: uuid.UUID
    size: str | None
    color: str | None
    variant: str | None


class ProductInfo(BaseModel):
    id: uuid.UUID
    name: str
    brand: str | None
    description: str | None
    store: StoreInfo
    buy_url: str  # affiliate link when present, otherwise the store's product page
    product_url: str
    # Prices are shown exactly as recorded, in their own currency. Never converted.
    price: Decimal | None
    currency: str | None
    availability_status: AvailabilityStatus
    country: str | None
    last_verified_at: datetime | None
    patterns: list[ProductPatternLink]
    ships_to_requested_country: bool | None
    is_demo: bool
