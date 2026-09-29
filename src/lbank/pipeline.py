"""Bronze -> Silver pipeline on DuckDB.

bronze/<table>.parquet
    Every raw file for the table, UNION ALL BY NAME (tolerates schema evolution),
    all columns as VARCHAR, plus lineage columns:
    _source_file, _source_etag, _source_last_modified, _ingested_at.

silver/<table>.parquet
    * blank / 'null' / 'NaN' strings -> NULL
    * column types inferred from the data (never for *_id / *_number / *_code / phone
      columns, which stay VARCHAR so leading zeros survive)
    * exact duplicates dropped, then one row per primary key (latest by the
      contract's order_by column, then latest source file)
    * rows with a NULL primary key go to silver/_quarantine/<table>.parquet
    Stats for every step land in data/_state/silver_<table>.json (read by dq.py).

Each table is skipped when its input fingerprint (source keys + ETags) is
unchanged; use --force to rebuild.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from .config import SETTINGS, load_contracts
from .download import read_manifest

LINEAGE = ["_source_file", "_source_etag", "_source_last_modified", "_ingested_at"]
KEEP_VARCHAR_SUFFIXES = ("_id", "_number", "_code", "phone", "postal_code", "ip_address",
                         "app_version", "_url", "element_id")
TYPE_ORDER = ["BIGINT", "DOUBLE", "BOOLEAN", "DATE", "TIMESTAMP"]
NULL_TOKENS = ("", "null", "none", "nan", "n/a", "na", "\\n")


def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def lit(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def connect(db: Path | str = ":memory:") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(db))
    con.execute("SET preserve_insertion_order=false")
    return con


# ------------------------------------------------------------------ bronze
def files_by_table() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for rec in read_manifest().values():
        if rec.get("table") and rec.get("format") and (SETTINGS.data_dir / rec["local_path"]).exists():
            out[rec["table"]].append(rec)
    return out


def fingerprint(recs: list[dict]) -> str:
    h = hashlib.sha256()
    for r in sorted(recs, key=lambda r: r["key"]):
        h.update(f"{r['key']}|{r['etag']}|{r['size']}\n".encode())
    return h.hexdigest()


def _reader(fmt: str, paths: list[str]) -> str:
    plist = "[" + ",".join(lit(p) for p in paths) + "]"
    if fmt == "csv":
        return (f"read_csv({plist}, all_varchar=true, union_by_name=true, filename=true, "
                f"header=true, auto_detect=true, ignore_errors=false)")
    if fmt == "parquet":
        return f"read_parquet({plist}, union_by_name=true, filename=true)"
    if fmt == "json":
        return f"read_json_auto({plist}, union_by_name=true, filename=true, format='auto')"
    raise ValueError(fmt)


def build_bronze(con, table: str, recs: list[dict]) -> dict:
    by_fmt: dict[str, list[str]] = defaultdict(list)
    for r in recs:
        by_fmt[r["format"]].append(str((SETTINGS.data_dir / r["local_path"]).resolve()))
    con.execute("CREATE OR REPLACE TEMP TABLE _manifest(path VARCHAR, key VARCHAR, etag VARCHAR, lm VARCHAR)")
    con.executemany("INSERT INTO _manifest VALUES (?,?,?,?)",
                    [(str((SETTINGS.data_dir / r["local_path"]).resolve()), r["key"], r["etag"],
                      r["last_modified"]) for r in recs])
    parts = []
    for fmt, paths in by_fmt.items():
        parts.append(f"SELECT COLUMNS(c -> c <> 'filename')::VARCHAR, filename FROM {_reader(fmt, paths)}")
    union = " UNION ALL BY NAME ".join(parts)
    now = datetime.now(timezone.utc).isoformat()
    out = SETTINGS.bronze / f"{table}.parquet"
    tmp = out.with_suffix(".tmp.parquet")
    con.execute(f"""
        COPY (
          SELECT u.* EXCLUDE (filename),
                 m.key  AS _source_file,
                 m.etag AS _source_etag,
                 m.lm   AS _source_last_modified,
                 {lit(now)} AS _ingested_at
          FROM ({union}) u LEFT JOIN _manifest m ON m.path = u.filename
        ) TO {lit(str(tmp))} (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 250000)
    """)
    tmp.replace(out)
    rows = con.execute(f"SELECT count(*) FROM read_parquet({lit(str(out))})").fetchone()[0]
    return {"rows": rows, "files": len(recs), "formats": sorted(by_fmt)}


# ------------------------------------------------------------------ silver
def _clean(col: str) -> str:
    toks = ",".join(lit(t) for t in NULL_TOKENS)
    return f"CASE WHEN lower(trim({q(col)})) IN ({toks}) THEN NULL ELSE trim({q(col)}) END"


def infer_types(con, src: str, cols: list[str]) -> dict[str, str]:
    candidates = [c for c in cols if not c.lower().endswith(KEEP_VARCHAR_SUFFIXES)]
    types = {c: "VARCHAR" for c in cols}
    if not candidates:
        return types
    aggs = []
    for c in candidates:
        cl = _clean(c)
        aggs.append(f"count({cl})")
        for t in TYPE_ORDER:
            # DuckDB happily casts '2024-01-05 10:00:00' to DATE (dropping the time),
            # so only call it a DATE when there is no time component at all.
            expr = f"CASE WHEN length({cl}) <= 10 THEN TRY_CAST({cl} AS DATE) END" if t == "DATE" \
                else f"TRY_CAST({cl} AS {t})"
            aggs.append(f"count({expr})")
    res = con.execute(f"SELECT {', '.join(aggs)} FROM {src}").fetchone()
    step = 1 + len(TYPE_ORDER)
    for i, c in enumerate(candidates):
        nn, *ok = res[i * step:(i + 1) * step]
        if nn == 0:
            continue
        for t, n in zip(TYPE_ORDER, ok):
            if n == nn:
                types[c] = t
                break
    return types


def build_silver(con, table: str, contract: dict | None) -> dict:
    src = f"read_parquet({lit(str(SETTINGS.bronze / f'{table}.parquet'))})"
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()]
    biz = [c for c in cols if c not in LINEAGE]
    types = infer_types(con, src, biz)
    select_typed = ",\n  ".join(
        (f"CAST({_clean(c)} AS {types[c]}) AS {q(c)}" if types[c] != "VARCHAR" else f"{_clean(c)} AS {q(c)}")
        for c in biz)
    con.execute(f"CREATE OR REPLACE TEMP TABLE _typed AS SELECT\n  {select_typed},\n  "
                f"{', '.join(q(c) for c in LINEAGE)} FROM {src}")

    stats: dict = {"table": table, "bronze_rows": con.execute("SELECT count(*) FROM _typed").fetchone()[0],
                   "types": types}
    biz_list = ", ".join(q(c) for c in biz)
    stats["distinct_rows"] = con.execute(f"SELECT count(*) FROM (SELECT DISTINCT {biz_list} FROM _typed)").fetchone()[0]
    stats["exact_duplicates"] = stats["bronze_rows"] - stats["distinct_rows"]

    pk = [c for c in (contract or {}).get("pk", []) if c in biz]
    silver_path = SETTINGS.silver / f"{table}.parquet"
    if pk:
        pk_list = ", ".join(q(c) for c in pk)
        null_pk = " OR ".join(f"{q(c)} IS NULL" for c in pk)
        order_cols = []
        ob = (contract or {}).get("order_by")
        if ob in biz:
            order_cols.append(f"{q(ob)} DESC NULLS LAST")
        order_cols += ["_source_last_modified DESC NULLS LAST", "_source_file DESC"]
        qdir = SETTINGS.silver / "_quarantine"
        qdir.mkdir(exist_ok=True)
        stats["null_pk_rows"] = con.execute(f"SELECT count(*) FROM _typed WHERE {null_pk}").fetchone()[0]
        if stats["null_pk_rows"]:
            con.execute(f"COPY (SELECT * FROM _typed WHERE {null_pk}) TO {lit(str(qdir / f'{table}.parquet'))} (FORMAT parquet)")
        con.execute(f"""
            COPY (
              SELECT * FROM _typed WHERE NOT ({null_pk})
              QUALIFY row_number() OVER (PARTITION BY {pk_list} ORDER BY {', '.join(order_cols)}) = 1
            ) TO {lit(str(silver_path))} (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 250000)""")
        # PK conflicts: same key, different content (after exact dups are removed)
        stats["pk_conflict_rows"] = con.execute(f"""
            SELECT coalesce(sum(n - 1), 0) FROM (
              SELECT count(*) n FROM (SELECT DISTINCT {biz_list} FROM _typed WHERE NOT ({null_pk}))
              GROUP BY {pk_list} HAVING count(*) > 1)""").fetchone()[0]
    else:
        stats["null_pk_rows"] = 0
        stats["pk_conflict_rows"] = None
        con.execute(f"COPY (SELECT DISTINCT ON ({biz_list}) * FROM _typed) TO {lit(str(silver_path))} "
                    f"(FORMAT parquet, COMPRESSION zstd)")
    stats["silver_rows"] = con.execute(f"SELECT count(*) FROM read_parquet({lit(str(silver_path))})").fetchone()[0]
    stats["pk"] = pk
    return stats


def schema_drift(table: str, types: dict[str, str]) -> dict:
    """Compare against the schema seen last run; persist the new one."""
    p = SETTINGS.state / f"schema_{table}.json"
    prev = json.loads(p.read_text()) if p.exists() else None
    p.write_text(json.dumps(types, indent=1, sort_keys=True))
    if prev is None:
        return {"first_run": True}
    return {"added": sorted(set(types) - set(prev)), "removed": sorted(set(prev) - set(types)),
            "type_changed": {c: [prev[c], types[c]] for c in set(prev) & set(types) if prev[c] != types[c]}}


def register_views() -> None:
    """warehouse.duckdb: views over silver + bronze for DBeaver / notebooks."""
    con = duckdb.connect(str(SETTINGS.warehouse))
    con.execute("CREATE SCHEMA IF NOT EXISTS silver; CREATE SCHEMA IF NOT EXISTS bronze")
    for layer in ("silver", "bronze"):
        for p in sorted((SETTINGS.data_dir / layer).glob("*.parquet")):
            con.execute(f"CREATE OR REPLACE VIEW {layer}.{q(p.stem)} AS SELECT * FROM read_parquet({lit(str(p.resolve()))})")
    con.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build bronze + silver layers")
    ap.add_argument("--tables", nargs="*")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--memory-limit", default="8GB")
    a = ap.parse_args(argv)
    SETTINGS.ensure_dirs()
    contracts = load_contracts()
    groups = files_by_table()
    if a.tables:
        groups = {t: v for t, v in groups.items() if t in set(a.tables)}
    if not groups:
        print("No downloaded files found. Run `make download` (or download --sample-files 3) first.")
        return 1
    unknown = sorted(set(groups) - set(contracts))
    if unknown:
        print(f"WARNING: tables without a contract (processed, not validated): {unknown}")

    con = connect()
    con.execute(f"SET memory_limit='{a.memory_limit}'")
    con.execute(f"SET temp_directory='{SETTINGS.state / 'duckdb_tmp'}'")
    for table, recs in sorted(groups.items()):
        state_p = SETTINGS.state / f"silver_{table}.json"
        fp = fingerprint(recs)
        if not a.force and state_p.exists() and json.loads(state_p.read_text()).get("fingerprint") == fp:
            print(f"[skip] {table}: inputs unchanged")
            continue
        t0 = time.time()
        b = build_bronze(con, table, recs)
        s = build_silver(con, table, contracts.get(table))
        s.update(bronze=b, fingerprint=fp, drift=schema_drift(table, s["types"]),
                 built_at=datetime.now(timezone.utc).isoformat(), seconds=round(time.time() - t0, 1))
        state_p.write_text(json.dumps(s, indent=1, default=str))
        print(f"[ok]   {table}: {b['files']} files, bronze {s['bronze_rows']:,} -> silver {s['silver_rows']:,} "
              f"(exact dups {s['exact_duplicates']:,}, pk conflicts {s['pk_conflict_rows']}, "
              f"null pk {s['null_pk_rows']:,}) in {s['seconds']}s")
    con.close()
    register_views()
    print(f"warehouse: {SETTINGS.warehouse}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
