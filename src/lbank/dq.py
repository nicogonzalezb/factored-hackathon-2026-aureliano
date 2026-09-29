"""Data-quality report: contracts in contracts/tables.yml checked against silver.

Writes reports/data_quality.md (human) and reports/dq_results.json (machine).
`--strict` exits non-zero when any severity=error check fails (use in CI).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from .config import SETTINGS, load_contracts
from .pipeline import connect, lit, q


def pct(n, d):
    return None if not d else round(100.0 * n / d, 3)


def check_table(con, table: str, c: dict, silver_tables: set[str]) -> dict:
    path = SETTINGS.silver / f"{table}.parquet"
    src = f"read_parquet({lit(str(path))})"
    cols = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()}
    n = con.execute(f"SELECT count(*) FROM {src}").fetchone()[0]
    st_p = SETTINGS.state / f"silver_{table}.json"
    stats = json.loads(st_p.read_text()) if st_p.exists() else {}
    checks: list[dict] = []

    def add(name, severity, failed, total, detail=None):
        checks.append({"check": name, "severity": severity, "failed": int(failed or 0), "total": int(total or 0),
                       "pct": pct(failed or 0, total), "status": "pass" if not failed else
                       {"error": "fail", "warn": "warn"}.get(severity, "info"), "detail": detail})

    referenced = set(c.get("pk", [])) | set(c.get("not_null", [])) | set(c.get("enums", {})) | \
        set(c.get("ranges", {})) | set(c.get("fks", {})) | set(c.get("unique", []))
    missing = sorted(referenced - set(cols))
    add("schema: contract columns present", "error", len(missing), len(referenced), missing or None)

    exp = c.get("expected_rows")
    if exp:
        off = abs(n - exp) / exp
        add("row count within 10% of documented", "warn", int(off > 0.10), 1, {"silver": n, "documented": exp})

    b = stats.get("bronze_rows", n)
    add("exact duplicate rows (removed)", "info", stats.get("exact_duplicates", 0), b)
    add("primary-key conflicts (resolved: latest wins)", "warn", stats.get("pk_conflict_rows") or 0, b)
    add("null primary key (quarantined)", "error", stats.get("null_pk_rows", 0), b)

    for col in c.get("not_null", []):
        if col in cols:
            k = con.execute(f"SELECT count(*) FILTER (WHERE {q(col)} IS NULL) FROM {src}").fetchone()[0]
            add(f"not null: {col}", "error", k, n)
    for col in c.get("unique", []):
        if col in cols:
            k = con.execute(f"SELECT coalesce(sum(k-1),0) FROM (SELECT count(*) k FROM {src} "
                            f"WHERE {q(col)} IS NOT NULL GROUP BY {q(col)} HAVING count(*)>1)").fetchone()[0]
            add(f"unique: {col}", "error", k, n)
    for col, allowed in (c.get("enums") or {}).items():
        if col in cols:
            al = ",".join(lit(str(v)) for v in allowed)
            rows = con.execute(f"SELECT CAST({q(col)} AS VARCHAR) v, count(*) FROM {src} WHERE {q(col)} IS NOT NULL "
                               f"AND CAST({q(col)} AS VARCHAR) NOT IN ({al}) GROUP BY 1 ORDER BY 2 DESC").fetchall()
            add(f"enum: {col}", "warn", sum(r[1] for r in rows), n, {r[0]: r[1] for r in rows[:8]} or None)
    for col, (lo, hi) in (c.get("ranges") or {}).items():
        if col in cols and cols[col] in ("BIGINT", "DOUBLE", "INTEGER", "DECIMAL"):
            cond = " OR ".join(x for x in [f"{q(col)} < {lo}" if lo is not None else "",
                                           f"{q(col)} > {hi}" if hi is not None else ""] if x)
            k = con.execute(f"SELECT count(*) FROM {src} WHERE {cond}").fetchone()[0]
            add(f"range: {col} in [{lo}, {hi}]", "warn", k, n)
    for col, ref in (c.get("fks") or {}).items():
        ptab, pcol = ref.split(".")
        if col in cols and ptab in silver_tables:
            psrc = f"read_parquet({lit(str(SETTINGS.silver / f'{ptab}.parquet'))})"
            k, nn = con.execute(f"""SELECT count(*) FILTER (WHERE p.{q(pcol)} IS NULL), count(*)
                FROM {src} t LEFT JOIN (SELECT DISTINCT {q(pcol)} FROM {psrc}) p
                ON CAST(t.{q(col)} AS VARCHAR) = CAST(p.{q(pcol)} AS VARCHAR)
                WHERE t.{q(col)} IS NOT NULL""").fetchone()
            add(f"fk: {col} -> {ref}", "warn", k, nn)

    extra: dict = {"rows": n, "columns": cols}
    ev = c.get("event_ts")
    if ev in cols and "process_date" in cols:
        r = con.execute(f"""
            SELECT min({q(ev)}), max({q(ev)}),
                   quantile_cont(lag, 0.5), quantile_cont(lag, 0.95), max(lag),
                   count(*) FILTER (WHERE lag > 1), count(*) FILTER (WHERE lag < 0), count(lag)
            FROM (SELECT {q(ev)}, date_diff('day', CAST({q(ev)} AS DATE), CAST(process_date AS DATE)) lag FROM {src})
        """).fetchone()
        extra["event_range"] = [str(r[0]), str(r[1])]
        extra["late_arrival"] = {"lag_days_p50": r[2], "lag_days_p95": r[3], "lag_days_max": r[4],
                                 "rows_processed_>1_day_late": r[5], "rows_processed_before_event": r[6]}
        add("late arrivals (process_date > event date + 1d)", "info", r[5], r[7])
        add("process_date before event date", "warn", r[6], r[7])

    nulls = con.execute("SELECT " + ", ".join(f"count(*) FILTER (WHERE {q(k)} IS NULL)" for k in cols)
                        + f" FROM {src}").fetchone()
    extra["null_pct"] = {k: pct(v, n) for k, v in zip(cols, nulls)}
    extra["drift"] = stats.get("drift")
    return {"table": table, "checks": checks, **extra}


def render(results: list[dict]) -> str:
    L = ["# Data quality report", "",
         f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} from `data/silver`, "
         f"contracts `contracts/tables.yml`.", "",
         "| table | rows | errors | warnings | exact dups removed | pk conflicts | late >1d |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for r in results:
        ch = {c["check"]: c for c in r["checks"]}
        e = sum(c["status"] == "fail" for c in r["checks"])
        w = sum(c["status"] == "warn" for c in r["checks"])
        late = next((c for c in r["checks"] if c["check"].startswith("late arrivals")), None)
        L.append(f"| {r['table']} | {r['rows']:,} | {e} | {w} | "
                 f"{ch['exact duplicate rows (removed)']['failed']:,} | "
                 f"{ch['primary-key conflicts (resolved: latest wins)']['failed']:,} | "
                 f"{'' if not late else str(late['pct']) + '%'} |")
    for r in results:
        L += ["", f"## {r['table']}", ""]
        if r.get("event_range"):
            L.append(f"Event range: {r['event_range'][0]} → {r['event_range'][1]}  ")
            L.append(f"Late arrival: `{json.dumps(r['late_arrival'], default=str)}`  ")
        if r.get("drift") and not r["drift"].get("first_run"):
            L.append(f"Schema drift vs previous run: `{json.dumps(r['drift'])}`  ")
        bad = [c for c in r["checks"] if c["status"] != "pass"]
        if bad:
            L += ["", "| status | check | failed | total | % | detail |", "|---|---|---:|---:|---:|---|"]
            for c in bad:
                d = "" if c["detail"] is None else json.dumps(c["detail"], ensure_ascii=False, default=str)[:160]
                L.append(f"| {c['status']} | {c['check']} | {c['failed']:,} | {c['total']:,} | {c['pct']} | {d} |")
        else:
            L.append("All checks pass.")
        top = sorted(((k, v) for k, v in r["null_pct"].items() if v and not k.startswith("_")),
                     key=lambda kv: -kv[1])[:8]
        if top:
            L.append("")
            L.append("Highest null %: " + ", ".join(f"`{k}` {v}%" for k, v in top))
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args(argv)
    contracts = load_contracts()
    silver = {p.stem for p in SETTINGS.silver.glob("*.parquet")}
    if not silver:
        print("No silver tables. Run `make pipeline` first.")
        return 1
    con = connect()
    results = [check_table(con, t, contracts.get(t, {}), silver) for t in sorted(silver)]
    SETTINGS.reports_dir.mkdir(exist_ok=True)
    (SETTINGS.reports_dir / "dq_results.json").write_text(json.dumps(results, indent=1, default=str))
    (SETTINGS.reports_dir / "data_quality.md").write_text(render(results))
    errors = sum(c["status"] == "fail" for r in results for c in r["checks"])
    warns = sum(c["status"] == "warn" for r in results for c in r["checks"])
    print(f"DQ: {len(results)} tables, {errors} failing error checks, {warns} warnings "
          f"-> reports/data_quality.md")
    return 1 if (a.strict and errors) else 0


if __name__ == "__main__":
    raise SystemExit(main())
