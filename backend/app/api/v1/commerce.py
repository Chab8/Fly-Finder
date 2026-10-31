from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import Container, get_container
from app.schemas.catalog import Page
from app.schemas.commerce import ProductInfo, StoreInfo

router = APIRouter(tags=["commerce"])


@router.get("/products", response_model=Page[ProductInfo])
def list_products(
    fly_id: uuid.UUID | None = None,
    store_id: uuid.UUID | None = None,
    country: str | None = Query(None, pattern=r"^[A-Za-z]{2}$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    container: Container = Depends(get_container),
) -> Page[ProductInfo]:
    return container.products.list(
        fly_id=fly_id, store_id=store_id, country=country.upper() if country else None, limit=limit, offset=offset,
    )


@router.get("/stores", response_model=list[StoreInfo])
def list_stores(
    country: str | None = Query(None, pattern=r"^[A-Za-z]{2}$", description="Stores located in or shipping to this country"),
    container: Container = Depends(get_container),
) -> list[StoreInfo]:
    return container.products.stores(country)
