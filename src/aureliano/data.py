"""Acceso al dataset LATAM Bank directamente en S3 vía DuckDB, sin descargarlo.

Uso:
    from aureliano.data import connect, partitioned
    con = connect()                                   # vistas: customers, products, ...
    con.sql("SELECT count(*) FROM products").show()
    rel = partitioned(con, "complaints", year=2026, month=6)   # solo lee ese mes
    rel.aggregate("count(*)").show()

Las tablas particionadas (~1.100 CSV diarios cada una) se leen acotando year/month:
recorrerlas enteras desde S3 es lento. Para análisis repetidos, materializa el
resultado a Parquet local con `rel.write_parquet("data/x.parquet")`.
"""
import os
from pathlib import Path

import duckdb
from dotenv import load_dotenv

SINGLE_FILE = ["customers", "products", "branches", "service_agents",
               "marketing_campaigns", "daily_exchange_rates"]
PARTITIONED = ["transactions", "digital_events", "call_center_interactions",
               "call_transcripts", "complaints", "satisfaction_surveys", "campaign_sends"]


def _base() -> str:
    return os.environ["DATASET_S3_URI"].rstrip("/")


def connect(db_path: str = ":memory:") -> duckdb.DuckDBPyConnection:
    """Conexión DuckDB autenticada contra S3, con vistas para las tablas de un solo archivo."""
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    con = duckdb.connect(db_path)
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(
        "CREATE OR REPLACE SECRET s3_latam (TYPE s3, KEY_ID ?, SECRET ?, REGION ?)",
        [os.environ["AWS_ACCESS_KEY_ID"], os.environ["AWS_SECRET_ACCESS_KEY"], os.environ["AWS_REGION"]],
    )
    for t in SINGLE_FILE:
        con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_csv_auto('{_base()}/{t}.csv')")
    return con


def partitioned(con: duckdb.DuckDBPyConnection, table: str,
                year: int | str = "*", month: int | str = "*", day: int | str = "*") -> duckdb.DuckDBPyRelation:
    """Relación sobre una tabla particionada, leyendo solo las particiones pedidas."""
    if table not in PARTITIONED:
        raise ValueError(f"{table} no es particionada; usa la vista directamente")
    fmt = lambda v: v if v == "*" else f"{int(v):02d}"
    glob = f"{_base()}/{table}/year={year}/month={fmt(month)}/day={fmt(day)}/*.csv"
    # union_by_name: el dataset declara schema evolution entre particiones
    return con.sql(f"SELECT * FROM read_csv_auto('{glob}', hive_partitioning=true, union_by_name=true)")
