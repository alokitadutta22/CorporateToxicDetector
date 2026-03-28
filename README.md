# 🛡️ Corporate Toxic Comment Detector

> **SIH 2024 Digital Safety | Enterprise-Grade Hybrid ML + LLM Application**

### 🔴 [Live Demo → alokita-corporate-toxic-detector.hf.space](https://alokita-corporate-toxic-detector.hf.space)

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Alokita/corporate-toxic-detector)

A production-ready system that detects toxic, harassing, and threatening language in corporate communications. It combines a **fast ML model** with a **deep-learning LLM** to catch both obvious and evasive toxic content — including leet speak (`f@ck`), jumbled letters (`fcuk`), and unicode tricks.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Hybrid ML + LLM Scoring** | Combines TF-IDF/LogisticRegression (fast, 88% accuracy) with Toxic-BERT (deep, 95% accuracy) into a weighted hybrid score |
| **Anti-Evasion Normalizer** | 9-step text processing pipeline that defeats leet speak, letter transpositions, separator insertion, character repetition, unicode homoglyphs, and fuzzy misspellings |
| **PII Protection** | Microsoft Presidio-powered masking strips names, emails, phone numbers, and SSNs before logging |
| **Enterprise Audit Log** | Every prediction is logged to a SQLite database with timestamps for HR compliance |
| **In-Memory Cache** | Identical queries return instantly without re-running the ML/LLM pipeline |
| **React Dashboard** | Modern, dark-themed UI with real-time score visualization, bar charts, and audit log viewer |
| **Docker Ready** | Multi-stage Dockerfile + docker-compose for one-command deployment |

---

## 📁 Project Structure

```
CorporateToxicDetector/
├── src/                          # Backend source code
│   ├── api/
│   │   └── main.py               # FastAPI server (REST endpoints, CORS, caching)
│   ├── models/
│   │   ├── predictor.py          # Hybrid prediction pipeline (ML + LLM orchestration)
│   │   └── train_peft.py         # ML model training script (TF-IDF + LogisticRegression)
│   ├── rag/
│   │   └── llm_rag.py            # Toxic-BERT LLM wrapper + corporate policy mapper
│   ├── utils/
│   │   ├── text_normalizer.py    # 9-step anti-evasion text normalizer
│   │   ├── pii_masker.py         # PII detection & anonymization (Presidio)
│   │   ├── audit_logger.py       # SQLite audit log (SQLAlchemy ORM)
│   │   └── cache.py              # In-memory prediction cache
│   └── data/
│       └── prepare_data.py       # Dataset loading, cleaning, and sampling
├── frontend/                     # React + Vite frontend
│   └── src/
│       ├── App.jsx               # Main dashboard component
│       ├── App.css               # Dashboard styles (dark theme)
│       ├── index.css             # Global styles
│       └── main.jsx              # React entry point
├── models/                       # Trained ML model artifacts
│   ├── toxic_classifier.pkl      # Logistic Regression model
│   └── tfidf_vectorizer.pkl      # TF-IDF vocabulary/weights
├── data/                         # Data files
│   ├── train.csv                 # Raw Jigsaw toxicity dataset
│   ├── cleaned_train.csv         # Preprocessed training data
│   └── corporate_audit.db        # SQLite audit log database
├── docs/                         # 📖 Documentation (safe to delete)
│   └── PROJECT_GUIDE.md          # Complete project guide for presentation
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Docker Compose config
├── config.yaml                   # Model/training configuration
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment variables template
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start the API server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Open the App
- **Frontend Dashboard:** http://localhost:5173
- **API Health Check:** http://localhost:8000/health
- **API Docs (Swagger):** http://localhost:8000/docs

### 4. Docker (Alternative)
```bash
docker-compose up --build
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Basic health check |
| `GET` | `/health` | Detailed health (model info, cache stats, uptime) |
| `POST` | `/predict` | Analyze a comment for toxicity |
| `GET` | `/audit-logs?limit=50` | Retrieve recent audit log entries |

### Example Request
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"comment": "You are an idiot"}'
```

### Example Response
```json
{
  "comment": "You are an idiot",
  "masked_comment": "You are an idiot",
  "normalized_comment": "You are an idiot",
  "ml_score": 0.82,
  "llm_label": "toxic",
  "llm_confidence": 0.97,
  "hybrid_score": 0.92,
  "is_toxic": true,
  "risk_level": "HIGH",
  "policy_violation": "🚨 HR Harassment Policy Violated",
  "llm_explanation": "LLM confidence: 97.0% - 🚨 HR Harassment Policy Violated",
  "cached": false,
  "latency_ms": 245.3
}
```

---

## 🧠 How It Works (Summary)

```
User Input → Text Normalizer → PII Masker → ML Model (30%) + LLM (70%) → Hybrid Score → Response
                  ↓                  ↓              ↓                          ↓
           "fcuk" → "fuck"    Strips names    Both models score         > 0.5 = TOXIC
                                              the clean text            > 0.7 = HIGH risk
```

> 📖 **For a complete explanation of every concept, algorithm, and file** — see [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md). That guide covers everything from basic to advanced, written for someone with no prior knowledge of these technologies.

---

## 📝 License

This project was built for SIH 2024 Digital Safety track.
