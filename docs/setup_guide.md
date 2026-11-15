# Setup Guide (Windows PowerShell)

Owner: Member 6 (Integration).

## 0. Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.10, 3.11 or 3.12 (recommended) | `py --version` |
| Node.js | 18+ (20 or 22 recommended) | `node --version` |
| Git | any recent | `git --version` |

Download Python from python.org (tick **"Add python.exe to PATH"**) and Node.js from nodejs.org.
Python 3.13+ may work, but some machine-learning packages are slow to publish wheels for the newest Python versions, so 3.11 is the safest choice.

## 1. Get the code

```powershell
git clone <your-repo-url> EvidenceAI
cd EvidenceAI
```
(Or unzip `EvidenceAI.zip` and `cd` into the `EvidenceAI` folder.)

## 2. Backend

```powershell
cd server

# Create and activate a virtual environment
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If PowerShell says *"running scripts is disabled"*, run this once in the same window, then activate again:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

```powershell
# Install dependencies (large: includes PyTorch; allow 5–15 minutes)
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create your settings file
Copy-Item .env.example .env
notepad .env
```

### Setting `GEMINI_API_KEY`

1. Create a key at <https://aistudio.google.com/apikey>.
2. Put it in `server\.env`: `GEMINI_API_KEY=your_real_key` (no quotes, no spaces).
3. Restart the backend after changing `.env`.

Alternative for one terminal session only (nothing saved to disk):
```powershell
$env:GEMINI_API_KEY = "your_real_key"
```
Without a key the app still works in **retrieval-only mode** (evidence shown, no AI answer).

### Start the backend

```powershell
uvicorn app.main:app --reload --port 8000
```
Check <http://localhost:8000/api/health> in the browser. Interactive API docs: <http://localhost:8000/docs>.

## 3. Frontend (second terminal)

```powershell
cd EvidenceAI\client
npm install
npm run dev
```
Open <http://localhost:5173>. (`npm install` also creates `package-lock.json`; commit it so everyone gets identical versions.)

## 4. Try the endpoints from PowerShell

```powershell
# Health
Invoke-RestMethod http://localhost:8000/api/health

# Upload the sample PDF (curl.exe ships with Windows 10/11; note the .exe)
curl.exe -F "file=@sample_data\evidenceai_sample_paper.pdf" http://localhost:8000/api/documents/upload

# List documents
Invoke-RestMethod http://localhost:8000/api/documents

# Ask a question
$body = @{ question = "What are the limitations of the study?"; document_ids = @("doc_001"); session_id = "session_001" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/chat/ask -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 5

# Evaluation counts
Invoke-RestMethod http://localhost:8000/api/evaluation/summary
```

## 5. Run the automated tests

```powershell
cd EvidenceAI\server
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest -v
```

## 6. Resetting the demo

Stop the backend, then delete the `server\data` folder (uploaded PDFs, ChromaDB, counters). It is recreated automatically.

## Troubleshooting

| Problem | Fix |
|---|---|
| `pip install` reports a version conflict or no matching distribution | The pinned versions in `requirements.txt` could not be install-tested when this project was generated. Try Python 3.11; if it persists, loosen the offending pin (e.g. `PyMuPDF>=1.24`) and tell Member 6 so the pin can be updated. |
| Red banner "Backend not reachable" | Backend not running, or not on port 8000. Check Terminal 1. |
| First upload is very slow | The embedding model is downloading (needs internet). Wait once; later uploads are fast. |
| "The Gemini request failed" | Check the key, the `GEMINI_MODEL` name and your connection. Details are in the backend terminal log. |
| Browser shows a CORS error | The frontend must run at `http://localhost:5173`, or add its address to `CORS_ORIGINS` in `server/.env`. |
| Port already in use | Use another port, e.g. `--port 8001`, and set `VITE_API_BASE_URL=http://localhost:8001/api` in `client/.env`. |
| "OCR is not included" message | The PDF is scanned images. Use a text-based PDF (you can select text in it). |
