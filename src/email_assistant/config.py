from __future__ import annotations
from pathlib import Path
import json, os
from typing import Any, Dict

DEFAULT_CONFIG_FILE = Path("app.config.json")

def load_config(path: str | Path = DEFAULT_CONFIG_FILE) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def ensure_dirs(cfg: Dict[str, Any]) -> None:
    for key in ["stores", "graphdb"]:
        if key in cfg and isinstance(cfg[key], dict):
            for sub in ["root", "decisions", "dataDir"]:
                val = cfg[key].get(sub)
                if isinstance(val, str):
                    Path(os.path.expanduser(val)).mkdir(parents=True, exist_ok=True)
