"""Inventory + incremental download of the datathon bucket, with a lineage manifest.

Each object's key, size, ETag and LastModified are recorded in
data/_state/s3_manifest.jsonl. A file is (re)downloaded only when it is new or
its ETag/size changed, so re-running picks up late-arriving partitions without
re-pulling 19M rows.

`--source-dir` replays the same logic against a local folder (used by the test
fixture to prove incremental/late-arrival behaviour offline).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from .config import SETTINGS
from .layout import parse_key


# ---------------------------------------------------------------- sources
class S3Source:
    def __init__(self, bucket: str, prefix: str, region: str):
        import boto3
        from botocore.config import Config

        self.bucket, self.prefix = bucket, prefix
        self.s3 = boto3.client("s3", region_name=region,
                               config=Config(retries={"max_attempts": 8, "mode": "adaptive"},
                                             max_pool_connections=32))

    def list(self):
        pag = self.s3.get_paginator("list_objects_v2")
        for page in pag.paginate(Bucket=self.bucket, Prefix=self.prefix):
            for o in page.get("Contents", []):
                if o["Key"].endswith("/"):
                    continue
                yield {"key": o["Key"], "size": o["Size"], "etag": o["ETag"].strip('"'),
                       "last_modified": o["LastModified"].isoformat()}

    def fetch(self, key: str, dest: Path) -> None:
        tmp = dest.with_suffix(dest.suffix + ".part")
        self.s3.download_file(self.bucket, key, str(tmp))
        tmp.replace(dest)


class LocalSource:
    """Pretends a local directory is the bucket. Keys are '<prefix><relpath>'."""

    def __init__(self, root: Path, prefix: str):
        self.root, self.prefix = Path(root), prefix

    def list(self):
        for p in sorted(self.root.rglob("*")):
            if p.is_file():
                st = p.stat()
                yield {"key": self.prefix + p.relative_to(self.root).as_posix(), "size": st.st_size,
                       "etag": hashlib.md5(p.read_bytes()).hexdigest(),
                       "last_modified": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat()}

    def fetch(self, key: str, dest: Path) -> None:
        shutil.copy2(self.root / key[len(self.prefix):], dest)


# ---------------------------------------------------------------- manifest
def read_manifest() -> dict[str, dict]:
    m: dict[str, dict] = {}
    if SETTINGS.manifest.exists():
        for line in SETTINGS.manifest.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                m[r["key"]] = r
    return m


def write_manifest(m: dict[str, dict]) -> None:
    tmp = SETTINGS.manifest.with_suffix(".tmp")
    tmp.write_text("\n".join(json.dumps(v, sort_keys=True) for _, v in sorted(m.items())) + "\n")
    tmp.replace(SETTINGS.manifest)


def local_path_for(key: str) -> Path:
    rel = key[len(SETTINGS.prefix):] if key.startswith(SETTINGS.prefix) else key
    return SETTINGS.raw / rel


# ---------------------------------------------------------------- commands
def human(n: float) -> str:
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:,.1f} {u}"
        n /= 1024
    return f"{n:,.1f} PB"


def inventory(objs: list[dict]) -> None:
    by_table: dict[str, dict] = defaultdict(lambda: {"files": 0, "bytes": 0, "fmts": set(), "parts": set()})
    for o in objs:
        ki = parse_key(o["key"], SETTINGS.prefix)
        t = by_table[ki.table or "?"]
        t["files"] += 1
        t["bytes"] += o["size"]
        t["fmts"].add(ki.fmt or "?")
        t["parts"].update(ki.partitions.keys())
    print(f"{'table':28} {'files':>7} {'size':>11}  formats   partition keys")
    for name, t in sorted(by_table.items()):
        print(f"{name:28} {t['files']:>7} {human(t['bytes']):>11}  {','.join(sorted(t['fmts'])):9} "
              f"{','.join(sorted(t['parts'])) or '-'}")
    print(f"{'TOTAL':28} {len(objs):>7} {human(sum(o['size'] for o in objs)):>11}")
    print("\nFirst keys:")
    for o in objs[:10]:
        print("  ", o["key"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Download datathon data incrementally")
    ap.add_argument("--list", action="store_true", help="inventory only, no download")
    ap.add_argument("--tables", nargs="*", help="only these tables")
    ap.add_argument("--sample-files", type=int, default=0,
                    help="max files per table (quick start); 0 = all")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--source-dir", help="use a local folder instead of S3 (test fixture)")
    a = ap.parse_args(argv)

    SETTINGS.ensure_dirs()
    src = (LocalSource(Path(a.source_dir), SETTINGS.prefix) if a.source_dir
           else S3Source(SETTINGS.bucket, SETTINGS.prefix, SETTINGS.region))
    objs = list(src.list())
    if a.tables:
        wanted = {t.lower() for t in a.tables}
        objs = [o for o in objs if parse_key(o["key"], SETTINGS.prefix).table in wanted]
    if a.list:
        inventory(objs)
        return 0

    if a.sample_files:
        seen: dict[str, int] = defaultdict(int)
        keep = []
        for o in sorted(objs, key=lambda o: o["key"]):
            t = parse_key(o["key"], SETTINGS.prefix).table
            if seen[t] < a.sample_files:
                keep.append(o)
                seen[t] += 1
        objs = keep

    manifest = read_manifest()
    todo = []
    for o in objs:
        prev = manifest.get(o["key"])
        dest = local_path_for(o["key"])
        if prev and prev["etag"] == o["etag"] and prev["size"] == o["size"] and dest.exists():
            continue
        todo.append(o)

    print(f"{len(objs)} objects in scope, {len(todo)} new/changed "
          f"({human(sum(o['size'] for o in todo))}) to download")
    now = datetime.now(timezone.utc).isoformat()
    failures = 0

    def job(o):
        dest = local_path_for(o["key"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        src.fetch(o["key"], dest)
        return o

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(job, o): o for o in todo}
        for i, f in enumerate(as_completed(futs), 1):
            o = futs[f]
            try:
                f.result()
                ki = parse_key(o["key"], SETTINGS.prefix)
                prev = manifest.get(o["key"])
                manifest[o["key"]] = {**o, "table": ki.table, "format": ki.fmt,
                                      "partitions": ki.partitions,
                                      "local_path": str(local_path_for(o["key"]).relative_to(SETTINGS.data_dir)),
                                      "downloaded_at": now,
                                      "first_seen_at": (prev or {}).get("first_seen_at", now),
                                      "version": (prev or {}).get("version", 0) + 1}
            except Exception as e:  # keep going; report at the end
                failures += 1
                print(f"  FAILED {o['key']}: {e}", file=sys.stderr)
            if i % 200 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)}")
                write_manifest(manifest)
    write_manifest(manifest)
    print(f"done. failures={failures}. manifest: {SETTINGS.manifest}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
