"""OpenCLIP image embedder.

Default: ViT-B-32 / laion2b_s34b_b79k (512-d). Licenses checked 2026-10-31:
open_clip code is MIT; the laion/CLIP-ViT-B-32-laion2B-s34B-b79K weights are MIT.
Weights are downloaded from Hugging Face on first use and cached locally.
"""

from __future__ import annotations

import logging
import threading

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class OpenClipEmbedder:
    def __init__(self, model_name: str, pretrained: str, device: str = "cpu", expected_dimension: int | None = None):
        self.model_name = model_name
        self.pretrained = pretrained
        self.device = device
        self.model_id = f"open_clip:{model_name}:{pretrained}"
        self._expected_dimension = expected_dimension
        self._model = None
        self._preprocess = None
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        return True

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            import open_clip
            import torch

            logger.info("Loading OpenCLIP model %s (%s) on %s", self.model_name, self.pretrained, self.device)
            model, _, preprocess = open_clip.create_model_and_transforms(self.model_name, pretrained=self.pretrained, device=self.device)
            model.eval()
            torch.set_grad_enabled(False)
            self._model, self._preprocess = model, preprocess

    def warm_up(self) -> None:
        self._ensure_loaded()

    def embed(self, image: Image.Image) -> np.ndarray:
        import torch

        self._ensure_loaded()
        tensor = self._preprocess(image.convert("RGB")).unsqueeze(0).to(self.device)
        with torch.no_grad():
            features = self._model.encode_image(tensor)
            features = features / features.norm(dim=-1, keepdim=True)
        vector = features[0].float().cpu().numpy().astype(np.float32)
        if self._expected_dimension and vector.shape[0] != self._expected_dimension:
            raise RuntimeError(
                f"{self.model_id} produces {vector.shape[0]}-d vectors but the database expects {self._expected_dimension}"
            )
        return vector


def build_embedder(enabled: bool, model_name: str, pretrained: str, device: str, dimension: int):
    from app.services.embeddings.base import DisabledEmbedder

    model_id = f"open_clip:{model_name}:{pretrained}"
    if not enabled:
        return DisabledEmbedder(model_id, "EMBEDDINGS_ENABLED=false")
    try:
        import open_clip  # noqa: F401
        import torch  # noqa: F401
    except ImportError:
        return DisabledEmbedder(model_id, "open_clip_torch / torch not installed (see requirements-ml.txt)")
    return OpenClipEmbedder(model_name, pretrained, device, expected_dimension=dimension)
