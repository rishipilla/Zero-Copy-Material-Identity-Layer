# Zero-Copy Material Identity Layer

> Intelligent material deduplication and identity resolution across multiple enterprise source systems.

## 🚀 Overview

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

## 🎯 Problem Statement

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

## 💡 Solution

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

## 🏗️ Architecture

```
                   ┌──────────────────┐
                   │    ERP / CSV      │
                   │ SAP / Oracle etc  │
                   └────────┬──────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │  Ingestion API   │
                  │     FastAPI      │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Raw Materials    │
                  │   PostgreSQL     │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │  Normalization   │
                  │  + Attribute     │
                  │    Extraction    │
                  └────────┬─────────┘
                           │
                           ▼
              ┌───────────────────────────┐
              │      Matching Engine      │
              │                           │
              │ Semantic Similarity       │
              │ Attribute Similarity      │
              │ Rule-Based Validation     │
              └─────────────┬─────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │ Match Decision   │
                  │                  │
                  │ MATCH            │
                  │ REVIEW           │
                  │ NO_MATCH         │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Canonical        │
                  │ Identities       │
                  │   PostgreSQL     │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │     Neo4j        │
                  │ Identity Graph   │
                  └────────┬─────────┘
                           ▲
                           │
                  ┌────────┴─────────┐
                  │ React Dashboard  │
                  │                  │
                  │ Import           │
                  │ Match            │
                  │ Identity         │
                  │ Graph            │
                  └──────────────────┘
```

## 🧰 Technology Stack

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
- Sentence Transformers (all-MiniLM-L6-v2)
- Scikit-learn
- Cosine similarity

**Graph**
- Neo4j
- Neo4j Python Driver

**Infrastructure**
- Docker Desktop
- PostgreSQL Docker container
- Neo4j Docker container

## 📁 Project Structure

```
zero-copy-material-identity/
│
├── backend/
│   │
│   ├── app/
│   │   ├── api/
│   │   │   └── materials.py
│   │   │
│   │   ├── db/
│   │   │   └── database.py
│   │   │
│   │   ├── models/
│   │   │   ├── material.py
│   │   │   ├── material_attribute.py
│   │   │   ├── material_identity.py
│   │   │   ├── material_identity_member.py
│   │   │   └── material_match.py
│   │   │
│   │   ├── services/
│   │   │   ├── ingestion.py
│   │   │   ├── normalization.py
│   │   │   ├── matching.py
│   │   │   ├── matcher.py
│   │   │   ├── identity.py
│   │   │   └── graph.py
│   │   │
│   │   └── main.py
│   │
│   └── .venv/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   ├── package.json
│   └── package-lock.json
│
├── data/
│   └── materials.csv
│
└── README.md
```

## 🗄️ Database Design

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

## 🧠 Matching Engine

The matching engine combines three signals.

**1. Semantic Similarity**

Sentence Transformers generates embeddings for normalized material descriptions. Cosine similarity is used to determine semantic similarity.

**2. Attribute Similarity**

Important material attributes are compared: Material, Type, Diameter, Length, Standard. Exact matches receive a strong score.

**3. Rule-Based Validation**

Business rules prevent incorrect matches. For example, `M10 × 50` must not automatically match `M10 × 80` even if their descriptions are semantically very similar. Hard attribute conflicts can therefore force `NO_MATCH`.

## 📊 Hybrid Confidence Formula

The current prototype uses:

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

## 🧪 Current Demo Dataset

The included demo contains five material records:

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

## 🚀 Installation

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
- Health check: http://127.0.0.1:8000/health

### 5. Start the Frontend

Open a second PowerShell window:

```powershell
cd C:\Users\<YOUR_USERNAME>\zero-copy-material-identity\frontend
node_modules\.bin\vite.cmd --host 127.0.0.1
```

Frontend: http://127.0.0.1:5173

## 🎬 Hackathon Demo

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

## 🔍 API Endpoints

| Endpoint | Description |
|---|---|
| `POST /api/materials/import` | Uploads a CSV file |
| `POST /api/materials/match` | Runs pairwise material matching |
| `POST /api/materials/identities` | Creates canonical material identities |
| `POST /api/materials/graph` | Creates the Neo4j material identity graph |

## 🔐 Zero-Copy Principle

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

## 📈 Why This Approach Works

A pure semantic similarity system can make dangerous mistakes. For example, `SS Hex Bolt M10 × 50` and `SS Hex Bolt M10 × 80` are semantically very similar — but their lengths are different.

Therefore the system combines AI semantic understanding + structured attribute comparison + business rules, producing safer material identity resolution than relying on embeddings alone.

## 🏆 Hackathon Value Proposition

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

## 🧑‍🤝‍🧑 Suggested Team Presentation

- **Member 1 — Problem**: Explain the duplicate material problem across ERP systems.
- **Member 2 — Solution**: Explain the Zero-Copy Identity Layer.
- **Member 3 — AI / Matching**: Explain semantic similarity + attribute matching + business rules.
- **Member 4 — Architecture / Demo**: Show CSV → PostgreSQL → Matching → Identities → Neo4j → React Dashboard.

## 🎤 60-Second Demo Script

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
> In our demo, five source records result in ten comparisons and three canonical material identities.
>
> Most importantly, the original source records remain untouched. We create an intelligent identity layer on top of them."

## 🛠️ Future Enhancements

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

## 📌 Project Status

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

## 📄 License

This project was created as a hackathon prototype (Smart India Hackathon 2026, Problem Statement SIH26099).
