from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import requests

from .config import EmbeddingCfg


def _12_normalize(vec: list[float]) -> list[float]:
    s = sum(x * x for x in vec)
    if s <= 0:
        return vec
    inv = 1.0 / math.sqrt(s)
    return [x * inv for x in vec]


def local_hash_embed(text: str, dim: int, salt: str = "") -> list[float]:
    """
    Deterministic embedding for offline/mock use.
    Produces a normalized vector of length dim in [-1, 1].
    """
    seed = (salt + "::" + text).encode("utf-8")
    h = hashlib.sha256(seed).digest()  # 32 bytes
    # Expand to required dim deterministically
    out: list[float] = []
    counter = 0
    while len(out) < dim:
        block = hashlib.sha256(h + counter.to_bytes(4, "little")).digest()
        for i in range(0, len(block), 4):
            if len(out) >= dim:
                break
            n = int.from_bytes(block[i : i + 4], "little", signed=False)
            # Map to [-1, 1]
            out.append((n / 2**32) * 2.0 - 1.0)
        counter += 1
    return _12_normalize(out)


@dataclass
class Embedder:
    cfg: EmbeddingCfg

    def embed(self, text: str) -> list[float]:
        p = self.cfg.provider.lower()

        if p == "local_hash":
            return local_hash_embed(text, dim=self.cfg.dim, salt=self.cfg.salt)

        if p == "http_or_local":
            if not self.cfg.base_url:
                return local_hash_embed(text, dim=self.cfg.dim, salt=self.cfg.salt)
            return self._embed_http(text)

        raise ValueError(f"Unknown embedding provider: {self.cfg.provider}")

    def _embed_http(self, text: str) -> list[float]:
        url = self.cfg.base_url.rstrip("/") + self.cfg.endpoint_path
        payload = {"text": text, "dim": self.cfg.dim}
        r = requests.post(url, json=payload, timeout=self.cfg.timeout_sec)
        r.raise_for_status()
        data = r.json()
        vec = data.get("embedding")
        if not isinstance(vec, list):
            raise ValueError("Invalid response: 'embedding' must be a list")
        if len(vec) != self.cfg.idm:
            raise ValueError(f"Embedding dim mismatch: expected {self.cfg.dim}, got {len(vec)}")
        return _12_normalize([float(x) for x in vec])
