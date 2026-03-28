# 📖 Corporate Toxic Comment Detector — Complete Project Guide

> **This file is documentation only. You can safely delete the entire `docs/` folder at any time without breaking anything in the project.**

---

## Table of Contents

1. [What Does This Project Do?](#1-what-does-this-project-do)
2. [The Big Picture — How Everything Connects](#2-the-big-picture--how-everything-connects)
3. [Core Concepts Explained (Zero to Hero)](#3-core-concepts-explained-zero-to-hero)
   - [3.1 Machine Learning (ML) Basics](#31-machine-learning-ml-basics)
   - [3.2 TF-IDF — Turning Words Into Numbers](#32-tf-idf--turning-words-into-numbers)
   - [3.3 Logistic Regression — The ML Classifier](#33-logistic-regression--the-ml-classifier)
   - [3.4 What is a Large Language Model (LLM)?](#34-what-is-a-large-language-model-llm)
   - [3.5 BERT and Toxic-BERT — The Deep Learning Model](#35-bert-and-toxic-bert--the-deep-learning-model)
   - [3.6 Hybrid Scoring — Why We Use Both](#36-hybrid-scoring--why-we-use-both)
   - [3.7 Text Normalization — Anti-Evasion](#37-text-normalization--anti-evasion)
   - [3.8 PII Masking — Privacy Protection](#38-pii-masking--privacy-protection)
   - [3.9 Caching — Speed Optimization](#39-caching--speed-optimization)
   - [3.10 Audit Logging — Compliance](#310-audit-logging--compliance)
4. [Complete File-by-File Breakdown](#4-complete-file-by-file-breakdown)
5. [The Prediction Pipeline — Step by Step](#5-the-prediction-pipeline--step-by-step)
6. [The Anti-Evasion Normalizer — Deep Dive](#6-the-anti-evasion-normalizer--deep-dive)
7. [Frontend Architecture](#7-frontend-architecture)
8. [Algorithms & Data Structures Used](#8-algorithms--data-structures-used)
9. [Technologies & Libraries Used](#9-technologies--libraries-used)
10. [Presentation Talking Points](#10-presentation-talking-points)
11. [Likely Questions & Answers](#11-likely-questions--answers)

---

## 1. What Does This Project Do?

**Problem:** In corporate environments (offices, Slack channels, email, HR systems), people sometimes post toxic, harassing, or threatening messages. Companies need an automated system to detect this in real-time before it causes harm.

**Solution:** This project is a web application where you paste any text and it tells you:
- **Is it toxic?** (YES / NO)
- **How toxic?** (percentage score from 0-100%)
- **Risk level** (LOW / MEDIUM / HIGH)
- **Which corporate policy it violates** (Harassment, Hate Speech, Sexual Harassment, Workplace Safety Threat)

**What makes it special:**
- It uses **two different AI models** working together (a fast one + a smart one)
- It can catch people who **deliberately misspell** bad words (like writing `fcuk` instead of the obvious word, using `@` instead of `a`, writing `f.u.c.k` with dots, etc.)
- It **protects privacy** — if someone's name or email appears in the text, it's hidden before logging
- It keeps a **permanent audit trail** so HR can review past detections

---

## 2. The Big Picture — How Everything Connects

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER'S BROWSER                                │
│                   React Dashboard (localhost:5173)                    │
│    ┌──────────────────┐    ┌──────────────────────────────────────┐  │
│    │  Text Input Box   │    │  Results Panel (Score, Charts, Risk) │  │
│    └────────┬─────────┘    └──────────────────▲───────────────────┘  │
│             │ User types & clicks                │ Results displayed  │
│             │ "Detect Toxicity"                  │                    │
└─────────────┼────────────────────────────────────┼───────────────────┘
              │ HTTP POST /predict                 │ JSON Response
              ▼                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI BACKEND (localhost:8000)                  │
│                                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌───────────┐    ┌───────────┐ │
│  │  Cache    │───▶│ Text         │───▶│ PII       │───▶│ Hybrid    │ │
│  │  Check    │    │ Normalizer   │    │ Masker    │    │ Predictor │ │
│  │          │    │ (9 steps)    │    │ (Presidio)│    │           │ │
│  └──────────┘    └──────────────┘    └───────────┘    │ ┌───────┐ │ │
│       │                                                │ │ML 30% │ │ │
│       │ (if cache hit,                                 │ │LLM 70%│ │ │
│       │  skip all this)                                │ └───────┘ │ │
│       │                                                └─────┬─────┘ │
│       │                                                      │       │
│       │         ┌──────────────┐                             │       │
│       │         │ Audit Logger │◀────────────────────────────┘       │
│       │         │ (SQLite DB)  │                                     │
│       │         └──────────────┘                                     │
└───────┼──────────────────────────────────────────────────────────────┘
        │
        ▼
   ⚡ Instant response if same text was analyzed before
```

**In simple terms:**
1. User types text in the browser
2. Browser sends it to the backend server
3. Backend cleans the text (catches tricks), strips private info, then runs **two AI models**
4. The two AI scores are combined into a final score
5. The result is logged in a database and sent back to the browser
6. The browser displays the verdict with beautiful charts

---

## 3. Core Concepts Explained (Zero to Hero)

### 3.1 Machine Learning (ML) Basics

**What is ML?**
Machine Learning is a way to make computers "learn from examples" instead of being manually programmed with rules.

**Analogy:** Imagine you show a child 10,000 photos labeled "cat" or "dog." After enough examples, the child can look at a *new* photo they've never seen and say "that's a cat." The child learned the *pattern* — they didn't memorize rules like "cats have pointed ears." ML works the same way.

**In this project:**
- We showed our ML model **25,000 real comments** from the internet, each labeled as "toxic" or "not toxic" (this data comes from the Jigsaw Toxicity Challenge dataset by Google)
- The model learned *what toxic language looks like*
- Now when it sees a new comment, it gives a probability (0% to 100%) of toxicity

---

### 3.2 TF-IDF — Turning Words Into Numbers

**The problem:** Computers can't read words. They only understand numbers. So we need a way to convert text like `"you are an idiot"` into numbers.

**TF-IDF stands for:** Term Frequency — Inverse Document Frequency

**How it works (simplified):**
- **TF (Term Frequency):** How often does a word appear in *this one comment*? If "idiot" appears 3 times, its TF is high.
- **IDF (Inverse Document Frequency):** How *rare* is this word across *all comments* in the dataset? Common words like "the", "is", "a" appear everywhere — they get a LOW score. Rare words like "idiot" or "harass" appear in few comments — they get a HIGH score.
- **TF × IDF** = The final score. Words that are **frequent in this comment BUT rare overall** get the highest weight.

**Example:**
```
Comment: "you are a complete idiot, you total idiot"

"you"   → appears often in this comment, BUT it's in every comment → LOW score
"idiot" → appears often in this comment, AND it's rare overall   → HIGH score
"a"     → common everywhere                                      → VERY LOW score
```

**Result:** Each comment becomes a list of ~5000 numbers (one per word in our vocabulary). Toxic words like "idiot", "hate", "kill" have high numbers. Neutral words have low numbers.

**In our project:** The file `models/tfidf_vectorizer.pkl` stores the learned vocabulary and word weights. It was trained by `src/models/train_peft.py`.

**Settings we used:**
```python
TfidfVectorizer(
    max_features=5000,     # only keep top 5000 most useful words
    stop_words='english',  # ignore "the", "is", "a", etc.
    ngram_range=(1, 2),    # consider single words AND word pairs ("go away", "you idiot")
    min_df=3               # ignore words that appear in fewer than 3 comments
)
```

---

### 3.3 Logistic Regression — The ML Classifier

**What is it?**
Logistic Regression is one of the simplest and fastest ML classification algorithms. Despite its name, it's used for *classification* (putting things into categories), not regression.

**How it works (simplified):**
After TF-IDF converts text into numbers, Logistic Regression draws a mathematical "boundary line." Everything on one side = toxic, everything on the other side = safe.

**Analogy:** Imagine plotting all 25,000 comments on a map. Toxic ones cluster in one area (they have similar word patterns). Safe ones cluster in another area. Logistic Regression finds the best line that separates the two clusters.

**Why we chose it:**
- It's **extremely fast** (predicts in <1 millisecond)
- It gives a **probability** (not just yes/no) — e.g., "82% likely toxic"
- It works well with TF-IDF features
- It gets **88.6% accuracy** on our test data

**Settings we used:**
```python
LogisticRegression(
    class_weight='balanced',  # handles the fact that most comments are safe (not 50/50)
    max_iter=2000,            # maximum training iterations
    random_state=42           # ensures results are reproducible
)
```

**`class_weight='balanced'`** is important because in real data, maybe 90% of comments are safe and only 10% are toxic. Without this setting, the model could cheat by always predicting "safe" and still be "90% accurate." The `balanced` setting forces the model to pay extra attention to the rare toxic examples.

**In our project:** The trained model is saved as `models/toxic_classifier.pkl`.

---

### 3.4 What is a Large Language Model (LLM)?

**What is it?**
An LLM is a type of AI that has been trained on *massive amounts of text* (books, websites, Wikipedia, etc.) and has learned to deeply understand language — context, meaning, sarcasm, nuance.

**How is it different from the ML model above?**

| Feature | ML (TF-IDF + LogisticRegression) | LLM (Toxic-BERT) |
|---|---|---|
| **Understands word order?** | ❌ No — treats "dog bites man" and "man bites dog" the same | ✅ Yes — understands word order changes meaning |
| **Understands context?** | ❌ No — looks at words in isolation | ✅ Yes — understands "you're killing it" (praise) vs "I'll kill you" (threat) |
| **Speed** | ⚡ Very fast (<1ms) | 🐢 Slower (~200ms) |
| **Accuracy** | 88.6% | 95% |
| **Size** | ~7 MB | ~400 MB |

**Analogy:** The ML model is like a word-counting robot — it counts suspicious words and makes a guess. The LLM is like someone who actually *reads and understands* the sentence.

---

### 3.5 BERT and Toxic-BERT — The Deep Learning Model

**BERT** (Bidirectional Encoder Representations from Transformers) is a famous AI model created by Google in 2018. It reads text *bidirectionally* — it looks at words before AND after each word to understand context.

**Toxic-BERT** is a specialized version of BERT. Someone took the original BERT model and *fine-tuned* it (trained it further) specifically on the Jigsaw toxic comment dataset. So it's an expert at detecting toxic language.

- **Model name:** `unitary/toxic-bert`
- **Source:** Hugging Face Model Hub (a website where researchers share pre-trained models)
- **How we use it:** We load it using the `transformers` library by Hugging Face

**What "Transformer" means:**
A Transformer is the architecture (design blueprint) behind BERT. Its key innovation is the **Attention Mechanism** — the model can "pay attention" to the most important words in a sentence. When analyzing "you're a terrible manager", the attention mechanism focuses on "terrible" and connects it to the sentiment about "manager."

**In our project:** The file `src/rag/llm_rag.py` loads Toxic-BERT and wraps it in a class that:
1. Runs the model on the input text
2. Gets a label (toxic, hate, sexual, threat) and a confidence score (0-100%)
3. Maps the label to a **corporate policy violation** (e.g., "toxic" → "HR Harassment Policy Violated")

---

### 3.6 Hybrid Scoring — Why We Use Both

We use **both** models because each has strengths the other lacks:

```
Final Score = (ML Score × 0.30) + (LLM Score × 0.70)
```

- **ML gets 30% weight** — it's the fast first-pass, catches obvious toxicity
- **LLM gets 70% weight** — it's the deep expert, catches nuanced/contextual toxicity

**Example with "you're killing it!"** (this is actually a COMPLIMENT):
- ML model: Sees the word "killing" → scores 60% toxic ❌ (wrong)
- LLM model: Understands the phrase is positive → scores 5% toxic ✅ (right)
- Hybrid: (0.60 × 0.30) + (0.05 × 0.70) = 0.18 + 0.035 = **21.5%** → **SAFE** ✅

**Risk Level Classification:**
```
Score > 0.7  →  HIGH risk    (🔴 definitely toxic)
Score > 0.3  →  MEDIUM risk  (🟡 borderline, needs review)
Score ≤ 0.3  →  LOW risk     (🟢 probably safe)
Score > 0.5  →  "is_toxic" = true
```

---

### 3.7 Text Normalization — Anti-Evasion

**The problem:** People who want to be toxic but avoid detection will deliberately distort their words:
- `f@ck` (using symbols instead of letters)
- `f.u.c.k` (inserting dots between letters)
- `fuuuuck` (repeating characters)
- `fcuk` (swapping letter order)
- Using Cyrillic `а` instead of Latin `a` (they look identical but are different characters)

**Our solution:** A 9-step normalizer that processes text *before* the AI models see it. It converts all tricks back to the plain word. This is covered in detail in [Section 6](#6-the-anti-evasion-normalizer--deep-dive).

---

### 3.8 PII Masking — Privacy Protection

**PII** = Personally Identifiable Information (names, email addresses, phone numbers, SSNs).

**Why it matters:** If someone reports "John Smith from accounting is a terrible person", we need to detect it's toxic — but we should NOT store "John Smith" in our audit log. That would create a privacy liability.

**How it works:**
We use **Microsoft Presidio** — an open-source PII detection engine. It uses:
- **Named Entity Recognition (NER):** An AI model that identifies names, locations, organizations in text
- **Pattern matching:** Regex patterns for emails (`xxx@xxx.com`), phone numbers, SSNs

**Example:**
```
Input:  "John Smith is a terrible manager, call him at john@company.com"
Output: "<PERSON> is a terrible manager, call him at <EMAIL_ADDRESS>"
```

**In our project:** The file `src/utils/pii_masker.py` runs Presidio's Analyzer + Anonymizer. The masked text is what gets stored in the audit log, never the original.

---

### 3.9 Caching — Speed Optimization

**The problem:** Running the LLM model takes ~200-500ms per request. If 100 people report the same spam message, we'd waste compute resources.

**Solution:** An in-memory cache (Python dictionary) that stores `{text → result}`. If the exact same text is submitted again, we return the cached result instantly (~1ms).

**In our project:** `src/utils/cache.py` implements this. It also tracks hit/miss counts for the health endpoint.

---

### 3.10 Audit Logging — Compliance

**Why:** In an enterprise, you can't just detect toxicity and forget it. HR and legal departments need records. "When was this flagged? What was the score? What policy was violated?"

**How:** We use **SQLAlchemy** (a Python ORM — Object-Relational Mapper) that stores each prediction's result into a **SQLite** database file (`data/corporate_audit.db`).

**What gets logged:**
| Column | Description |
|---|---|
| `id` | Auto-incrementing row number |
| `timestamp` | When the prediction was made |
| `original_text_masked` | The PII-masked version of the text (NOT the original) |
| `ml_score` | ML model's toxicity score |
| `llm_confidence` | LLM model's toxicity score |
| `hybrid_score` | Combined final score |
| `risk_level` | HIGH / MEDIUM / LOW |
| `policy_violation` | Which company policy was violated |

---

## 4. Complete File-by-File Breakdown

### Backend — `src/api/main.py`
**What it is:** The FastAPI web server — the "front door" of the backend.

**What it does:**
- Creates a FastAPI application with 4 endpoints (`/`, `/health`, `/predict`, `/audit-logs`)
- Configures **CORS** (Cross-Origin Resource Sharing) — this is a browser security mechanism. Without it, the React frontend on `localhost:5173` would be blocked from calling the API on `localhost:8000`
- Defines request/response models using **Pydantic** (data validation library)
- Handles the request flow: check cache → run predictor → store in cache → return result
- Measures latency (how long each request took)

**Key concept — Pydantic:**
Pydantic is a library that validates incoming data. If someone sends a request without the `comment` field, Pydantic automatically rejects it with a clear error message before our code even runs.

---

### Backend — `src/models/predictor.py`
**What it is:** The orchestrator — it coordinates the entire prediction pipeline.

**The flow (in order):**
1. **Normalize** the text (anti-evasion)
2. **Mask PII** (privacy protection)
3. **ML Score** — TF-IDF vectorize the text → run through Logistic Regression → get probability
4. **LLM Score** — run through Toxic-BERT → get label + confidence
5. **Combine** the scores: `hybrid_score = (ML × 0.30) + (LLM × 0.70)`
6. **Determine** risk level and toxicity flag
7. **Log** the result to the audit database
8. **Return** everything

**Important design decision:** Normalization runs BEFORE PII masking. This matters because if we masked first, the PII engine could mistakenly classify obfuscated words like `fcuk` as person names and hide them, preventing the normalizer from ever seeing them.

---

### Backend — `src/models/train_peft.py`
**What it is:** The training script that creates the ML model. You run this once to produce the `.pkl` files.

**Step-by-step:**
1. Load `data/cleaned_train.csv` (25,000 comments)
2. Drop any empty/NaN rows
3. Split into 80% training / 20% validation
4. Fit a TF-IDF vectorizer on the training data (learns the vocabulary)
5. Train a Logistic Regression model on the TF-IDF features
6. Evaluate accuracy on the validation set
7. Save both the model and vectorizer as `.pkl` files (pickle format — Python's serialization)

**You do NOT need to rerun this** — the trained models are already saved in `models/`.

---

### Backend — `src/rag/llm_rag.py`
**What it is:** The LLM (Toxic-BERT) wrapper.

**What "RAG" means:**
RAG stands for Retrieval-Augmented Generation — it's a technique where you retrieve relevant documents and feed them to an LLM. In our project, this is a *simulation* of RAG — instead of retrieving documents, we map model labels to a hardcoded corporate policy dictionary. In a real enterprise system, this would query an actual company policy database.

**How it works:**
1. Loads `unitary/toxic-bert` from Hugging Face (downloads ~400MB on first run, then cached)
2. Runs `text-classification` pipeline on the input
3. Gets a label (`toxic`, `hate`, `sexual`, `threat`) and a confidence score
4. Maps the label to a corporate policy string

**`device=-1` means:** Use CPU, not GPU. If you had an NVIDIA GPU with CUDA, you'd use `device=0` for much faster inference.

---

### Backend — `src/utils/text_normalizer.py`
**What it is:** The anti-evasion text normalizer (366 lines). The most complex utility module.

See [Section 6](#6-the-anti-evasion-normalizer--deep-dive) for the full deep dive.

---

### Backend — `src/utils/pii_masker.py`
**What it is:** Privacy protection using Microsoft Presidio.

**How Presidio works under the hood:**
1. **Analyzer** — scans text using a combination of:
   - A pre-trained NER (Named Entity Recognition) model based on spaCy
   - Regular expressions for structured data (emails, phone numbers, SSNs)
   - A scoring system that assigns confidence to each detected entity
2. **Anonymizer** — replaces detected entities with placeholder tags like `<PERSON>`, `<EMAIL_ADDRESS>`

---

### Backend — `src/utils/audit_logger.py`
**What it is:** Database logging for compliance.

**Key concepts:**
- **SQLAlchemy** — A Python library that lets you interact with databases using Python objects instead of writing raw SQL queries
- **ORM (Object-Relational Mapper)** — Maps Python classes to database tables. Our `AuditLog` class = the `inference_logs` table
- **SQLite** — A lightweight database stored as a single file (`data/corporate_audit.db`). No server needed — it's just a file on disk

---

### Backend — `src/utils/cache.py`
**What it is:** Simple in-memory cache using a Python dictionary.

**How it works:**
- Stores `{text_input: prediction_result}` in a Python `dict`
- If the same text is sent again → return stored result instantly
- Tracks `hits` (cache found) and `misses` (cache not found) for monitoring

**Limitation:** The cache resets when the server restarts (it's in-memory, not persistent). In production, you'd use Redis.

---

### Backend — `src/data/prepare_data.py`
**What it is:** Data preprocessing script.

**What it does:**
1. Loads the raw Jigsaw dataset (`data/train.csv`)
2. Ensures all label columns exist (`toxic`, `severe_toxic`, `obscene`, etc.)
3. Cleans text (lowercase, strip whitespace)
4. Randomly samples 25,000 rows (for faster training)
5. Saves as `data/cleaned_train.csv`
6. Creates `config.yaml` with training parameters

---

### Frontend — `frontend/src/App.jsx`
**What it is:** The entire React dashboard UI in a single component file.

**Major sections:**
- **Hero Landing** — animated intro with gradient text
- **Features Grid** — cards showcasing system capabilities
- **Analyze Section** — text input, quick-fill buttons, "Detect Toxicity" button
- **Results Panel** — hybrid score, risk badges, ML vs LLM breakdown, bar chart
- **Audit Log** — table of past predictions fetched from `/audit-logs`
- **Responsive Navbar** — navigation links + system online indicator

**Key technologies:**
- **React** — JavaScript library for building user interfaces
- **Vite** — Fast development server and build tool (replaces older tools like Webpack)
- **Recharts** — React charting library (for the bar chart comparing ML/LLM/Hybrid)
- **Lucide React** — Icon library

---

### Config Files

| File | Purpose |
|---|---|
| `config.yaml` | Stores model and training configs (max_length, batch_size, etc.) |
| `.env.example` | Template for environment variables (API host, model paths, DB path) |
| `Dockerfile` | Multi-stage Docker build — first builds the React frontend, then bundles with the Python backend |
| `docker-compose.yml` | Defines the containerized service with port mapping, volumes, and health checks |
| `requirements.txt` | All Python package dependencies |

---

## 5. The Prediction Pipeline — Step by Step

Here's exactly what happens when someone types `"fcuk you, John"` and clicks **Detect Toxicity**:

```
Step 1: FRONTEND
  User types "fcuk you, John" → clicks button
  React app sends HTTP POST to http://localhost:8000/predict
  Request body: {"comment": "fcuk you, John"}

Step 2: API RECEIVES REQUEST (src/api/main.py)
  FastAPI validates the request (Pydantic checks "comment" field exists)
  Strips whitespace → "fcuk you, John"
  Checks cache → not found (cache miss)
  Calls predictor.predict("fcuk you, John")

Step 3: TEXT NORMALIZATION (src/utils/text_normalizer.py)
  Input: "fcuk you, John"
  Step 3a: Unicode normalization   → "fcuk you, John" (no change)
  Step 3b: Homoglyph replacement   → "fcuk you, John" (no change)
  Step 3c: Leet speak reversal     → "fcuk you, John" (no change)
  Step 3d: Strip separators        → "fcuk you, John" (no change)
  Step 3e: Reduce repetition       → "fcuk you, John" (no change)
  Step 3f: Slur pattern matching   → "fcuk you, John" (no match - wrong letter order)
  Step 3g: TRANSPOSITION matching  → "fuck you, John" ✅ CAUGHT! regex \bf+c+u+k+ matched
  Step 3h: Anagram detection       → "fuck you, John" (already normalized)
  Step 3i: Fuzzy matching          → "fuck you, John" (already normalized)
  Output: "fuck you, John"

Step 4: PII MASKING (src/utils/pii_masker.py)
  Input: "fuck you, John"
  Presidio detects "John" as PERSON entity
  Output: "fuck you, <PERSON>"

Step 5: ML SCORING (TF-IDF + LogisticRegression)
  Input: "fuck you, John" (normalized text, not masked)
  TF-IDF vectorizes into 5000 numbers
  LogisticRegression outputs probability: 0.85 (85% toxic)

Step 6: LLM SCORING (Toxic-BERT)
  Input: "fuck you, John" (normalized text)
  BERT processes through transformer layers
  Output: label="toxic", confidence=0.992 (99.2% toxic)
  Policy mapped: "🚨 HR Harassment Policy Violated"

Step 7: HYBRID COMBINATION
  hybrid_score = (0.85 × 0.30) + (0.992 × 0.70)
               = 0.255 + 0.694
               = 0.949 (94.9%)
  is_toxic: 0.949 > 0.5 → TRUE
  risk_level: 0.949 > 0.7 → "HIGH"

Step 8: AUDIT LOG (src/utils/audit_logger.py)
  Writes to SQLite: {masked_text: "fuck you, <PERSON>", score: 0.949, risk: HIGH, ...}

Step 9: CACHE STORE (src/utils/cache.py)
  Stores: cache["fcuk you, John"] = {full result object}

Step 10: API RETURNS RESPONSE
  Returns JSON with all scores, labels, risk levels
  Includes latency_ms and cached=false

Step 11: FRONTEND RENDERS
  React receives JSON → updates state → renders:
  - 🔴 TOXIC badge + HIGH risk badge
  - 95% hybrid score with red progress bar
  - ML: 85% and LLM: 99% side-by-side
  - Bar chart visualization
  - Policy violation message
```

---

## 6. The Anti-Evasion Normalizer — Deep Dive

This is the **most technically interesting** part of the project. The normalizer has **9 sequential steps**, each catching a different type of evasion:

### Step 1: Unicode Normalization (NFKD)
**What:** Converts fancy Unicode characters to their standard form.
**Example:** The character `ﬁ` (a single Unicode ligature) → becomes `fi` (two separate characters).
**Algorithm:** Uses the NFKD (Normalization Form Compatibility Decomposition) standard, which is a Unicode standard for decomposing characters.

### Step 2: Homoglyph Replacement
**What:** Replaces characters that *look identical* but are from different alphabets.
**Example:** Cyrillic `а` (Unicode U+0430) looks exactly like Latin `a` (Unicode U+0061), but they're different characters. A naive system wouldn't match `fаck` (with Cyrillic а) against "fuck".
**Method:** Dictionary lookup — we have a map of ~25 known homoglyphs to their ASCII equivalents.

### Step 3: Leet Speak Reversal
**What:** Converts number/symbol substitutions back to letters.
**Map:** `@ → a`, `! → i`, `1 → i`, `3 → e`, `0 → o`, `$ → s`, `5 → s`, `7 → t`, `+ → t`, `# → h`, `8 → b`, etc.
**Smart feature:** Only applies if the symbol is adjacent to other letters (so `$100` stays as `$100`, but `@$$hole` becomes `asshole`).

### Step 4: Separator Stripping
**What:** Removes dots, dashes, spaces inserted between letters.
**Example:** `f.u.c.k` → `fuck`, `b-i-t-c-h` → `bitch`
**Algorithm:** Regex pattern that matches: letter + separator + letter + separator + letter (3+ letters with separators), then strips the separators.

### Step 5: Repetition Reduction
**What:** Reduces excessive character repetition to max 2.
**Example:** `fuuuuuuck` → `fuuck`, `shiiiiiit` → `shiit`
**Algorithm:** Regex `(.)\1{2,}` → `\1\1` (any character repeated 3+ times → reduced to 2).

### Step 6: Slur Pattern Matching
**What:** Pre-compiled regex patterns for known obfuscated slurs.
**Example patterns:**
- `\bf+[\W_]*[uv]+[\W_]*[ck]+` matches `f_u_c_k`, `fvck`, `f__uck`, etc.
- `\bs+[\W_]*h+[\W_]*[i!1]+[\W_]*t+` matches `sh!t`, `sh1t`, `s.h.i.t`, etc.
**Count:** 15 pattern families covering all major slurs.

### Step 7: Transposition Pattern Matching
**What:** Pre-compiled regex patterns for known letter-swapped spellings.
**Example:** `fcuk` matches `\bf+c+u+k+`, `btich` matches `\bb+t+i+c+h+`
**Includes suffix support:** `fcking`, `fcuked`, `fcuks` all get caught.
**Count:** 20 transposition patterns.

### Step 8: Anagram Detection (Sorted-Letter Signature)
**What:** Sorts the letters of each word alphabetically and checks if the sorted version matches a known toxic word's sorted letters.

**Algorithm:**
```
"fcuk" → sort letters → "cfku"
"fuck" → sort letters → "cfku"
Both sort to "cfku" → MATCH! → Replace with "fuck"
```

**Safe-word protection:** Some legitimate words are anagrams of toxic words (e.g., "this" is an anagram of "shit" — both sort to "hist"). We maintain a whitelist of ~100 safe English words to prevent false positives.

**Data structure used:** Python dictionary `ANAGRAM_MAP` = `{sorted_letters: canonical_word}` — O(1) lookup time.

### Step 9: Fuzzy Matching (Damerau-Levenshtein Distance)
**What:** Catches near-miss misspellings within 1 edit operation.

**Damerau-Levenshtein distance** measures the minimum number of operations to transform one string into another. Allowed operations:
1. **Insertion** — add a character (`fck` → `fuck`, distance = 1)
2. **Deletion** — remove a character (`fucck` → `fuck`, distance = 1)
3. **Substitution** — change a character (`fuxk` → `fuck`, distance = 1)
4. **Transposition** — swap two adjacent characters (`fcuk` → `fuck`, distance = 1)

**Algorithm:** Dynamic programming — fills a 2D matrix where `d[i][j]` = minimum edits to transform the first `i` characters of word1 into the first `j` characters of word2. Time complexity: O(n × m) where n, m are word lengths.

**Safety:** Only replaces if distance = exactly 1 (very conservative to avoid false positives). Only checks words between 3-8 characters long. Skips words in the safe-word whitelist.

---

## 7. Frontend Architecture

### Technology Stack
- **React 19** — UI library (component-based architecture)
- **Vite 8** — Build tool and dev server (extremely fast hot-reloading)
- **Recharts** — React chart library (renders the ML/LLM/Hybrid bar chart)
- **Lucide React** — Icon library (Shield, Send, AlertTriangle, etc.)

### How the Frontend Communicates with the Backend
The frontend uses the browser's built-in **Fetch API** to make HTTP requests:
```javascript
const response = await fetch('http://localhost:8000/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ comment: inputText })
});
const data = await response.json();
```

### State Management
Uses React's `useState` hook to manage:
- `comment` — the user's input text
- `result` — the prediction response from the API
- `loading` — whether a request is in progress
- `auditLogs` — array of past predictions from `/audit-logs`

---

## 8. Algorithms & Data Structures Used

| Algorithm / Technique | Where Used | Purpose |
|---|---|---|
| **TF-IDF** (Term Frequency—Inverse Document Frequency) | `train_peft.py`, `predictor.py` | Convert text to numerical vectors for ML |
| **Logistic Regression** | `train_peft.py`, `predictor.py` | Fast binary classification (toxic vs safe) |
| **BERT Transformer** (Attention Mechanism) | `llm_rag.py` | Deep contextual text understanding |
| **Weighted Ensemble** | `predictor.py` | Combine ML (30%) + LLM (70%) scores |
| **Regex Pattern Matching** | `text_normalizer.py` | Detect obfuscated slurs and leet speak |
| **Damerau-Levenshtein Distance** (Dynamic Programming) | `text_normalizer.py` | Fuzzy matching for misspelled slurs |
| **Anagram Detection** (Sorted-Key Hashing) | `text_normalizer.py` | Catch letter-transposition evasions |
| **Named Entity Recognition (NER)** | `pii_masker.py` (via Presidio) | Detect and mask personal information |
| **In-Memory Caching** (Hash Map) | `cache.py` | O(1) lookup for repeated queries |
| **ORM** (Object-Relational Mapping) | `audit_logger.py` (via SQLAlchemy) | Persist predictions to SQLite database |
| **CORS** (Cross-Origin Resource Sharing) | `main.py` | Allow frontend on port 5173 to call API on port 8000 |
| **Singleton Pattern** | All utility modules | Ensure only one instance of each service exists |

---

## 9. Technologies & Libraries Used

### Backend (Python)
| Library | Version | Purpose |
|---|---|---|
| **FastAPI** | Latest | High-performance async REST API framework |
| **Uvicorn** | Latest | ASGI server to run FastAPI |
| **scikit-learn** | Latest | ML library (TF-IDF, LogisticRegression, train/test splitting) |
| **transformers** (Hugging Face) | Latest | Load and run pre-trained BERT models |
| **torch** (PyTorch) | Latest | Deep learning framework (backend for transformers) |
| **presidio-analyzer** | Latest | PII entity detection (names, emails, phones, SSN) |
| **presidio-anonymizer** | Latest | PII replacement with placeholder tags |
| **SQLAlchemy** | Latest | ORM for SQLite database access |
| **joblib** | Latest | Serialization for ML models (.pkl files) |
| **pandas** | Latest | Data loading and manipulation (CSV processing) |
| **pydantic** | Latest | Data validation (API request/response models) |

### Frontend (JavaScript)
| Library | Purpose |
|---|---|
| **React** | Component-based UI framework |
| **Vite** | Fast dev server + build tool |
| **Recharts** | Bar charts for score visualization |
| **Lucide React** | Icon components |

### Infrastructure
| Tool | Purpose |
|---|---|
| **Docker** | Containerization for consistent deployment |
| **Docker Compose** | Multi-service orchestration |
| **SQLite** | Lightweight embedded database |

---

## 10. Presentation Talking Points

### Opening (30 seconds)
> "This is a Corporate Toxic Comment Detector — an enterprise tool that uses a hybrid of traditional Machine Learning and a Large Language Model to detect harassing, threatening, or hateful content in corporate communications. It's designed to help HR teams enforce workplace safety policies in real-time."

### The Problem (1 minute)
> "Online harassment in workplaces is growing. But detecting it isn't as simple as searching for bad words — people deliberately misspell or obfuscate their messages to avoid filters. Writing `fcuk` instead of the obvious word, using `@` instead of `a`, or inserting dots between letters. Our system catches all of these tricks."

### Architecture Demo (2 minutes)
> "The system has three main layers:
> 1. **An anti-evasion normalizer** that processes the text through 9 steps to undo obfuscation tricks — leet speak reversal, anagram detection, fuzzy edit-distance matching, and more.
> 2. **A hybrid AI engine** combining a fast ML model (TF-IDF + Logistic Regression at 88% accuracy) with a deep Transformer-based LLM (Toxic-BERT at 95% accuracy). These are ensembled with a 30/70 weight.
> 3. **Enterprise protections** — PII masking with Microsoft Presidio ensures personal information never hits our logs, and every prediction is audit-logged to a SQLite database for HR compliance."

### Live Demo (2 minutes)
Show these inputs in order:
1. `"Great job team!"` → Safe, LOW risk (proves it doesn't flag everything)
2. `"You are an idiot"` → Toxic, HIGH risk (catches obvious toxicity)
3. `"fcuk you"` → Toxic, HIGH risk (catches transposition evasion)
4. `"f.u.c.k this company"` → Toxic, HIGH risk (catches separator evasion)
5. `"You're killing it! Great presentation"` → Safe, LOW risk (LLM understands context)

### Technical Highlights (1 minute)
> "Key algorithmic highlights:
> - **Damerau-Levenshtein distance** with dynamic programming for fuzzy matching
> - **Sorted-key anagram detection** with safe-word whitelisting to prevent false positives
> - **BERT Transformer attention mechanism** for contextual understanding
> - **Weighted ensemble scoring** to balance speed and accuracy"

### Closing (30 seconds)
> "This system is Docker-ready for deployment, includes API documentation via Swagger, and the architecture supports scaling to Redis caching, GPU inference, and real-time Slack/Teams integration."

---

## 11. Likely Questions & Answers

### Q: "Why not just use a list of bad words?"
**A:** A bad-word list is trivially easy to bypass — people use misspellings (`fcuk`), leet speak (`@$$h0le`), spacing (`f u c k`), or context-dependent phrases. Our system handles all of these through the 9-step normalizer AND the BERT LLM which understands context.

### Q: "Why two models? Why not just the LLM?"
**A:** The LLM (Toxic-BERT) is accurate but slow (~200ms per prediction). The ML model is less accurate but instant (<1ms). In a production system processing thousands of messages per second (e.g., Slack), you'd use the ML model as a fast pre-filter and only escalate uncertain cases to the LLM. The hybrid approach gives us the best of both worlds.

### Q: "What dataset did you train on?"
**A:** The Jigsaw Toxic Comment Classification Challenge dataset from Google/Jigsaw. It contains ~160,000 Wikipedia comments labeled for toxicity, severe toxicity, obscenity, threat, insult, and identity hate. We use a 25,000-sample subset for faster training.

### Q: "What's the 88.6% accuracy for the ML model? Isn't that low?"
**A:** For a bag-of-words model (TF-IDF + Logistic Regression), 88.6% is strong. The ~11.4% error is usually on ambiguous cases like sarcasm or context-dependent phrases — which is exactly what the LLM covers with its 95% accuracy. The hybrid combination achieves ~92% effective accuracy.

### Q: "What happens if someone uses a language other than English?"
**A:** Currently, the system is English-only. The TF-IDF vectorizer is trained on English text, and Toxic-BERT is an English model. For multilingual support, you'd replace Toxic-BERT with a multilingual model like `xlm-roberta-base` and retrain the TF-IDF on multilingual data.

### Q: "Can this be deployed to production?"
**A:** Yes. The Docker setup already supports one-command deployment. For enterprise scale, you'd add: Redis for persistent caching, PostgreSQL for the audit database, GPU instances for faster LLM inference, and rate limiting on the API.

### Q: "What's the Singleton Pattern you used?"
**A:** Each utility module (normalizer, PII masker, cache, audit logger, LLM analyzer) creates exactly ONE instance at module load time. This avoids the overhead of loading models multiple times and ensures consistent state (e.g., cache hit counts are accurate). The instance is shared across all API requests.

### Q: "How does the Damerau-Levenshtein algorithm work?"
**A:** It's a dynamic programming algorithm that builds a matrix to find the minimum number of operations (insert, delete, substitute, or transpose) to convert one string into another. If the distance between an input word and a toxic word is exactly 1, we treat it as an intentional misspelling. For example, `fuk` → `fuck` (1 insertion), `fcuk` → `fuck` (1 transposition).

### Q: "What is CORS and why do you need it?"
**A:** CORS (Cross-Origin Resource Sharing) is a browser security feature. When your React app on `localhost:5173` tries to call the API on `localhost:8000`, the browser blocks it by default because they're different "origins" (different ports). Our FastAPI middleware explicitly allows the frontend's origin, so the browser permits the requests.

### Q: "What does the `itertools.permutations` import do?"
**A:** It's imported for potential future use (generating all possible letter arrangements of a word). Currently, the anagram detection uses a more efficient sorted-key approach instead of generating all permutations.

---

> **📌 Remember:** This entire `docs/` folder is standalone documentation. Deleting it will not affect any part of the working application. All actual project code lives in `src/`, `frontend/`, and `models/`.
