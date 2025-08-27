from __future__ import annotations
from pathlib import Path
import json, os, glob, datetime
from typing import Any, Dict, List

def _expand(path: str) -> Path:
    return Path(os.path.expanduser(path))

class JsonStore:
    def __init__(self, path: str):
        self.path = _expand(path)

    def read(self) -> Any:
        if not self.path.exists():
            return None
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def write(self, data: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

class NdjsonStore:
    def __init__(self, dir_path: str):
        self.dir = _expand(dir_path)
        self.dir.mkdir(parents=True, exist_ok=True)

    def append(self, obj: Dict[str, Any], dt: datetime.date | None = None) -> Path:
        dt = dt or datetime.datetime.now().date()
        out = self.dir / f"{dt.isoformat()}.ndjson"
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj) + "\n")
        return out

    def scan(self, start: str | None = None, end: str | None = None, limit: int = 1000) -> List[Dict[str, Any]]:
        files = sorted(glob.glob(str(self.dir / "*.ndjson")))
        rows: List[Dict[str, Any]] = []
        for p in files:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
                    if len(rows) >= limit:
                        return rows
        return rows
