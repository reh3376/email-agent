from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_FILE = Path("app.config.json")


def load_config(path: str | Path = DEFAULT_CONFIG_FILE) -> dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dirs(cfg: dict[str, Any]) -> None:
    for key in ["stores", "graphdb"]:
        if key in cfg and isinstance(cfg[key], dict):
            for sub in ["root", "decisions", "dataDir"]:
                val = cfg[key].get(sub)
                if isinstance(val, str):
                    Path(os.path.expanduser(val)).mkdir(parents=True, exist_ok=True)
