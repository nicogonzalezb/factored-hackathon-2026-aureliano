"""Paths and settings. Everything is driven by .env / environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    """Tiny .env loader (no extra dependency). Real env vars win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")


def _s3_location() -> tuple[str, str]:
    """DATASET_S3_URI (s3://bucket/prefix/) wins; DATATHON_BUCKET/DATATHON_PREFIX kept as fallback."""
    uri = os.getenv("DATASET_S3_URI", "")
    if uri.startswith("s3://"):
        bucket, _, prefix = uri[len("s3://"):].partition("/")
        return bucket, prefix
    return (os.getenv("DATATHON_BUCKET", "factored-datathon-2026-s3-157725502942-us-east-2-an"),
            os.getenv("DATATHON_PREFIX", "data/"))


_BUCKET, _PREFIX = _s3_location()


@dataclass(frozen=True)
class Settings:
    bucket: str = _BUCKET
    prefix: str = _PREFIX
    region: str = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-2"))
    data_dir: Path = Path(os.getenv("DATA_DIR", ROOT / "data"))
    reports_dir: Path = Path(os.getenv("REPORTS_DIR", ROOT / "reports"))
    contracts_path: Path = ROOT / "contracts" / "tables.yml"

    @property
    def raw(self) -> Path:
        return self.data_dir / "raw"

    @property
    def bronze(self) -> Path:
        return self.data_dir / "bronze"

    @property
    def silver(self) -> Path:
        return self.data_dir / "silver"

    @property
    def state(self) -> Path:
        return self.data_dir / "_state"

    @property
    def manifest(self) -> Path:
        return self.state / "s3_manifest.jsonl"

    @property
    def warehouse(self) -> Path:
        return self.data_dir / "warehouse.duckdb"

    def ensure_dirs(self) -> None:
        for p in (self.raw, self.bronze, self.silver, self.state, self.reports_dir):
            p.mkdir(parents=True, exist_ok=True)


SETTINGS = Settings()


def load_contracts() -> dict:
    return yaml.safe_load(SETTINGS.contracts_path.read_text())["tables"]
