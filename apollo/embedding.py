from __future__ import annotations

import hashlib
import math
from typing import Protocol


class EmbeddingModel(Protocol):
    def encode(self, texts: list[str]) -> list[list[float]]:
        ...


class BGEEmbeddingModel:
    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "BGE embedding requires sentence-transformers. "
                "Install project dependencies with: python -m pip install -e ."
            ) from exc
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]


class HashEmbeddingModel:
    """Dependency-free smoke-test embedding.

    Production routing should use BGEEmbeddingModel. This model exists so tests
    and demos can exercise the two-stage control flow without network/model
    setup.
    """

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [self._encode_one(text) for text in texts]

    def _encode_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = self._tokens(text)
        for token in tokens:
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def _tokens(self, text: str) -> list[str]:
        compact = "".join(text.split())
        chars = [char for char in compact if char]
        bigrams = [compact[i : i + 2] for i in range(max(0, len(compact) - 1))]
        trigrams = [compact[i : i + 3] for i in range(max(0, len(compact) - 2))]
        return chars + bigrams + trigrams


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))
