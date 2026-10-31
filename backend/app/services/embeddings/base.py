"""Image embedder interface."""

from __future__ import annotations

from typing import Protocol

import numpy as np
from PIL import Image


class ImageEmbedder(Protocol):
    model_id: str

    @property
    def available(self) -> bool: ...

    def embed(self, image: Image.Image) -> np.ndarray:
        """Return an L2-normalized float32 vector."""
        ...


class DisabledEmbedder:
    """Used when EMBEDDINGS_ENABLED=false or the ML dependencies are not installed."""

    def __init__(self, model_id: str, reason: str):
        self.model_id = model_id
        self.reason = reason

    @property
    def available(self) -> bool:
        return False

    def embed(self, image: Image.Image) -> np.ndarray:
        raise RuntimeError(f"embeddings disabled: {self.reason}")
