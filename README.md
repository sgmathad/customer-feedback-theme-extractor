# Customer Feedback Theme Extractor

> Upload customer feedback → AI discovers themes → sentiment analysis → prioritised recommendations → PDF report.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Quick Start](#quick-start)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Running Tests](#running-tests)
8. [Deployment](#deployment)
9. [Project Structure](#project-structure)

---

## Overview

The **Customer Feedback Theme Extractor** is a full-stack AI application that turns raw customer feedback (CSV, Excel, text, PDF, Word) into actionable insights:

- **Theme discovery** — sentence embeddings + K-Means clustering surfaces the topics customers talk about most
- **Sentiment analysis** — DistilBERT classifies each entry as positive, neutral, or negative
- **Quote selection** — PII-redacted, diversity-filtered representative quotes per theme
- **Recommendations** — Claude generates a prioritised "What to Fix First" list
- **PDF export** — one-click branded report download

---

## Features

| Feature         | Detail                                                                |
| --------------- | --------------------------------------------------------------------- |
| File formats    | CSV, XLSX, TXT, PDF, DOCX, JSON                                       |
| File limits     | 10 MB per file, 50 MB per batch                                       |
| Clustering      | K-Means with silhouette-score tuning (3–12 clusters)                  |
| Sentiment model | `distilbert-base-uncased-finetuned-sst-2-english`                     |
| Theme naming    | Claude `claude-sonnet-4-20250514`                                     |
| Recommendations | Claude, weighted by frequency + negative-sentiment %                  |
| Demo dataset    | 42 synthetic entries across 7 product themes                          |
| PDF report      | ReportLab — header, stats, sentiment, themes, quotes, recommendations |
| Error handling  | Per-file size validation, pipeline timeouts, structured error JSON    |

---

## Architecture

```
┌──────────────────────────────────────┐    HTTP/REST
│          React + Vite frontend       │ ──────────────▶ ┌──────────────────────┐
│  FeedBackUpload → Dashboard          │                  │  FastAPI backend     │
│  ThemeCard · SentimentChart          │ ◀────────────── │  /upload /demo       │
│  RecommendationsPanel                │    JSON / PDF    │  /analyze /results   │
└──────────────────────────────────────┘                  └──────────┬───────────┘
                                                                     │
                                             ┌───────────────────────┼──────────────┐
                                             │                       │              │
                                     HuggingFace              Anthropic API     ReportLab
                                     (DistilBERT)          (claude-sonnet-4)   (PDF gen)
```

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- An **Anthropic API key** — [get one here](https://console.anthropic.com/)

### 1. Clone and configure

```bash
git clone https://github.com/your-org/feedback-theme-extractor.git
cd feedback-theme-extractor

# Backend env
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Frontend env
cp frontend/.env.example frontend/.env
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements/requirements.txt

# First run downloads the DistilBERT model (~260 MB) — this is automatic
uvicorn api.app:app --reload --port 8000
```

Backend will be running at **http://localhost:8000**  
Interactive API docs: **http://localhost:8000/docs**

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be running at **http://localhost:5173**

### 4. Try it out

1. Open **http://localhost:5173**
2. Click **"Try with sample data"** to load 42 synthetic reviews
3. Click **"Analyze"** — wait ~30–60 s
4. Explore the dashboard, expand theme cards, read quotes
5. Click **"Download Report"** for the PDF

---

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` in the project root and `frontend/.env.example` to `frontend/.env`.

| Variable                  | Default                 | Description                     |
| ------------------------- | ----------------------- | ------------------------------- |
| `ANTHROPIC_API_KEY`       | _(required)_            | Your Anthropic API key          |
| `BACKEND_HOST`            | `0.0.0.0`               | Uvicorn bind host               |
| `BACKEND_PORT`            | `8000`                  | Uvicorn bind port               |
| `MAX_FILE_SIZE_MB`        | `10`                    | Per-file upload limit           |
| `MAX_REQUEST_SIZE_MB`     | `50`                    | Total batch upload limit        |
| `MIN_CLUSTERS`            | `3`                     | Minimum themes to discover      |
| `MAX_CLUSTERS`            | `12`                    | Maximum themes to discover      |
| `QUOTES_PER_THEME`        | `5`                     | Representative quotes per theme |
| `NUM_RECOMMENDATIONS`     | `5`                     | Prioritised actions to generate |
| `ANALYZE_TIMEOUT_SECONDS` | `300`                   | Pipeline timeout                |
| `LOG_LEVEL`               | `INFO`                  | Python logging level            |
| `VITE_API_BASE_URL`       | `http://localhost:8000` | Backend URL (frontend)          |

---

## API Reference

All endpoints return JSON. Errors follow the shape `{"error": "ErrorType", "message": "..."}`.

| Method   | Path                | Description                        |
| -------- | ------------------- | ---------------------------------- |
| `GET`    | `/`                 | Health check                       |
| `GET`    | `/status`           | Files uploaded, limits, ready flag |
| `POST`   | `/upload`           | Upload one or more files           |
| `POST`   | `/demo`             | Load built-in demo dataset         |
| `POST`   | `/analyze`          | Run full analysis pipeline         |
| `GET`    | `/results`          | List stored analyses               |
| `GET`    | `/results/{id}`     | Get a specific analysis            |
| `GET`    | `/results/{id}/pdf` | Download PDF report                |
| `DELETE` | `/clear`            | Remove all uploaded files          |
| `DELETE` | `/results/{id}`     | Delete one analysis                |
| `DELETE` | `/results`          | Delete all analyses                |

Full interactive docs at `/docs` (Swagger UI) or `/redoc`.

---

## Running Tests

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Tests cover:

- Upload validation (extension, size, empty)
- Demo dataset loading
- Full analysis pipeline (mocked services)
- Result retrieval and deletion
- PDF generation and download
- Middleware (file size limits, timeouts)

---

## Deployment

### Backend — Render / Railway / Fly.io

1. Set all environment variables (especially `ANTHROPIC_API_KEY`) in the platform dashboard
2. Set start command: `uvicorn api.app:app --host 0.0.0.0 --port $PORT`
3. Add `CORS_ORIGINS=https://your-frontend.vercel.app` to allow your frontend

**Render** example `render.yaml`:

```yaml
services:
  - type: web
    name: feedback-extractor-api
    env: python
    buildCommand: pip install -r backend/requirements/requirements.txt
    startCommand: cd backend && uvicorn api.app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false
```

### Frontend — Vercel / Netlify

1. Set `VITE_API_BASE_URL=https://your-backend.onrender.com` as a build environment variable
2. Build command: `npm run build`
3. Output directory: `dist`

**Vercel** one-liner:

```bash
cd frontend
npx vercel --prod
```

---

## Project Structure

```
feedback-theme-extractor/
├── .env.example                    # Root env template
├── README.md
│
├── backend/
│   ├── api/
│   │   ├── app.py                  # FastAPI app, routes, middleware wiring
│   │   └── middleware.py           # FileSizeLimit, Timeout, RequestLogging
│   ├── services/
│   │   ├── file_parser.py          # Multi-format file ingestion
│   │   ├── text_cleaner.py         # Dedup + normalisation
│   │   ├── embeddings_clustering.py # Sentence-BERT + K-Means
│   │   ├── theme_generator.py      # Claude theme naming
│   │   ├── sentiment_analyzer.py   # DistilBERT sentiment
│   │   ├── quote_selector.py       # PII redaction + diversity quotes
│   │   ├── recommendations.py      # Claude "What to Fix First"
│   │   ├── pdf_report.py           # ReportLab PDF
│   │   └── demo_data.py            # 42-entry synthetic dataset
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_api.py
│   │   └── test_middleware.py
│   └── requirements/
│       └── requirements.txt
│
└── frontend/
    ├── .env.example
    ├── src/
    │   ├── lib/
    │   │   └── api.ts              # Centralised API client
    │   ├── interfaces/
    │   │   ├── analysisInterface.ts
    │   │   └── index.ts
    │   ├── reusables/
    │   │   ├── FileUpload.tsx
    │   │   ├── ProgressBar.tsx
    │   │   ├── SentimentBadge.tsx
    │   │   └── index.ts
    │   └── components/
    │       ├── FeedBackUpload.tsx  # Upload flow + state machine
    │       ├── Dashboard.tsx       # Results dashboard
    │       ├── ThemeCard.tsx       # Expandable theme with quotes
    │       ├── SentimentChart.tsx  # Stacked bar / horizontal bar
    │       ├── RecommendationsPanel.tsx
    │       └── index.ts
    └── package.json
```

---

## License

MIT © 2026
