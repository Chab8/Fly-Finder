"""Commercial product queries. Prices are shown as recorded, in their own currency."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.models.enums import AvailabilityStatus
from app.repositories.catalog_snapshot import SnapshotProvider
from app.schemas.catalog import Page
from app.schemas.commerce import ProductInfo, StoreInfo

_AVAILABILITY_ORDER = {
    AvailabilityStatus.in_stock: 0, AvailabilityStatus.preorder: 1, AvailabilityStatus.unknown: 2,
    AvailabilityStatus.out_of_stock: 3, AvailabilityStatus.discontinued: 4,
}
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _sort_key(product: ProductInfo) -> tuple:
    verified = product.last_verified_at or _EPOCH
    if verified.tzinfo is None:
        verified = verified.replace(tzinfo=UTC)
    return (
        product.ships_to_requested_country is False,  # products that ship to the user first
        _AVAILABILITY_ORDER[product.availability_status],
        -verified.timestamp(),                          # most recently verified first
        product.name,
    )


class ProductService:
    def __init__(self, snapshots: SnapshotProvider):
        self._snapshots = snapshots

    def for_fly(self, fly_id: uuid.UUID, country: str | None = None) -> list[ProductInfo]:
        snapshot = self._snapshots.get()
        snapshot.get_fly(fly_id)  # 404 if the pattern does not exist
        products = [snapshot.product_info(p, country) for p in snapshot.products_for_fly(fly_id)]
        return sorted(products, key=_sort_key)

    def list(
        self, *, fly_id: uuid.UUID | None = None, store_id: uuid.UUID | None = None, country: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> Page[ProductInfo]:
        snapshot = self._snapshots.get()
        records = snapshot.products_for_fly(fly_id) if fly_id else snapshot.all_products()
        if store_id:
            records = [p for p in records if p.store_id == store_id]
        items = sorted((snapshot.product_info(p, country) for p in records), key=_sort_key)
        return Page[ProductInfo](items=items[offset : offset + limit], total=len(items), limit=limit, offset=offset)

    def stores(self, country: str | None = None) -> list[StoreInfo]:
        snapshot = self._snapshots.get()
        stores = [snapshot.store_info(s.id) for s in snapshot.stores.values()]
        if country:
            code = country.upper()
            stores = [s for s in stores if s.country == code or code in s.shipping_countries or "WORLDWIDE" in s.shipping_countries]
        return sorted(stores, key=lambda s: s.name.lower())
