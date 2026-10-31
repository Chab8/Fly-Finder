from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import Container, get_container, get_language
from app.models.enums import FishingEnvironment, FlyCategory, OrganismGroup, TaxonRank
from app.schemas.catalog import FlyPatternDetail, FlyPatternSummary, OrganismDetail, OrganismSummary, Page, SearchResults
from app.schemas.commerce import ProductInfo

router = APIRouter(tags=["catalog"])


@router.get("/organisms", response_model=Page[OrganismSummary])
def list_organisms(
    q: str | None = Query(None, max_length=100),
    group: OrganismGroup | None = None,
    order: str | None = Query(None, max_length=80),
    family: str | None = Query(None, max_length=80),
    rank: TaxonRank | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    lang: str = Depends(get_language),
    container: Container = Depends(get_container),
) -> Page[OrganismSummary]:
    return container.snapshots.get().list_organisms(
        lang=lang, q=q, group=group, order=order, family=family, rank=rank, limit=limit, offset=offset,
    )


@router.get("/organisms/{organism_id}", response_model=OrganismDetail)
def get_organism(organism_id: uuid.UUID, lang: str = Depends(get_language), container: Container = Depends(get_container)) -> OrganismDetail:
    snapshot = container.snapshots.get()
    return snapshot.organism_detail(snapshot.get_organism(organism_id), lang)


@router.get("/flies", response_model=Page[FlyPatternSummary])
def list_flies(
    q: str | None = Query(None, max_length=100),
    category: FlyCategory | None = None,
    environment: FishingEnvironment | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    container: Container = Depends(get_container),
) -> Page[FlyPatternSummary]:
    return container.snapshots.get().list_flies(q=q, category=category, environment=environment, limit=limit, offset=offset)


@router.get("/flies/{fly_id}", response_model=FlyPatternDetail)
def get_fly(fly_id: uuid.UUID, lang: str = Depends(get_language), container: Container = Depends(get_container)) -> FlyPatternDetail:
    snapshot = container.snapshots.get()
    return snapshot.fly_detail(snapshot.get_fly(fly_id), lang)


@router.get("/flies/{fly_id}/products", response_model=list[ProductInfo])
def get_fly_products(
    fly_id: uuid.UUID,
    country: str | None = Query(None, pattern=r"^[A-Za-z]{2}$"),
    container: Container = Depends(get_container),
) -> list[ProductInfo]:
    return container.products.for_fly(fly_id, country.upper() if country else None)


@router.get("/search", response_model=SearchResults)
def search(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    lang: str = Depends(get_language),
    container: Container = Depends(get_container),
) -> SearchResults:
    return container.snapshots.get().search(q, lang, limit)
