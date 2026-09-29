# Aureliano — Factored AI & Data Hackathon 2026

Sistema de atención al cliente bancario AI-first para el workflow de **información y elegibilidad de crédito**, construido sobre el dataset LATAM Bank.

> En construcción. Deadline: 2026-10-05, 23:59. Plan de trabajo: [docs/PLAN.md](docs/PLAN.md).

## Principios
- El LLM conversa; los números los calcula código determinista y cada cifra se verifica contra el output de una herramienta.
- Riesgo predictivo (modelo aprendido) y política de elegibilidad (reglas versionadas) están separados de la conversación.
- Permisos y autenticación se aplican en la capa de servicio, no en el prompt.
- Ante duda, datos faltantes o casos borderline: handoff estructurado a un humano.

## Código reutilizado
Algunas piezas genéricas (motor de amortización, audit log append-only, cliente LLM) provienen de un proyecto previo del equipo y se declaran explícitamente aquí cuando se incorporen.

## Setup
Requiere Python ≥ 3.11, [uv](https://docs.astral.sh/uv/) y `make`.

```bash
make setup    # crea .venv, instala dependencias y .env desde .env.example
```

Completa `.env` (API key de Anthropic + credenciales read-only del Data Dictionary PDF). **Nunca** subas credenciales al repositorio.

## Pipeline de datos (`src/lbank`)
Descarga incremental desde S3 y capas bronze/silver sobre DuckDB, con contratos de datos (`contracts/tables.yml`) derivados del data dictionary oficial.

```
S3 ──download (manifest, ETag-incremental)──► data/raw/…               tal como se entrega
   ──pipeline──────────────────────────────► data/bronze/<t>.parquet   todo VARCHAR + lineage
                                             data/silver/<t>.parquet   tipado, limpio, 1 fila / PK
   ──dq────────────────────────────────────► reports/data_quality.md
   ──eda───────────────────────────────────► reports/eda_contact_center.md
                                             data/warehouse.duckdb     vistas silver.*, bronze.*
```

| comando | qué hace |
|---|---|
| `make check` | verifica credenciales y lista tablas/tamaños del bucket (sin descargar) |
| `make sample` | primeros 3 archivos por tabla → bronze → silver → DQ → EDA |
| `make download` | descarga incremental: solo objetos nuevos/cambiados (re-ejecutar para late arrivals) |
| `make pipeline` | raw → bronze → silver; omite tablas cuyos inputs no cambiaron |
| `make all` | download + pipeline + dq + eda |
| `make fixture-test` | test offline end-to-end con fixture sintético (late arrival, re-entrega corregida, columna nueva) |

`uv run python -m lbank dq --strict` sale con código ≠ 0 ante fallas de nivel error (para CI). Consultas: `uv run duckdb data/warehouse.duckdb`.

### Versionado de datos (DVC)
`dvc.yaml` define la cadena `download → pipeline → dq → eda`; `make repro` (= `dvc repro`) la ejecuta y `dvc.lock` fija el hash de `data/raw`, `data/bronze` y `data/silver` en cada commit. Las salidas son `persist` (DVC no las borra; la descarga sigue siendo incremental) y `download` es `always_changed` para detectar late arrivals en S3. Volver a una versión: `git checkout <commit> && dvc checkout`. 

**Remote (Google Drive).** `dvc push` / `dvc pull` usan la carpeta compartida del equipo (default remote `gdrive`). Cada miembro necesita acceso a la carpeta, estar en la lista de test users del cliente OAuth y configurar localmente (no se commitea, va a `.dvc/config.local`):

```bash
uv run dvc remote modify --local gdrive gdrive_client_id '<CLIENT_ID>'
uv run dvc remote modify --local gdrive gdrive_client_secret '<CLIENT_SECRET>'
uv run dvc pull     # primera vez abre el login de Google en el navegador
```

Pide el client ID/secret por un canal privado. Con el consent screen en modo Testing el token expira cada 7 días (vuelve a pedir login).

`data/` (~7 GB) no se versiona en git. El pipeline proviene del setup de datos previo del equipo para este hackathon.
