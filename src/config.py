from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass(frozen=True)
class Config:
    warehouse_path: Path
    raw_dir: Path
    outputs_dir: Path
    cfg: dict

def load_config(path: str = "config.yaml") -> Config:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return Config(
        warehouse_path=Path(data["warehouse_path"]),
        raw_dir=Path(data["raw_dir"]),
        outputs_dir=Path(data["outputs_dir"]),
        cfg=data,
    )
