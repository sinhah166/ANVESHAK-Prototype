# 🌌 ANVESHAK
### Autonomous Real-Time Astronomical Signal Detection & Classification Pipeline

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688)
![React](https://img.shields.io/badge/React-18.2.0-61DAFB)
![License](https://img.shields.io/badge/License-MIT-purple)

**ANVESHAK** (Sanskrit for "Searcher" or "Explorer") is a highly scalable, real-time software pipeline designed to autonomously ingest, process, detect, and classify astronomical signals. 

It is capable of handling multiple data streams simultaneously—ranging from optical light curves (like those from TESS and Kepler) to dynamic radio spectrograms—identifying potential exoplanetary transits, stellar variability, narrowband radio anomalies, and RFIs using a combination of robust scientific algorithms and Machine Learning (Isolation Forests, Random Forests).

---

## ✨ Key Features

- 📡 **Multi-Source Ingestion Framework:** Pluggable adapter architecture to easily ingest data from TESS, Kepler, local archives, or real-time telescope feeds.
- ⚡ **Real-Time Processing Pipeline:** Built on an asynchronous architecture using FastAPI, Redis Streams, and PostgreSQL.
- 🔬 **Scientific Feature Extraction:** 
  - **Light Curves:** Detrending (Savitzky-Golay), Phase-folding, and Transit Least Squares (TLS) detection.
  - **Radio Spectrograms:** Background subtraction, RFI flagging, and drift-rate calculation.
- 🧠 **Machine Learning Classification:** Random Forest baseline and rule-based fallback to classify signals (e.g., `planet_candidate`, `eclipsing_binary`, `narrowband_candidate`).
- 📊 **Stunning Live Dashboard:** A dark-themed, glassmorphic React interface featuring live WebSocket feeds, Plotly.js interactive charts, and Recharts distribution analytics.

---

## 🏗️ Architecture Overview

The platform is designed using a microservices-inspired architecture:

1. **Ingestion Layer (Adapters):** Connects to external APIs/archives and normalizes raw data into a standard schema.
2. **Processing Layer (Pipeline):** Preprocesses arrays (NumPy/SciPy), detects signals, and extracts scientific features.
3. **ML Layer:** Classifies the extracted features to determine the nature of the signal and assigns a confidence score.
4. **Message Broker (Redis):** Publishes the detection events to streams for real-time broadcasting.
5. **API & Storage (FastAPI + PostgreSQL):** Persists the results and provides REST & WebSocket endpoints.
6. **Presentation Layer (React):** Consumes the API and WebSocket feeds to render the Mission Control Dashboard.

---

## 🛠️ Technology Stack

- **Backend Core:** Python 3.11+, FastAPI, SQLAlchemy (Async), Pydantic
- **Data Science / Astronomy:** NumPy, SciPy, Scikit-Learn, Lightkurve, TransitLeastSquares
- **Queue / Broker:** Redis Streams
- **Database:** PostgreSQL
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Plotly.js, Recharts
- **Infrastructure:** Docker, Docker Compose

---

## 🚀 Getting Started (Quick Setup)

The easiest way to run the entire ANVESHAK platform is using **Docker Compose**.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Make sure it is running)
- Git

### 1. Clone & Start
Open your terminal and run:
```bash
# Clone the repository (if you haven't already)
git clone https://github.com/yourusername/anveshak.git
cd anveshak

# Build and start all services in detached mode
docker compose up --build -d
```

### 2. Access the Platform
Once the containers are up, the services will be available at:
- **Mission Control Dashboard:** (link will be available soon)
- **FastAPI Backend (Swagger UI):** (link will be available soon)

### 3. Run the Live Demo
1. Open the Dashboard at (link will be available soon)
2. Click the **RUN DEMO PIPELINE** button in the left sidebar.
3. Watch the Live Detection Feed populate in real-time as simulated TESS and Radio data streams through the pipeline!

---

## 📂 Project Structure

```text
ANVESHAK/
├── backend/                  # Python FastAPI Application
│   ├── app/
│   │   ├── adapters/         # Data ingestion adapters (TESS, Kepler, Synthetic)
│   │   ├── api/              # REST API and WebSocket routes
│   │   ├── core/             # Configuration, Logging, Enums
│   │   ├── ml/               # Machine Learning models (Random Forest, CNN stubs)
│   │   ├── models/           # SQLAlchemy ORM Database Models
│   │   ├── processing/       # Scientific algorithms (Lightcurve, Spectrogram, TLS)
│   │   ├── queue/            # Redis Producer and Consumer clients
│   │   ├── schemas/          # Pydantic validation schemas
│   │   └── services/         # Business logic and Orchestration
│   ├── tests/                # Pytest suite
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Backend container definition
│
├── frontend/                 # React & Vite Application
│   ├── src/
│   │   ├── charts/           # Interactive Plotly.js scientific charts
│   │   ├── components/       # UI Components (Layout, StatsCards, LiveFeed)
│   │   ├── hooks/            # Custom hooks (useWebSocket)
│   │   └── pages/            # Dashboard Views (Overview, Candidates, Pipeline)
│   ├── package.json          # Node dependencies
│   ├── tailwind.config.js    # Theme styling
│   └── Dockerfile            # Frontend container definition
│
├── config/                   # System configuration files
│   └── sources.yaml          # Active data source definitions
│
├── .env.example              # Environment variables template
└── docker-compose.yml        # Multi-container orchestration
```

---

## 🔌 API Endpoints

The backend exposes a fully documented OpenAPI specification at `/docs`. Key endpoints include:

- `POST /api/pipeline/run/{source_id}` - Triggers the pipeline for a specific telescope/source.
- `POST /api/pipeline/demo` - Triggers the real-time visual demo sequence.
- `GET /api/candidates` - Retrieves a paginated, filterable list of all detected candidates.
- `GET /api/candidates/{id}` - Retrieves full scientific details and chart data arrays for a specific candidate.
- `WS /ws/events` - WebSocket endpoint for subscribing to live detection alerts.

---

## ⚠️ Scientific Disclaimer

ANVESHAK is designed as an automated triage, sorting, and alerting mechanism for astronomical datasets. 
**The automated classifications and outputs (e.g., `planet_candidate`, `narrowband_candidate`) produced by this pipeline do NOT constitute scientific confirmation.** 
All candidates flagged by this system require rigorous independent astronomical analysis, manual vetting, and follow-up observation before they can be considered scientifically validated discoveries.

---

## 🔮 Future Roadmap

- [ ] **Phase 13: Full Test Suite Coverage** (Unit tests for TLS algorithms and data normalization)
- [ ] **CNN Integration:** Replace the baseline Random Forest classifier with a deep PyTorch CNN for spectrogram classification.
- [ ] **SETI TurboSETI Integration:** Connect to Berkeley's TurboSETI for advanced radio drift-rate detection.
- [ ] **User Authentication:** Add JWT-based logins for multi-user mission control teams.

---

**Developed with ❤️ for the Astronomical and Open-Source Community.**
