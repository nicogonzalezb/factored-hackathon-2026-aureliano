"""First-pass demand analysis to choose the workflow (problem statement §1).

Answers: which contact reasons drive volume, which fail first-contact
resolution / get escalated / hurt CSAT, how that differs by country and channel,
what the complaints backlog looks like, and what language coverage the
transcripts actually give us (the brief requires Spanish AND Portuguese).

Writes reports/eda_contact_center.md. Every query is plain SQL over the
warehouse views, so you can re-run any block in DBeaver or a notebook.
"""
from __future__ import annotations

from .config import SETTINGS
from .pipeline import connect, lit

SECTIONS: list[tuple[str, str, str]] = [
    ("Contact reasons: volume, resolution, escalation", "call_center_interactions", """
        SELECT reason_category, contact_reason,
               count(*) AS contacts,
               round(100.0*count(*)/sum(count(*)) OVER (), 2) AS pct_volume,
               round(100.0*avg(CAST(was_resolved AS INT)), 1) AS fcr_pct,
               round(100.0*avg(CAST(was_escalated AS INT)), 1) AS escalated_pct,
               round(100.0*avg(CAST(requires_followup AS INT)), 1) AS followup_pct,
               round(100.0*avg(CASE WHEN detected_sentiment IN ('Negative','Very Negative') THEN 1 ELSE 0 END), 1) AS neg_sent_pct,
               round(median(duration_seconds)/60.0, 1) AS median_handle_min,
               round(median(wait_time_seconds)/60.0, 1) AS median_wait_min
        FROM call_center_interactions
        GROUP BY ALL ORDER BY contacts DESC LIMIT 30"""),
    ("Reason category by country", "call_center_interactions", """
        SELECT c.country, i.reason_category, count(*) AS contacts,
               round(100.0*avg(CAST(i.was_resolved AS INT)),1) AS fcr_pct,
               round(100.0*avg(CAST(i.was_escalated AS INT)),1) AS escalated_pct
        FROM call_center_interactions i LEFT JOIN customers c USING (customer_id)
        GROUP BY ALL ORDER BY 1, 3 DESC"""),
    ("Channel mix", "call_center_interactions", """
        SELECT channel, interaction_type, count(*) AS contacts,
               round(100.0*avg(CAST(was_resolved AS INT)),1) AS fcr_pct,
               round(median(wait_time_seconds)/60.0,1) AS median_wait_min
        FROM call_center_interactions GROUP BY ALL ORDER BY contacts DESC"""),
    ("Monthly volume by reason category", "call_center_interactions", """
        PIVOT (SELECT strftime(date_trunc('month', CAST(interaction_date AS TIMESTAMP)), '%Y-%m') AS month,
                      reason_category FROM call_center_interactions)
        ON reason_category USING count(*) ORDER BY month"""),
    ("CSAT / NPS by contact reason", "satisfaction_surveys", """
        SELECT i.contact_reason, s.survey_type, count(*) AS surveys,
               round(avg(s.main_score), 2) AS avg_score,
               round(100.0*avg(CASE WHEN s.nps_category='Detractor' THEN 1 ELSE 0 END),1) AS detractor_pct
        FROM satisfaction_surveys s JOIN call_center_interactions i USING (interaction_id)
        GROUP BY ALL HAVING count(*) >= 30 ORDER BY avg_score ASC LIMIT 25"""),
    ("Complaints (PQR): category, SLA, resolution", "complaints", """
        SELECT case_type, category, count(*) AS cases,
               round(100.0*avg(CAST(sla_breached AS INT)),1) AS sla_breached_pct,
               round(median(resolution_days),1) AS median_resolution_days,
               round(100.0*avg(CASE WHEN status IN ('Escalated') THEN 1 ELSE 0 END),1) AS escalated_pct,
               round(100.0*avg(CAST(is_repeat_complainer AS INT)),1) AS repeat_pct
        FROM complaints GROUP BY ALL ORDER BY cases DESC LIMIT 25"""),
    ("Transcript language / accent coverage", "call_transcripts", """
        SELECT detected_language, detected_accent, count(*) AS transcripts,
               round(avg(accent_confidence),2) AS avg_accent_conf,
               round(100.0*count(*)/sum(count(*)) OVER (),2) AS pct
        FROM call_transcripts GROUP BY ALL ORDER BY transcripts DESC"""),
    ("Most frequent transcript intents", "call_transcripts", """
        SELECT trim(intent) AS intent, count(*) AS n
        FROM (SELECT unnest(string_split(detected_intents, ',')) AS intent FROM call_transcripts
              WHERE detected_intents IS NOT NULL)
        GROUP BY 1 ORDER BY n DESC LIMIT 25"""),
    ("Transaction status / disputes signal", "transactions", """
        SELECT transaction_type, transaction_status, count(*) AS txns,
               round(100.0*avg(CAST(is_fraud AS INT)),3) AS fraud_pct
        FROM transactions GROUP BY ALL ORDER BY txns DESC LIMIT 25"""),
]


def md_table(cols, rows, max_rows=40) -> str:
    def fmt(v):
        if v is None:
            return ""
        if isinstance(v, float):
            return f"{v:,.2f}"
        if isinstance(v, int):
            return f"{v:,}"
        return str(v).replace("|", "/")
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in rows[:max_rows]]
    return "\n".join(out)


def main(argv=None) -> int:
    con = connect()
    silver = {p.stem for p in SETTINGS.silver.glob("*.parquet")}
    for t in silver:
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet({lit(str(SETTINGS.silver / f'{t}.parquet'))})")
    L = ["# Contact-center demand analysis (first pass)", "",
         "Silver layer, all history. Use this to pick and justify the workflow; "
         "re-run after full download.", ""]
    for title, needs, sql in SECTIONS:
        L += [f"## {title}", ""]
        if needs not in silver:
            L += [f"_skipped: `{needs}` not loaded_", ""]
            continue
        try:
            cur = con.execute(sql)
            cols = [d[0] for d in cur.description]
            L += [md_table(cols, cur.fetchall()), ""]
        except Exception as e:  # a missing column shouldn't kill the whole report
            L += [f"_query failed: {e}_", ""]
    out = SETTINGS.reports_dir / "eda_contact_center.md"
    out.write_text("\n".join(L))
    print(f"EDA -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
