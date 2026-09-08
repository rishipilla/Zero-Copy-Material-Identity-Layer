# Zero-Copy Material Identity Layer

> Intelligent material deduplication and identity resolution across multiple enterprise source systems.

## Overview

Enterprise organizations often maintain the same physical material across multiple systems such as SAP, Oracle, ERP databases, spreadsheets, and legacy applications.

The same material may appear under different descriptions:

- `SS hex bolt M10 x 50 mm DIN 933`
- `Stainless Steel Hex Bolt 10mm x 50mm DIN933`
- `M10-50 SS HEX BOLT DIN 933`

Traditional data cleansing approaches modify or copy the original source records, making traceability difficult.

### Our approach

The **Zero-Copy Material Identity Layer** creates a canonical identity layer **without modifying the original source records**.

It:

1. Ingests material records
2. Normalizes descriptions
3. Extracts important attributes
4. Generates semantic similarity scores
5. Compares structured attributes
6. Applies business/rule-based validation
7. Produces match decisions
8. Groups confirmed matches into canonical identities
9. Creates an identity graph in Neo4j

The result is:

```
Multiple source records
        ↓
Normalization
        ↓
Semantic + Attribute + Rule Matching
        ↓
Canonical Material Identity
        ↓
Graph Representation
```

##  Problem Statement

Large organizations frequently have duplicate material records across different source systems.

For example:

| Source | Material Description |
|---|---|
| SAP | SS hex bolt M10 x 50 mm DIN 933 |
| SAP | Stainless Steel Hex Bolt 10mm x 50mm DIN933 |
| Oracle | M10-50 SS HEX BOLT DIN 933 |

Although the descriptions differ, all three records refer to the same physical material.

This causes:

- Duplicate material records
- Poor procurement visibility
- Incorrect inventory analysis
- Difficulty consolidating supplier information
- Inconsistent reporting
- Increased operational cost

## Solution

The Zero-Copy Material Identity Layer solves this by separating:

**Source Material Records** — The original records remain unchanged.

**Canonical Material Identity** — A derived identity represents the real-world material.

For example:

```
                    ┌─────────────────────────────┐
                    │ Canonical Material Identity  │
                    │ SS Hex Bolt M10 x 50 DIN933  │
                    └──────────────┬───────────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                │
                  ▼                ▼                ▼
             SAP 100001       SAP 100002      Oracle MT-7788
```

This provides traceability while avoiding modification of the original source records.

##  Architecture

The Zero-Copy Material Identity Layer keeps source ERP and CSV records as the read-only truth while deriving a canonical identity layer on top of them.

```text
                    ┌────────────────────────────────────────────┐
                    │ ERP / CSV Sources                          │
                    │ SAP / Oracle / sample CSV                  │
                    └─────────────────┬────────────────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────────────┐
                    │ Material Ingestion                         │
                    │ FastAPI / app/services/importer.py         │
                    │ POST /api/materials/import                 │
                    │ POST /api/materials/import-sample          │
                    └─────────────────┬────────────────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────────────┐
                    │ Normalization + Attribute Extraction       │
                    │ normalize.py + extract.py                  │
                    │ Raw source descriptions stay unchanged     │
                    └─────────────────┬────────────────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────────────┐
                    │ Hybrid Matching Engine                     │
                    │ matching.py                                │
                    │ semantic + attribute + rule signals       │
                    └─────────────────┬────────────────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────────────┐
                    │ Match Decision                             │
                    │ pending / accepted / rejected / conflict   │
                    └─────────────────┬────────────────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────────────┐
                    │ Canonical Material Identity Layer          │
                    │ PostgreSQL source-of-truth                 │
                    │ Material + Identity + Match tables          │
                    └─────────────────┬────────────────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────────────┐
                    │ Neo4j Identity Graph                        │
                    │ identity graph mirror for accepted records │
                    └─────────────────┬────────────────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────────────┐
                    │ React Dashboard                             │
                    │ Vite + React frontend                      │
                    └────────────────────────────────────────────┘
```

The flow is intentionally source-preserving: ERP and CSV records are imported into the FastAPI ingestion API, normalized and enriched with extracted attributes, then compared by the matching service before the match decision is recorded. Confirmed matches become material identities in PostgreSQL and are projected into the Neo4j identity graph for the React dashboard.

The committed sample dataset ships three supported synthetic ERP source systems in the import path (`SAP-A`, `SAP-B`, and `LEGACY-ERP`). It includes a three-way duplicate example group for the stainless fastener bolt family, a hydraulic hose group, and a welding electrode group. The route intentionally imports the sample rows idempotently so the local workflow remains safe and source-preserving while showing cross-source three-way identity evidence.

## 🚀 One-Command Local Startup

A beginner-friendly Windows PowerShell launcher is included in this repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\demo.ps1
```

Prerequisites:

- Docker Desktop / Docker Compose v2 available on `PATH`
- Python backend environment available, or the repository system Python can start the backend
- Node.js and npm available for the frontend

What the command does:

1. Checks for Docker and Docker Compose availability.
2. Starts the existing PostgreSQL and Neo4j containers from [docker-compose.yml](docker-compose.yml).
3. Waits for PostgreSQL and Neo4j ports to answer.
4. Starts the FastAPI backend locally with the repository's existing `uvicorn app.main:app` command when port `8000` is not already occupied.
5. Starts the Vite frontend locally with the repository's existing `npm run dev -- --host 127.0.0.1` command when port `5173` is not already occupied.
6. Optionally calls the existing safe idempotent sample import endpoint `POST /api/materials/import-sample` unless `-SkipSampleImport` is supplied.

The script prints the URLs that the evaluator should open:

- Frontend: http://127.0.0.1:5173
- Backend: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Neo4j browser: http://127.0.0.1:7474

The local startup flow is intentionally non-destructive:

- It does not reset the PostgreSQL database.
- It does not delete existing materials, matches, identities, or graph data.
- It does not automatically overwrite existing rows because the existing import route `import_csv` is set up to skip duplicates by `(source_system, legacy_code)`.
- It only starts the documented compose services and optionally invokes the existing sample endpoint. If a process already owns the backend or frontend port, the launcher notices that and avoids launching a second copy.

To stop the local workflow, close the backend and frontend terminal windows or stop the `uvicorn` and `npm` / `vite` processes in Task Manager.

## 🔌 ERP Integration Status

The repository includes an ERP integration surface in the backend router and service layer (`backend/app/routers/integrations.py`, `backend/app/services/erp_connectors.py`, and `backend/app/services/erp_sync.py`). Those files define a provider-aware connector abstraction for SAP and Oracle-style providers, plus an integration activity and sync status model that can report provider configuration and attempt a sync.

The shipped default workflow is still CSV and sample-data driven through the material ingestion route (`POST /api/materials/import-sample` and `POST /api/materials/import`) described in the repository. The connector settings are read from environment variables (`SAP_*`, `ORACLE_*`) and are therefore integration-ready scaffolding, not a turnkey production SAP/Oracle deployment. The current repository is best understood as a configurable ERP-to-identity implementation in which future ERP feeds may be routed through the same normalization, extraction, matching, and identity graph pipeline without changing the identity-resolution logic.

## Technology Stack

**Frontend**
- React
- Vite
- Axios
- Lucide React

**Backend**
- Python
- FastAPI
- Uvicorn
- SQLAlchemy

**Database**
- PostgreSQL

**AI / Matching**
- Scikit-learn (TF-IDF character n-grams + cosine similarity — the active `EMBEDDING_BACKEND=tfidf` default, chosen to run fully offline)
- Sentence Transformers is a documented, not-yet-wired swap-in for when model downloads are available (see `EMBEDDING_BACKEND` in `app/config.py`)

**Graph**
- Neo4j
- Neo4j Python Driver

**Infrastructure**
- Docker Desktop
- PostgreSQL Docker container
- Neo4j Docker container

## Project Structure

```
Zero-Copy-Material-Identity-Layer/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point — wires up every active router
│   │   ├── config.py            # Settings (DB URL, Neo4j, matching weights, ERP creds)
│   │   ├── database.py          # SQLAlchemy engine / session / Base
│   │   ├── models.py            # ORM models (Material, MaterialAttribute,
│   │   │                        #   MaterialMatch, MaterialIdentity, ...)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   │
│   │   ├── routers/             # Active API routers (all imported by main.py)
│   │   │   ├── materials.py     #   /api/materials — import, list, reset
│   │   │   ├── matches.py       #   /api/matches — review + resolve match candidates
│   │   │   ├── identities.py    #   /api/identities — canonical identity detail
│   │   │   ├── graph.py         #   /api/graph, /api/analytics
│   │   │   ├── integrations.py  #   /api/integrations — ERP connector status/sync
│   │   │   └── auth.py          #   /api/auth — demo login
│   │   │
│   │   └── services/            # Active business logic used by the routers above
│   │       ├── importer.py      #   CSV ingestion + triggers match-candidate generation
│   │       ├── normalize.py     #   Description normalization
│   │       ├── extract.py       #   Attribute extraction from descriptions
│   │       ├── matching.py      #   Semantic / attribute / rule scoring, hybrid confidence
│   │       ├── identity.py      #   Canonical identity assembly
│   │       ├── graph.py         #   In-memory graph view for the dashboard
│   │       ├── neo4j_sync.py    #   Mirrors accepted matches into Neo4j
│   │       ├── erp_connectors.py#   SAP / Oracle connector adapters
│   │       └── erp_sync.py      #   Pulls records from a connector into materials
│   │
│   ├── sample_data/
│   │   ├── erp_a_sap.csv        # Synthetic ERP-A dataset used by "Import Sample Data"
│   │   └── erp_b_sap.csv        # Synthetic ERP-B dataset used by "Import Sample Data"
│   │
│   ├── tests/                   # Pytest suite (test_matching.py, test_normalize.py, ...)
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx / main.jsx / api.js
│   │   ├── components/          # TopBar, Sidebar
│   │   └── views/                # ImportView, CandidatesView, GraphView, AnalyticsView
│   ├── package.json
│   └── Dockerfile
│
├── data/
│   └── materials.csv            # Sample CSV used in the manual demo walkthrough
│
├── docs/
│   └── ERP_INTEGRATION_GUIDE.md
│
├── docker-compose.yml            # postgres + neo4j + backend + frontend
└── README.md
```

> A few top-level folders (`ai/`, `connectors/`, `database/`, `docker/`, `graph/`, and a root-level `tests/`) exist as empty placeholders (`.gitkeep` only) from early scaffolding and hold no active code — they're omitted from the tree above.

##  Active Implementation

The backend went through a duplicate-cleanup pass early in development, where the material ingestion and matching logic was rewritten. To avoid ambiguity for anyone reading the code:

- **Entry point**: `backend/app/main.py` is the only application entry point. It creates the FastAPI app and registers every active router.
- **Active routers**: the routers actually imported by `main.py` — `materials`, `matches`, `graph` (including its `analytics_router`), `integrations`, `identities`, and `auth`, all under `app/routers/`. Everything the API surface exposes comes from this set.
- **Active ingestion pipeline**: CSV/ERP import is handled by `app/services/importer.py`, which normalizes descriptions (`normalize.py`), extracts attributes (`extract.py`), and then generates match candidates.
- **Active matching pipeline**: match scoring is handled by `app/services/matching.py` — semantic similarity (TF-IDF character n-grams + cosine similarity via scikit-learn, the default `EMBEDDING_BACKEND=tfidf`), attribute similarity, conflict detection, and the weighted hybrid confidence score.
- **Legacy/unused code**: earlier iterations of this pipeline (`app/api/materials.py`, `app/db/database.py`, `app/models/` per-file model package, and `app/services/ingestion.py`, `matcher.py`, `normalization.py`) still exist in the repository but are **not imported by `main.py` or by anything the active routers use** — they are not part of the runtime path and can be treated as dead code.

**Canonical pipeline** (what actually runs when you import data through the dashboard):

```
Source Materials  (CSV upload / sample datasets / ERP connectors)
        ↓
Ingestion            (importer.py)
        ↓
Normalization / Attribute Extraction   (normalize.py, extract.py)
        ↓
Matching             (matching.py — semantic + attribute + rule scoring)
        ↓
Match Decision        (material_matches table — pending / MATCH / REVIEW / NO_MATCH)
        ↓
Canonical Identities   (identity.py, material_identities table)
        ↓
Neo4j Identity Graph   (neo4j_sync.py)
        ↓
React Dashboard        (frontend/src/views)
```

## Database Design

The PostgreSQL database contains separate tables for source records, attributes, matches, and canonical identities.

**materials** — Stores the original source records.

Important fields: `id`, `source_system`, `legacy_code`, `description`, `manufacturer`, `category`, `unit`, `specifications`, `created_at`, `updated_at`

**material_attributes** — Stores derived normalized attributes.

Examples: `material`, `type`, `diameter`, `length`, `standard`, `normalized_description`

**material_matches** — Stores pairwise matching results.

Important fields: `material_a`, `material_b`, `semantic_score`, `attribute_score`, `rule_score`, `final_confidence`, `status`

Possible statuses: `MATCH`, `REVIEW`, `NO_MATCH`

**material_identities** — Stores canonical material identities.

Fields: `identity_id`, `canonical_name`, `category`, `status`

**material_identity_members** — Maps source material records to their canonical identity.

Fields: `identity_id`, `material_id`

This mapping is important for maintaining traceability between the canonical identity and the original source records.

##  Matching Engine

The matching engine combines three signals.

**1. Semantic Similarity**

Normalized material descriptions are vectorized with a TF-IDF character n-gram model (scikit-learn) and compared with cosine similarity. This is the default `EMBEDDING_BACKEND=tfidf` — it ships with zero external model downloads and works fully offline. A Sentence Transformers backend is documented as a future swap-in once model-download access is available.

**2. Attribute Similarity**

Important material attributes are compared: Material, Type, Diameter, Length, Standard. Exact matches receive a strong score.

**3. Rule-Based Validation**

Business rules prevent incorrect matches. For example, `M10 × 50` must not automatically match `M10 × 80` even if their descriptions are semantically very similar. Hard attribute conflicts can therefore force `NO_MATCH`.

##  Hybrid Confidence Formula

The current scoring model uses:

```
Final Confidence =
    0.50 × Semantic Score
  + 0.30 × Attribute Score
  + 0.20 × Rule Score
```

Decision thresholds:

- Confidence >= 0.85 → **MATCH**
- 0.65 <= Confidence < 0.85 → **REVIEW**
- Confidence < 0.65 → **NO_MATCH**

Hard attribute conflicts override the score and produce `NO_MATCH`.

## Current Dataset

The included dataset contains five material records:

| Source | Legacy Code | Description |
|---|---|---|
| SAP | 100001 | SS hex bolt M10 x 50 mm DIN 933 |
| SAP | 100002 | Stainless Steel Hex Bolt 10mm x 50mm DIN933 |
| ORACLE | MT-7788 | M10-50 SS HEX BOLT DIN 933 |
| SAP | 100003 | SS hex bolt M10 x 80 mm DIN 933 |
| ORACLE | MT-9911 | Steel washer M10 DIN 125 |

The expected pipeline result is:

```
5 source materials
        ↓
10 pairwise comparisons
        ↓
3 canonical identities
        ↓
5 identity memberships
```

The three identities represent:

- **Identity 1** — SS Hex Bolt M10 × 50 DIN 933 → SAP 100001, SAP 100002, ORACLE MT-7788
- **Identity 2** — SS Hex Bolt M10 × 80 DIN 933 → SAP 100003
- **Identity 3** — Steel Washer M10 DIN 125 → ORACLE MT-9911

##  Installation

### Prerequisites

Install:
- Docker Desktop
- Python 3.12
- Node.js
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/rishipilla/Zero-Copy-Material-Identity-Layer.git
cd Zero-Copy-Material-Identity-Layer
```

### 2. Start PostgreSQL

The project uses a PostgreSQL Docker container. Start Docker Desktop first, then:

```bash
docker start materials-postgres
```

Verify:

```bash
docker ps
```

### 3. Start Neo4j

Start the Neo4j container:

```bash
docker start materials-neo4j
```

Verify:

```bash
docker ps
```

### 4. Start the Backend

Open PowerShell:

```powershell
cd C:\Users\<YOUR_USERNAME>\zero-copy-material-identity\backend
```

Create/activate the Python environment if necessary:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start FastAPI:

```powershell
uvicorn app.main:app --reload
```

- Backend: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

### 5. Start the Frontend

Open a second PowerShell window:

```powershell
cd C:\Users\<YOUR_USERNAME>\zero-copy-material-identity\frontend
node_modules\.bin\vite.cmd --host 127.0.0.1
```

Frontend: http://127.0.0.1:5173

## 🎬 Presentation Workflow

Use the following sequence during the presentation.

**Step 1 — Import Materials**

Open http://127.0.0.1:5173, select `data/materials.csv`, click **Import CSV**.

Expected result: `5 materials imported successfully.`

If the CSV was already imported, the application prevents duplicate imports and may report `0 materials imported successfully.` — this is expected because the records already exist.

**Step 2 — Run Matching**

Click **Run Matching**.

Expected result: `Matching completed. 10 pairs evaluated.`

The system evaluates all unique material pairs. For five records: `5 × 4 / 2 = 10 pairs`

**Step 3 — Build Identities**

Click **Build Identities**.

Expected result: `Identity build completed. 3 identities created.`

**Step 4 — Build Graph**

Start Neo4j first, then click **Build Graph**.

Expected result: `Graph created. 5 materials, 3 identities, 5 relationships.`

The graph contains:

```
Identity
   │
   ├── HAS_MEMBER → Material
   ├── HAS_MEMBER → Material
   └── HAS_MEMBER → Material
```

##  API Endpoints

| Endpoint | Description |
|---|---|
| `POST /api/materials/import` | Uploads a CSV file (matching runs automatically as part of import) |
| `POST /api/materials/import-sample` | Loads the three bundled synthetic ERP datasets (`SAP-A`, `SAP-B`, `LEGACY-ERP`) and demonstrates the committed three-way cross-source duplicate examples for fasteners, hydraulics, and welding materials |
| `GET /api/materials` | Lists imported material records |
| `DELETE /api/materials/reset` | Clears the imported dataset (materials, attributes, matches, identities) |
| `GET /api/matches` | Lists pairwise match candidates |
| `POST /api/matches/{match_id}/resolve` | Accepts/rejects a match candidate |
| `GET /api/identities/{identity_id}` | Canonical identity detail |
| `GET /api/graph` | Neo4j-backed identity graph for the dashboard |
| `GET /api/integrations` | ERP connector status |
| `POST /api/auth/demo-login` | Password gate for the dashboard |
| `GET /api/health` | Health check |

##  Zero-Copy Principle

The system does not overwrite the original material descriptions.

```
SOURCE RECORD
     │
     ├── Original Description
     ├── Manufacturer
     ├── Legacy Code
     └── Source System
             │
             ▼
       Derived Attributes
             │
             ▼
      Canonical Identity
```

This preserves:

- Source traceability
- Original system ownership
- Legacy identifiers
- Auditability
- Reversibility

The canonical identity is a derived layer, not a replacement for the source record.

## Why This Approach Works

A pure semantic similarity system can make dangerous mistakes. For example, `SS Hex Bolt M10 × 50` and `SS Hex Bolt M10 × 80` are semantically very similar — but their lengths are different.

Therefore the system combines AI semantic understanding + structured attribute comparison + business rules, producing safer material identity resolution than relying on embeddings alone.

## Value Proposition

**Before:** SAP, Oracle, and CSV each contribute records independently → Duplicate material records

**After:** SAP, Oracle, and CSV all feed the same pipeline → Canonical Material Identity, without modifying the original records.

Key benefits:

- Intelligent deduplication
- Source-system preservation
- Explainable matching
- AI-assisted identity resolution
- Canonical material identities
- Graph-based relationships
- Enterprise-ready architecture
- Traceability

## Suggested Stakeholder Narrative

- **Problem**: Explain the duplicate material problem across ERP systems.
- **Solution**: Explain the Zero-Copy Identity Layer.
- **AI / Matching**: Explain semantic similarity + attribute matching + business rules.
- **Architecture**: Show CSV → PostgreSQL → Matching → Identities → Neo4j → React Dashboard.

## 🎤 60-Second Workflow Script

> "Organizations often store the same physical material multiple times across SAP, Oracle, and legacy systems. The descriptions are different, but the underlying material is the same.
>
> Our Zero-Copy Material Identity Layer solves this without modifying the original source records.
>
> We first import the source records into PostgreSQL. We normalize the descriptions and extract important attributes such as material type, diameter, length, and standard.
>
> Our matching engine combines semantic similarity, attribute similarity, and business rules to determine whether two records represent the same material.
>
> The confirmed matches are grouped into canonical identities and then represented as a graph in Neo4j.
>
> In this workflow, five source records result in ten comparisons and three canonical material identities.
>
> Most importantly, the original source records remain untouched. We create an intelligent identity layer on top of them."

## Future Enhancements

- Human review workflow
- Explainable match reasoning
- Confidence visualization
- Advanced attribute extraction
- More material categories
- Larger enterprise datasets
- Graph visualization
- Supplier intelligence
- Duplicate detection dashboards
- Audit history
- Role-based access control
- Production database migrations
- Automated ingestion from ERP systems

##  Project Status

| Component | Status |
|---|---|
| Architecture | ✅ |
| PostgreSQL | ✅ |
| CSV ingestion | ✅ |
| Normalization | ✅ |
| Attribute extraction | ✅ |
| Semantic matching | ✅ |
| Hybrid scoring | ✅ |
| Identity generation | ✅ |
| Identity membership | ✅ |
| Neo4j graph | ✅ |
| FastAPI | ✅ |
| React dashboard | ✅ |
| CORS | ✅ |
| GitHub repository | ✅ |
| End-to-end demo | ✅ |

## License

This project was created as a hackathon prototype (Smart India Hackathon 2026, Problem Statement SIH26099).