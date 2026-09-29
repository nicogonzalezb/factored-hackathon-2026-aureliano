"""Offline end-to-end test on a clearly labelled SYNTHETIC TEST FIXTURE.

Not organizer data. It mimics the bucket layout and seeds the documented
data-quality problems so every pipeline branch is exercised:

  * exact duplicates, a primary-key conflict (older + newer version of a row)
  * null primary key, NOT NULL violation, out-of-enum value, out-of-range score
  * FK orphans, blank / 'null' strings
  * partitioned facts in both hive (year=/month=/day=) and positional (2024/01/05) layouts
  * CSV + Parquet mixed in one table

Round 2 then simulates an update: a late-arriving partition, a changed file,
and a new column (schema evolution). Asserts that only new/changed objects are
downloaded, only affected tables rebuild, and silver reflects the update.

Run:  make fixture-test   (or  uv run python tests/test_fixture.py)
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FX = HERE / "_fixture"
SRC = FX / "bucket"
ENV = {**os.environ, "DATA_DIR": str(FX / "data"), "REPORTS_DIR": str(FX / "reports"),
       "PYTHONPATH": str(ROOT / "src")}


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def run(*args) -> str:
    r = subprocess.run([sys.executable, "-m", "lbank", *args], env=ENV, cwd=ROOT,
                       capture_output=True, text=True)
    print(r.stdout, r.stderr, sep="")
    assert r.returncode == 0, f"lbank {args} failed"
    return r.stdout


def state(table: str) -> dict:
    return json.loads((FX / "data" / "_state" / f"silver_{table}.json").read_text())


def build_round1() -> None:
    write_csv(SRC / "branches.csv",
              ["branch_id", "branch_code", "branch_name", "branch_type", "address", "city", "state", "country",
               "geographic_zone", "phone", "opening_time", "closing_time", "has_atms", "has_teller_windows",
               "branch_opening_date", "branch_status"],
              [["BR001", "001", "Centro", "Main", "Cra 7", "Bogotá", "Cundinamarca", "Colombia", "Urban",
                "6011234", "08:00:00", "17:00:00", "true", "true", "2010-01-01", "Active"],
               ["BR002", "002", "Polanco", "Premium", "Av. Masaryk", "CDMX", "CDMX", "Mexico", "Urban",
                "5551234", "09:00:00", "18:00:00", "true", "false", "2012-05-01", "Active"]])
    cust_h = ["customer_id", "document_number", "document_type", "first_name", "last_name", "date_of_birth",
              "gender", "city", "state", "country", "segment", "credit_score", "registration_date",
              "registration_branch_id", "customer_status", "last_updated", "accepts_marketing"]
    base = ["1990-01-01", "M", "Bogotá", "Cundinamarca", "Colombia"]
    write_csv(SRC / "customers.csv", cust_h, [
        ["C001", "0012345", "CC", "Ana", "Gómez", *base, "Premium", "720", "2020-01-01 10:00:00", "BR001", "Active",
         "2026-01-01 00:00:00", "true"],
        ["C001", "0012345", "CC", "Ana", "Gómez", *base, "Premium", "720", "2020-01-01 10:00:00", "BR001", "Active",
         "2026-01-01 00:00:00", "true"],                                  # exact duplicate
        ["C002", "0099999", "CC", "Luis", "Pérez", *base, "Basic", "650", "2021-03-01 10:00:00", "BR001", "Active",
         "2025-06-01 00:00:00", "false"],                                 # older version
        ["C002", "0099999", "CC", "Luis", "Pérez", *base, "Plus", "680", "2021-03-01 10:00:00", "BR001", "Active",
         "2026-02-01 00:00:00", "false"],                                 # newer version -> wins
        ["C003", "CURP123", "CURP", "Sofía", "Ruiz", "1985-07-07", "F", "CDMX", "CDMX", "Mexico", "Gold", "900",
         "2022-01-01 10:00:00", "BR999", "Active", "2026-01-01 00:00:00", "true"],  # bad enum, range, FK orphan
        ["", "X1", "CC", "Nadie", "Null", *base, "Basic", "null", "2022-01-01 10:00:00", "BR001", "Active",
         "2026-01-01 00:00:00", "true"],                                  # null PK -> quarantine
        ["C004", "0044444", "CC", "", "Díaz", *base, "Student", "", "2023-01-01 10:00:00", "BR002", "Active",
         "2026-01-01 00:00:00", "true"],                                  # NOT NULL violation (first_name)
    ])
    write_csv(SRC / "service_agents.csv",
              ["agent_id", "employee_code", "first_name", "last_name", "email", "native_accent",
               "country_of_origin", "agent_type", "experience_level", "languages", "hire_date", "agent_status",
               "work_shift", "avg_csat"],
              [["A01", "E01", "Marta", "León", "m@b.co", "colombian", "Colombia", "Phone", "Senior", "es",
                "2019-01-01", "Active", "Morning", "4.5"]])
    ih = ["interaction_id", "interaction_date", "process_date", "customer_id", "agent_id", "interaction_type",
          "channel", "contact_reason", "reason_category", "duration_seconds", "wait_time_seconds", "was_resolved",
          "requires_followup", "detected_sentiment", "sentiment_score", "was_escalated", "has_transcript",
          "has_recording"]
    write_csv(SRC / "call_center_interactions/year=2026/month=01/day=05/part-000.csv", ih, [
        ["I1", "2026-01-05 09:00:00", "2026-01-05", "C001", "A01", "Inbound Call", "Phone", "Card blocked",
         "Technical", "300", "40", "true", "false", "Neutral", "0.1", "false", "true", "true"],
        ["I2", "2026-01-05 10:00:00", "2026-01-05", "C002", "A01", "Chat", "WhatsApp", "Unrecognized charge",
         "Complaint", "600", "90", "false", "true", "Negative", "-0.6", "true", "true", "false"],
        ["I3", "2026-01-02 11:00:00", "2026-01-05", "C999", "A01", "Chat", "Web Chat", "Balance inquiry",
         "Transactional", "120", "5", "true", "false", "Positive", "0.7", "false", "false", "false"],  # late + orphan
    ])
    write_csv(SRC / "call_center_interactions/year=2026/month=01/day=06/part-000.csv", ih, [
        ["I4", "2026-01-06 09:30:00", "2026-01-06", "C004", "A01", "Inbound Call", "Phone", "Unrecognized charge",
         "Complaint", "700", "120", "false", "true", "Very Negative", "-0.9", "true", "true", "true"],
    ])
    write_csv(SRC / "call_transcripts/2026/01/05/part-000.csv",
              ["transcript_id", "interaction_id", "process_date", "customer_id", "agent_id", "full_text",
               "detected_language", "detected_accent", "accent_confidence", "detected_intents",
               "transcription_model", "duration_seconds"],
              [["T1", "I1", "2026-01-05", "C001", "A01", "Hola, mi tarjeta está bloqueada", "es", "colombian",
                "0.91", "card_block,unlock", "Whisper", "300"],
               ["T2", "I2", "2026-01-05", "C002", "A01", "No reconozco este cobro", "es", "colombian", "0.88",
                "dispute_charge", "Whisper", "600"]])
    write_csv(SRC / "complaints/year=2026/month=01/day=06/part-000.csv",
              ["complaint_id", "creation_date", "process_date", "customer_id", "case_type", "category",
               "reception_channel", "description", "priority", "status", "sla_breached", "resolution_days",
               "is_repeat_complainer", "origin_interaction_id"],
              [["Q1", "2026-01-06 12:00:00", "2026-01-06", "C004", "Claim", "Unrecognized transaction", "Call Center",
                "Cobro no reconocido", "High", "Open", "false", "", "false", "I4"]])
    write_csv(SRC / "satisfaction_surveys/year=2026/month=01/day=06/part-000.csv",
              ["survey_id", "survey_date", "process_date", "interaction_id", "customer_id", "agent_id",
               "survey_type", "send_channel", "main_score", "nps_category"],
              [["S1", "2026-01-06 08:00:00", "2026-01-06", "I1", "C001", "A01", "CSAT", "SMS", "5", ""],
               ["S2", "2026-01-06 08:00:00", "2026-01-06", "I2", "C002", "A01", "NPS", "Email", "11", "Detractor"]])


def build_round2() -> None:
    import duckdb
    # late-arriving partition for an old day, written as parquet with a NEW column
    p = SRC / "call_center_interactions/year=2026/month=01/day=04/part-000.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    duckdb.sql("""SELECT 'I5' interaction_id, TIMESTAMP '2026-01-04 15:00:00' interaction_date,
                  DATE '2026-01-08' process_date, 'C001' customer_id, 'A01' agent_id,
                  'Inbound Call' interaction_type, 'Phone' channel, 'Card blocked' contact_reason,
                  'Technical' reason_category, 200 duration_seconds, 30 wait_time_seconds, true was_resolved,
                  false requires_followup, 'Neutral' detected_sentiment, 0.0 sentiment_score, false was_escalated,
                  false has_transcript, true has_recording, 'pt' customer_language""").write_parquet(str(p))
    # a corrected re-delivery of an existing day
    f = SRC / "call_center_interactions/year=2026/month=01/day=06/part-000.csv"
    f.write_text(f.read_text().replace("Very Negative", "Negative"))


def main() -> None:
    shutil.rmtree(FX, ignore_errors=True)
    build_round1()

    print("=== round 1 ===")
    out = run("download", "--source-dir", str(SRC))
    assert "8 new/changed" in out, out
    run("pipeline")
    c = state("customers")
    assert c["bronze_rows"] == 7 and c["exact_duplicates"] == 1, c
    assert c["null_pk_rows"] == 1 and c["pk_conflict_rows"] == 1 and c["silver_rows"] == 4, c
    assert c["types"]["document_number"] == "VARCHAR", "leading zeros must survive"
    assert c["types"]["credit_score"] == "BIGINT" and c["types"]["last_updated"] == "TIMESTAMP", c["types"]
    import duckdb
    seg = duckdb.sql(f"SELECT segment FROM '{FX}/data/silver/customers.parquet' WHERE customer_id='C002'").fetchone()
    assert seg[0] == "Plus", "latest version of C002 must win"
    assert state("call_center_interactions")["silver_rows"] == 4
    run("dq")
    dq = {r["table"]: {ch["check"]: ch for ch in r["checks"]}
          for r in json.loads((FX / "reports" / "dq_results.json").read_text())}
    assert dq["customers"]["enum: segment"]["failed"] == 1
    assert dq["customers"]["range: credit_score in [300, 850]"]["failed"] == 1
    assert dq["customers"]["not null: first_name"]["failed"] == 1
    assert dq["customers"]["fk: registration_branch_id -> branches.branch_id"]["failed"] == 1
    assert dq["call_center_interactions"]["fk: customer_id -> customers.customer_id"]["failed"] == 1
    assert dq["call_center_interactions"]["late arrivals (process_date > event date + 1d)"]["failed"] == 1
    assert dq["satisfaction_surveys"]["range: main_score in [0, 10]"]["failed"] == 1
    run("eda")
    assert "Unrecognized charge" in (FX / "reports" / "eda_contact_center.md").read_text()

    print("=== round 2: late arrival + corrected file + schema evolution ===")
    build_round2()
    out = run("download", "--source-dir", str(SRC))
    assert "2 new/changed" in out, out
    out = run("pipeline")
    assert "[skip] customers" in out and "[ok]   call_center_interactions" in out, out
    s = state("call_center_interactions")
    assert s["silver_rows"] == 5, s
    assert s["drift"]["added"] == ["customer_language"], s["drift"]
    sent = duckdb.sql(f"SELECT detected_sentiment FROM '{FX}/data/silver/call_center_interactions.parquet' "
                      f"WHERE interaction_id='I4'").fetchone()[0]
    assert sent == "Negative", "corrected re-delivery must replace the old value"
    run("dq")
    print("\nALL FIXTURE CHECKS PASSED")


if __name__ == "__main__":
    main()
