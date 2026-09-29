"""Infer table name, format and partition values from an object key.

The data dictionary only promises `data/<table>.csv` for small tables and
year/month/day partitions for large fact tables, so we accept any of:

    data/customers.csv
    data/customers/customers.csv
    data/transactions/year=2024/month=01/day=05/part-000.csv(.gz)
    data/transactions/2024/01/05/part-000.parquet
    data/transactions/process_date=2024-01-05/x.json
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

FORMATS = {
    ".csv": "csv", ".csv.gz": "csv", ".tsv": "csv", ".txt": "csv",
    ".parquet": "parquet", ".pq": "parquet",
    ".json": "json", ".jsonl": "json", ".ndjson": "json", ".json.gz": "json",
}
_KV = re.compile(r"^([A-Za-z_]+)=(.+)$")


@dataclass
class KeyInfo:
    key: str
    table: str | None
    fmt: str | None
    partitions: dict = field(default_factory=dict)


def file_format(name: str) -> str | None:
    low = name.lower()
    for ext in sorted(FORMATS, key=len, reverse=True):
        if low.endswith(ext):
            return FORMATS[ext]
    return None


def _strip_ext(name: str) -> str:
    low = name.lower()
    for ext in sorted(FORMATS, key=len, reverse=True):
        if low.endswith(ext):
            return name[: -len(ext)]
    return name


def parse_key(key: str, prefix: str = "data/") -> KeyInfo:
    rel = key[len(prefix):] if key.startswith(prefix) else key
    parts = [p for p in rel.split("/") if p]
    if not parts:
        return KeyInfo(key, None, None)
    fmt = file_format(parts[-1])
    if len(parts) == 1:
        table = _strip_ext(parts[0])
    else:
        table = parts[0]
    table = table.lower().strip()
    parts_vals: dict = {}
    positional = []
    for seg in parts[1:-1]:
        m = _KV.match(seg)
        if m:
            parts_vals[m.group(1)] = m.group(2)
        elif seg.isdigit():
            positional.append(seg)
    for name, val in zip(("year", "month", "day"), positional):
        parts_vals.setdefault(name, val)
    return KeyInfo(key, table, fmt, parts_vals)
