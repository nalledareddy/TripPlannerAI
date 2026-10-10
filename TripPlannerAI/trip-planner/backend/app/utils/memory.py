from __future__ import annotations

import json
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings

try:
    import chromadb
except Exception:  # pragma: no cover - optional dependency load failure
    chromadb = None


class PreferenceMemoryStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.file_path: Path = self.settings.memory_file
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._chroma_collection = None

        if self.settings.use_chroma and chromadb is not None:
            try:
                client = chromadb.PersistentClient(path=str(self.settings.chroma_dir))
                self._chroma_collection = client.get_or_create_collection("trip_preferences")
            except Exception:
                self._chroma_collection = None

    def _read_file(self) -> dict[str, Any]:
        if not self.file_path.exists():
            return {}
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_file(self, data: dict[str, Any]) -> None:
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def load_preferences(self, user_id: str) -> dict[str, Any]:
        if self._chroma_collection is not None:
            try:
                result = self._chroma_collection.get(ids=[user_id])
                documents = result.get("documents") or []
                if documents and documents[0]:
                    parsed = json.loads(documents[0])
                    return parsed if isinstance(parsed, dict) else {}
            except Exception:
                pass

        with self._lock:
            data = self._read_file()
        record = data.get(user_id, {})
        return record if isinstance(record, dict) else {}

    def save_preferences(self, user_id: str, preferences: dict[str, Any]) -> None:
        cleaned = preferences if isinstance(preferences, dict) else {}

        if self._chroma_collection is not None:
            try:
                self._chroma_collection.upsert(ids=[user_id], documents=[json.dumps(cleaned)])
                return
            except Exception:
                pass

        with self._lock:
            data = self._read_file()
            data[user_id] = cleaned
            try:
                self._write_file(data)
            except Exception:
                return


@lru_cache(maxsize=1)
def get_memory_store() -> PreferenceMemoryStore:
    return PreferenceMemoryStore()
