from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict

def load_yaml(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
