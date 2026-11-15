# EvidenceAI — Research Assistant With Verifiable Answers

Upload PDF research papers or reports, ask questions in plain English, and get answers that point to the **exact page and passage** they came from. If the documents do not contain the answer, EvidenceAI says **"Insufficient evidence in the uploaded documents"** instead of guessing.

> **Student prototype / educational demonstration.** It is *not* a production research tool and must not be used for medical, legal or other high-stakes decisions. Accuracy, security and scalability have not been validated.

## How it works (30 seconds)

```
PDF ──► extract text per page (PyMuPDF) ──► clean + split into overlapping chunks
    ──► embeddings (Sentence Transformers) ──► store in ChromaDB (with doc ID + page number)

Question ──► embed ──► find the most similar chunks ──► drop weak matches
         ──► nothing relevant? → "insufficient_evidence" (Gemini is NOT called)
         ──► otherwise ask Gemini to answer ONLY from numbered evidence [E1], [E2] ...
         ──► verify the [E#] markers against the real evidence ──► show answer + citation cards
```

If no Gemini key is configured the app still runs in a clearly labelled **retrieval-only mode**: it shows the retrieved evidence but writes **no** AI answer.

## Quick start (Windows PowerShell)

You need **Python 3.10–3.12** and **Node.js 18+** (20 or 22 recommended). Full details: [docs/setup_guide.md](docs/setup_guide.md).

**Terminal 1 — backend**

```powershell
cd EvidenceAI\server
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env        # then open .env and paste your GEMINI_API_KEY (optional)
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend**

```powershell
cd EvidenceAI\client
npm install
npm run dev
```

Open **http://localhost:5173**, upload `sample_data/evidenceai_sample_paper.pdf`, and ask *"What are the limitations of the study?"*

> The first upload downloads the embedding model (about 90 MB) and needs internet. Later runs are fast.

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | `server/.env` | Google Gemini key from <https://aistudio.google.com/apikey>. Empty = retrieval-only mode. |
| `GEMINI_MODEL` | `server/.env` | Gemini model name (default `gemini-2.5-flash`; change it if Google retires it). |
| `MIN_RELEVANCE_SCORE` | `server/.env` | Evidence threshold (default `0.30`). **Needs tuning** with your documents. |
| `VITE_API_BASE_URL` | `client/.env` | Backend URL (default `http://localhost:8000/api`). |

All settings: [server/.env.example](server/.env.example). **Never commit a real `.env` file.**

## Project structure

```
EvidenceAI/
├─ client/                      React + Vite frontend            (Member 1)
│  └─ src/ components/ pages/ services/api.js App.jsx index.css
├─ server/                      FastAPI backend
│  ├─ app/
│  │  ├─ main.py  schemas.py  routes/                            (Member 2)
│  │  ├─ document_processing/   extract, clean, chunk, upload    (Member 3)
│  │  ├─ embeddings/ retrieval/ rag/                             (Member 4)
│  │  ├─ citations/ evaluation/                                  (Member 5)
│  │  └─ core/                  config, errors, registry, deps   (Members 2 + 6)
│  ├─ tests/  requirements.txt  requirements-dev.txt  .env.example
├─ docs/                        architecture, API, setup, testing, team guides (Member 6)
├─ sample_data/                 fictional sample PDF + generator script
└─ .github/                     CI workflow, PR template        (Member 6)
```

## Documentation

- [Setup guide](docs/setup_guide.md) · [API contracts](docs/api_contracts.md) · [Architecture](docs/architecture.md)
- [Testing guide and results](docs/testing_guide.md) · [5-minute demo script](docs/demo_script.md)
- [Team responsibilities](docs/team_responsibilities.md) · [Team development guide (Git workflow)](docs/team_development_guide.md)
- [Known limitations and future work](docs/known_limitations.md)

## Privacy note

When a Gemini key is configured, the question and the retrieved passages are sent to Google's Gemini API. Do not upload confidential documents unless that is acceptable. PDFs and the ChromaDB database stay on your computer in `server/data/` (git-ignored).
