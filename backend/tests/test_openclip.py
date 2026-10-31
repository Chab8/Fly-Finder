"""Loads the real OpenCLIP weights (~600 MB download on first run). Opt-in: RUN_ML_TESTS=1."""

import os

import numpy as np
import pytest
from PIL import Image

from app.services.embeddings.openclip import OpenClipEmbedder

pytestmark = [
    pytest.mark.ml,
    pytest.mark.skipif(os.environ.get("RUN_ML_TESTS") != "1", reason="set RUN_ML_TESTS=1 to load the real model"),
]


def test_real_embedding_is_512d_and_normalized():
    embedder = OpenClipEmbedder("ViT-B-32", "laion2b_s34b_b79k", "cpu", expected_dimension=512)
    red = embedder.embed(Image.new("RGB", (256, 256), (200, 30, 30)))
    red2 = embedder.embed(Image.new("RGB", (300, 300), (190, 40, 35)))
    blue = embedder.embed(Image.new("RGB", (256, 256), (30, 30, 200)))
    assert red.shape == (512,) and np.linalg.norm(red) == pytest.approx(1.0, abs=1e-4)
    assert float(red @ red2) > float(red @ blue)
