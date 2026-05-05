from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "tool_embeddings.json"


def compute_tools_hash(tools_path: Path) -> str:
    content = tools_path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def save_cache(
    vectors: list[list[float]],
    tool_codes: list[str],
    tools_hash: str,
    embedding: str | None = None,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> None:
    data: dict[str, Any] = {
        "tools_hash": tools_hash,
        "tool_codes": tool_codes,
        "vectors": vectors,
    }
    if embedding is not None:
        data["embedding"] = embedding
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data), encoding="utf-8")


def load_cache(
    tools_hash: str,
    embedding: str | None = None,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> tuple[list[str], list[list[float]]] | None:
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("tools_hash") != tools_hash:
        return None
    if embedding is not None and data.get("embedding") != embedding:
        return None

    tool_codes = data.get("tool_codes")
    vectors = data.get("vectors")
    if not isinstance(tool_codes, list) or not isinstance(vectors, list):
        return None
    return list(map(str, tool_codes)), vectors
