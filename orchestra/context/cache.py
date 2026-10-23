"""Deterministic content-hash cache for parsed manifests, indexes, and evaluation results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ContentCache:
    """Manages file-backed deterministic caching with SHA256 invalidation."""

    def __init__(self, cache_dir: Union[str, Path]):
        self.cache_dir = Path(cache_dir).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_key_hash(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def get(self, key: str, expected_content_hash: Optional[str] = None) -> Optional[Any]:
        cache_file = self.cache_dir / f"{self._get_key_hash(key)}.json"
        if not cache_file.is_file():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                entry = json.load(f)

            if expected_content_hash is not None:
                if entry.get("content_hash") != expected_content_hash:
                    # Stale entry
                    return None

            return entry.get("data")
        except Exception:
            return None

    def set(self, key: str, data: Any, content_hash: Optional[str] = None) -> None:
        cache_file = self.cache_dir / f"{self._get_key_hash(key)}.json"
        entry = {
            "key": key,
            "content_hash": content_hash,
            "data": data,
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)

    def invalidate(self, key: str) -> bool:
        cache_file = self.cache_dir / f"{self._get_key_hash(key)}.json"
        if cache_file.is_file():
            cache_file.unlink()
            return True
        return False

    def clear(self) -> int:
        count = 0
        for f in self.cache_dir.glob("*.json"):
            f.unlink()
            count += 1
        return count
