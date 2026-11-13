# RecoEngine

[![CI Pipeline](https://github.com/Soulofghost/recoengine/actions/workflows/ci.yml/badge.svg)](https://github.com/Soulofghost/recoengine/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/SQLite-WAL%20Mode-003B57.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **RecoEngine** is a high-performance personalized recommendation and discovery engine. It fuses item-item collaborative filtering co-occurrence matrices with dense content-based feature vector embeddings to generate explainable recommendations in real time with sub-millisecond response latency.

---

## 1. System Architecture

RecoEngine features a decoupled dual-model recommendation pipeline capable of seamless cold-start handling and real-time interaction feedback loops.

```
┌─────────────────────────────────────────────────────────────┐
│                 Discovery UI Console (SPA)                  │
│   • Multi-Persona Simulator (AI Engineer, DevOps, FinTech)  │
│   • Strategy Modulator (Hybrid / Collaborative / Content)   │
│   • Real-Time Recommendation Carousel with Explainability   │
│   • Interactive Catalog with 1-Click Interaction Logging    │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
┌──────────────────────────────▼──────────────────────────────┐
│                   FastAPI Application Tier                  │
│   • Interaction Ingestion Controller                        │
│   • Vector Feature Serialization Engine                     │
│   • Explainability Generator & Recommendation Dispatcher    │
└──────────────────────────────┬──────────────────────────────┘
                               │
       ┌───────────────────────┴───────────────────────┐
       ▼                                               ▼
┌─────────────────────────────┐         ┌─────────────────────────────┐
│  Item-Item Collaborative    │         │  Dense Content Vector Space │
│  • Implicit Rating Weights: │         │  • Multi-scale term hashing │
│    View (1.0), Save (2.5)   │         │  • Category & tag embeddings│
│    Rate (3.5), Buy (5.0)    │         │  • User centroid taste vector│
│  • Cross-user co-occurrence │         │  • Cosine similarity metric │
└──────────────┬──────────────┘         └──────────────┬──────────────┘
               │                                       │
               └───────────────────┬───────────────────┘
                                   ▼
                 ┌───────────────────────────────────┐
                 │       Hybrid Fusion Modulator     │
                 │ Score = β · Collab + (1-β) · Cont │
                 │ • Cold-Start Popularity Fallback  │
                 └─────────────────┬─────────────────┘
                                   ▼
                 ┌───────────────────────────────────┐
                 │    SQLite 3 High-Throughput WAL   │
                 │    • Items, Users, Interactions   │
                 │    • Recommendation Telemetry     │
                 └───────────────────────────────────┘
```

---

## 2. Core Mathematical Formulations

### A. Implicit Feedback Matrix
User interest is captured continuously across 4 discrete interaction tiers:
$$W(\text{interaction}) = \begin{cases}
1.0 & \text{VIEW} \\
2.5 & \text{BOOKMARK} \\
3.5 & \text{RATING} \\
5.0 & \text{PURCHASE}
\end{cases}$$

### B. User Taste Centroid Profile (Content-Based)
For a user $U$ who has interacted with items $\{i_1, i_2, \dots, i_k\}$ with weights $\{w_1, w_2, \dots, w_k\}$, their taste profile $\mathbf{u}_{\text{taste}}$ is computed as the normalized weighted centroid in $\mathbb{R}^{64}$:
$$\mathbf{u}_{\text{taste}} = \frac{\sum_{j=1}^{k} w_j \mathbf{v}_{ij}}{\left\|\sum_{j=1}^{k} w_j \mathbf{v}_{ij}\right\|_2}$$
The content-based score for any unseen candidate item $C$ is then:
$$\text{Score}_{\text{content}}(C) = \frac{\mathbf{u}_{\text{taste}} \cdot \mathbf{v}_C + 1}{2}$$

### C. Item-Item Collaborative Co-Occurrence
Item pairs co-interacted by users establish affinity weights:
$$\text{Score}_{\text{collab}}(C) = \sum_{j \in \text{UserInteractions}} w_j \cdot \text{CoOccur}(j, C)$$
Normalized to $[0, 1]$ across candidate items.

### D. Hybrid Fusion & Cold-Start Adaptation
$$\text{Score}_{\text{hybrid}} = \beta \cdot \text{Score}_{\text{collab}} + (1 - \beta) \cdot \text{Score}_{\text{content}}$$
- If user has **zero interactions** (Cold Start), the engine falls back to `COLD_START_POPULARITY` ranking based on average review rating and engagement velocity.

---

## 3. Technology Stack

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI 0.110+ | Real-time REST API engine |
| **Linear Algebra** | NumPy 1.24+ | Centroid calculation and vector cosine similarity |
| **Data Validation** | Pydantic v2 | Strict JSON serialization and input schemas |
| **Persistence** | SQLite 3 | WAL mode with foreign key cascade support |
| **Frontend UI** | Vanilla JS / CSS3 | Bespoke dark discovery interface with persona switching |
| **Testing** | Pytest + HTTPX | Integration and collaborative recommendation unit tests |
| **DevOps** | Docker / Compose | Multi-stage production container |
| **CI/CD** | GitHub Actions | Automated build, test, and quality validation |

---

## 4. API Endpoints

### Catalog Management
- `POST /api/items` — Add catalog item and compute 64-dim content feature vector.
- `GET /api/items` — List catalog items (supports `?category=` filter).
- `GET /api/items/{id}` — Retrieve item metadata.

### Interaction Ingestion
- `POST /api/interactions` — Log user action:
  ```json
  {
    "user_id": "alvin_ai",
    "item_id": "3b2c1d...",
    "interaction_type": "PURCHASE"
  }
  ```

### Personalized Recommendations
- `GET /api/recommendations/{user_id}` — Generate personalized recommendations.
  Query parameters: `strategy` (`HYBRID`, `COLLABORATIVE`, `CONTENT_BASED`), `beta` (0.0 to 1.0), `top_k` (1 to 20).

### Telemetry & Health
- `GET /api/analytics/reco-metrics` — Total items, active profiles, interaction count, avg latency.
- `GET /health` — Service readiness probe.

---

## 5. Local Setup & Testing

### Installation
```bash
# Clone the repository
git clone https://github.com/Soulofghost/recoengine.git
cd recoengine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Running the Application
```bash
uvicorn app.main:app --app-dir backend --reload --port 8000
```
Visit `http://localhost:8000` to interact with the discovery feed.

### Running Test Suite
```bash
pytest backend/tests -v
```

---

## 6. Docker Deployment

```bash
docker-compose up --build -d
docker-compose logs -f
```

---

## 7. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
