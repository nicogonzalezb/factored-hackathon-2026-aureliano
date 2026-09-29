PY ?= uv run python

.PHONY: setup check list sample download pipeline dq eda all fixture-test repro

setup:            ## create venv + install deps (needs uv: https://docs.astral.sh/uv/)
	uv sync --extra analysis --extra dev
	@test -f .env || (cp .env.example .env && echo ">> created .env - fill ANTHROPIC_API_KEY and the AWS keys from the Data Dictionary PDF")

check:            ## verify credentials + bucket access (no download)
	$(PY) -m lbank download --list | tail -25

list:             ## full bucket inventory per table
	$(PY) -m lbank download --list

sample:           ## quick start: first 3 files per table, then build everything
	$(PY) -m lbank download --sample-files 3
	$(PY) -m lbank all

download:         ## full incremental download (re-run to pick up late arrivals)
	$(PY) -m lbank download

pipeline:         ## raw -> bronze -> silver (skips unchanged tables)
	$(PY) -m lbank pipeline

dq:               ## data-quality report -> reports/data_quality.md
	$(PY) -m lbank dq

eda:              ## demand analysis -> reports/eda_contact_center.md
	$(PY) -m lbank eda

all: download pipeline dq eda

fixture-test:     ## offline end-to-end test incl. late arrival + schema evolution
	$(PY) tests/test_fixture.py

repro:            ## versioned run: download -> pipeline -> dq -> eda, hashes pinned in dvc.lock
	uv run dvc repro
