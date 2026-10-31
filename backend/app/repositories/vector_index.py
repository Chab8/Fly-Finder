"""Visual similarity search over catalog image embeddings.

Similarity values are cosine similarities in [-1, 1]. They measure how alike two images
look to the embedding model. They are NOT probabilities of a correct identification.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class VectorHit:
    image_id: uuid.UUID
    owner_kind: str  # organism | fly
    owner_id: uuid.UUID
    similarity: float


class VectorIndex(Protocol):
    def search(self, owner_kind: str, embedding: np.ndarray, model: str, k: int = 10) -> list[VectorHit]: ...


def aggregate_by_owner(hits: list[VectorHit], k: int) -> list[VectorHit]:
    """Keep the best-scoring image per catalog record."""
    best: dict[uuid.UUID, VectorHit] = {}
    for hit in hits:
        if hit.owner_id not in best or hit.similarity > best[hit.owner_id].similarity:
            best[hit.owner_id] = hit
    return sorted(best.values(), key=lambda h: h.similarity, reverse=True)[:k]


class NullVectorIndex:
    """Used when no embeddings exist yet. Always returns no results."""

    def search(self, owner_kind: str, embedding: np.ndarray, model: str, k: int = 10) -> list[VectorHit]:
        return []


class InMemoryVectorIndex:
    """Numpy index loaded from an .npz file written by scripts/generate_embeddings.py."""

    def __init__(self, model: str, image_ids: list[uuid.UUID], owner_kinds: list[str], owner_ids: list[uuid.UUID], vectors: np.ndarray):
        self.model = model
        self._image_ids = image_ids
        self._owner_kinds = np.array(owner_kinds)
        self._owner_ids = owner_ids
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        self._vectors = vectors / np.where(norms == 0, 1, norms)

    @classmethod
    def from_file(cls, path: Path) -> InMemoryVectorIndex:
        data = np.load(path, allow_pickle=False)
        return cls(
            model=str(data["model"]),
            image_ids=[uuid.UUID(x) for x in data["image_ids"]],
            owner_kinds=list(data["owner_kinds"]),
            owner_ids=[uuid.UUID(x) for x in data["owner_ids"]],
            vectors=data["vectors"].astype(np.float32),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            path, model=np.array(self.model), image_ids=np.array([str(x) for x in self._image_ids]),
            owner_kinds=self._owner_kinds, owner_ids=np.array([str(x) for x in self._owner_ids]), vectors=self._vectors,
        )

    def search(self, owner_kind: str, embedding: np.ndarray, model: str, k: int = 10) -> list[VectorHit]:
        if model != self.model or len(self._image_ids) == 0:
            return []
        query = np.asarray(embedding, dtype=np.float32)
        query = query / (np.linalg.norm(query) or 1.0)
        mask = self._owner_kinds == owner_kind
        if not mask.any():
            return []
        indices = np.flatnonzero(mask)
        scores = self._vectors[indices] @ query
        order = indices[np.argsort(-scores)][: k * 4]
        score_by_index = dict(zip(indices.tolist(), scores.tolist(), strict=True))
        hits = [VectorHit(self._image_ids[i], owner_kind, self._owner_ids[i], float(score_by_index[i])) for i in order]
        return aggregate_by_owner(hits, k)
