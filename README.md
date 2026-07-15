# MEMS — Metrology Experiment Management System

A FastAPI backend for managing research projects, experiments, datasets, and analysis results for impedance metrology data — built on real measurement data from an automated AH2700A capacitance bridge suite.

## Live Demo
 
**API:** https://mems-production-5542.up.railway.app
**Interactive docs:** https://mems-production-5542.up.railway.app/docs
 
(Free-tier hosting — the first request after a period of inactivity may take a few seconds to wake up.)

## Desktop Client

A native desktop GUI, built with **PySide6 (Qt)**, sits on top of the API — full CRUD across all four resources through a real macOS/Windows/Linux application instead of `/docs`.

```
gui/
├── main.py            # window + tab wiring, applies the shared stylesheet
├── api_client.py       # thin requests wrapper around every backend endpoint
├── styles.py             # shared QSS stylesheet (fonts, headers, buttons, tables)
├── projects_tab.py         # Project CRUD
├── experiments_tab.py       # Experiment CRUD, cascading from a project dropdown
├── datasets_tab.py           # CSV upload (native file picker) + Dataset CRUD
└── analysis_tab.py             # Run analysis, view the full nested report as a tree, delete results
```

Run it:
```bash
cd gui
python main.py
```
By default it points at the live Railway deployment (`MEMS_API_URL` in `.env`); unset that variable, or point it at `http://127.0.0.1:8000`, to run against a local `uvicorn` instance instead.

Building this surfaced one real gap in the API — `DELETE /analysis/{dataset_id}` didn't exist even in `/docs`, since the original design only ever needed `run`/`get`/`list`. It was added specifically because the GUI's delete-button parity required it, and is now part of the documented API surface below.

## What it does

An automated instrumentation suite (AH2700A capacitance bridge + dielectric test fixture + thermo-hygrometer, driven over PyVISA/SCPI) collects overnight measurement runs and saves them as CSV files. MEMS is the layer on top: it organizes that data into projects and experiments, stores uploaded CSVs, and runs statistical analysis on them — all through a REST API instead of manually opening spreadsheets.

**Example:** instead of manually opening 15 CSVs to find "mean Cp for June experiments at 10kHz," it's one API call.

## Tech stack

| Tool | Role |
|---|---|
| FastAPI | HTTP layer — receives requests, returns JSON |
| SQLAlchemy | ORM — Python classes mapped to SQL tables |
| SQLite | Database (single file, no server process) |
| Pydantic | Request/response validation |
| Pandas | CSV loading, cleaning, statistics |
| Uvicorn | ASGI server |
| PySide6 | Desktop GUI (Qt) |
| requests | HTTP client used by the desktop GUI |

## Data model

```
Projects ──< Experiments ──< Datasets ──< Analysis
```
One project has many experiments. One experiment has many datasets. One dataset has exactly one analysis result.

| Table | Key fields |
|---|---|
| **Project** | `name`, `desc` |
| **Experiment** | `project_id`, `title`, `instrument`, `freq`, `voltage`, `notes` |
| **Dataset** | `experiment_id`, `filename`, `filepath` |
| **Analysis** | `dataset_id`, `mean_cp`, `std_dev`, `mean_loss`, `correlation`, `expanded_u` |

**Cascade delete:** deleting a Project removes all its Experiments, which removes their Datasets, which removes their Analysis results (SQLAlchemy `cascade="all, delete-orphan"`). This is standard REST behavior and keeps the API simple, but it's a deliberate tradeoff — a production system protecting irreplaceable research data would more likely use soft deletes or a confirmation step before a destructive cascade like this.

## Project structure
 
```
mems/
├── database.py          # engine, session, Base, get_db()
├── models.py             # SQLAlchemy table classes
├── schemas.py             # Pydantic request/response models
├── main.py                 # FastAPI app entry point, router registration
├── routers/
│   ├── projects.py          # Project CRUD
│   ├── experiments.py       # Experiment CRUD (linked to Project)
│   ├── datasets.py           # CSV upload + Dataset CRUD
│   └── analysis.py            # Stats computation + Analysis CRUD
├── tests/
│   ├── conftest.py            # isolated test database + fixtures
│   └── test_pipeline.py        # full pipeline + edge case tests
├── test_data/                    # sample CSV for running the pipeline without real lab data
├── uploaded_datasets/              # uploaded CSVs (gitignored)
├── .env                              # DATABASE_URL, UPLOAD_DIR, MEMS_API_URL (gitignored)
├── railway.json                        # Railway deployment config
├── gui/                                   # PySide6 desktop client (see Desktop Client section above)
└── requirements.txt
```

## API endpoints

**Projects** — `POST /projects` · `GET /projects` · `GET /projects/{id}` · `PUT /projects/{id}` · `DELETE /projects/{id}`

**Experiments** — `POST /experiments` · `GET /experiments` · `GET /experiments/by-project/{project_id}` · `GET /experiments/{id}` · `PUT /experiments/{id}` · `DELETE /experiments/{id}`

**Datasets** — `POST /datasets/upload` (multipart CSV upload) · `GET /datasets` · `GET /datasets/by-experiment/{experiment_id}` · `GET /datasets/{id}` · `DELETE /datasets/{id}`

**Analysis** — `POST /analysis/run/{dataset_id}` · `GET /analysis/{dataset_id}` · `GET /analysis` · `DELETE /analysis/{dataset_id}`

All `GET` list endpoints (`/projects`, `/experiments`, `/datasets`, `/analysis`) support `?skip=` and `?limit=` query params for pagination (default `limit=100`).

Full interactive documentation is auto-generated at `/docs` when the server is running.

## What the analysis engine does

On `POST /analysis/run/{dataset_id}`:
1. Loads the dataset's CSV via pandas
2. Drops instrument warm-up rows (`Humidity (%) == 0.0`, present on the first reading before the sensor settles)
3. Computes `mean_cp`, `std_dev` (capacitance), `mean_loss`, and the correlation between capacitance and relative humidity
4. Computes expanded uncertainty at a k=2 coverage factor
5. Stores the result, overwriting any prior analysis for that dataset rather than duplicating it

## Setup
 
```bash
cd mems
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Create a `.env` file in the project root:
```
DATABASE_URL=sqlite:///./mems.db
UPLOAD_DIR=uploaded_datasets
```
```bash
uvicorn main:app --reload
```
Then open `http://127.0.0.1:8000/docs`.

## Testing
 
An automated `pytest` suite covers the full pipeline (project → experiment → upload → analysis → report) plus known edge cases — missing/invalid IDs, non-CSV uploads, empty CSVs, and zero-variance data that would otherwise crash the correlation calculation.
 
```bash
pytest -v
```
Tests run against a separate, isolated SQLite database (`test.db`) — never against your real `mems.db`.
 
A trimmed sample CSV (10 rows from a real measurement run, including the instrument warm-up row) is included at `test_data/` so the full pipeline can be exercised without needing real lab data.

## Status
 
Built as a 6-day sprint (July 8-14, 2026), following on from the AH2700A automation suite built during a CSIR-NPL research internship. Hardened and deployed in a follow-up pass.
 
**Core build**
- [x] Project setup, database + ORM layer
- [x] Project CRUD
- [x] Experiment CRUD, linked to Project
- [x] CSV upload + Dataset CRUD
- [x] Analysis engine — verified end-to-end against real CSIR-NPL measurement data
- [x] Reporting endpoint (full project → experiment → dataset → analysis rollup)
**Hardening**
- [x] Configuration externalized to `.env`
- [x] Pagination on all list endpoints
- [x] Cascade delete, with documented tradeoff
- [x] Edge cases handled: empty/malformed CSVs, zero-variance data, missing columns
**Testing & deployment**
- [x] Automated `pytest` suite, including regression tests for bugs found during hardening
- [x] Deployed live on Railway with persistent volume storage

**Desktop GUI**
- [x] PySide6 client with four tabs, full CRUD parity with the API (including a new `DELETE /analysis/{id}` endpoint added specifically to close the gap)
- [x] Native file picker for CSV upload, tree view for the nested project report
- [x] Shared QSS stylesheet across the whole app
- [x] Connected to the live Railway deployment via `.env`, not hardcoded to localhost

## Why this project

- Built on real metrological measurement data, not a generic CRUD demo
- A domain-specific scientific data backend — the kind of problem instrumentation/metrology companies (Keysight, NI, Tektronix) actually solve internally
- A learning project for FastAPI, SQLAlchemy, and REST API design principles