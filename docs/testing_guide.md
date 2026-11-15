# Testing Guide and Test Results

Owner: Member 6 (Integration).

## How to run the automated tests

```powershell
cd EvidenceAI\server
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest -v
```
Tests that need an optional package skip themselves (and say why) if it is missing:
`test_api.py` needs `fastapi` + `httpx`; `test_pdf_extraction.py` needs `PyMuPDF`.
**On your machine, after `pip install -r requirements-dev.txt`, nothing should be skipped.** If everything passes there, update the table below with your real result.

## What the automated tests cover

| Required area | Test file | Notes |
|---|---|---|
| Health endpoint | `test_api.py::test_health` | needs FastAPI |
| PDF upload validation | `test_upload_validation.py` (service level), `test_api.py` (HTTP level) | wrong extension, fake PDF content, empty, too large (413), path-traversal names, scanned PDF → `no_text`, failed extraction, no leaked error details |
| PDF text extraction + page numbering | `test_pdf_extraction.py` | real PyMuPDF; 1-based page numbers, blank pages, corrupt PDF, bundled sample PDF |
| Chunk metadata preservation | `test_chunking.py` | document ID, filename, page, unique IDs, no cross-page mixing, verbatim text + exact offsets |
| Retrieval | `test_retrieval.py` | uses a **fake word-overlap embedder**; verifies plumbing (page, sorting, filters, threshold), **not** semantic quality |
| Insufficient-evidence behaviour | `test_pipeline.py`, `test_citations.py` | LLM never called when nothing relevant; model refusal; uncited answers withheld; fabricated `[E#]` IDs stripped |
| Chat response structure | `test_pipeline.py`, `test_api.py` | required citation fields, statuses, retrieval-only and LLM-error modes, metrics counts |

## Test results (generated in the build sandbox)

Environment: Linux, Python 3.13, pytest 9.1.1. **FastAPI, httpx, PyMuPDF, ChromaDB, Sentence Transformers and google-genai were NOT installed** (no network for `pip`).

```
python -m pytest -q -rs
43 passed, 2 skipped
SKIPPED tests/test_api.py            could not import 'fastapi'
SKIPPED tests/test_pdf_extraction.py could not import 'fitz'
```
Lint (`ruff check --select F,E9`: undefined names, unused imports, syntax errors): passed.

| Test module | Result in the sandbox |
|---|---|
| `test_chunking.py` | **passed** |
| `test_upload_validation.py` | **passed** |
| `test_retrieval.py` (fake embedder) | **passed** |
| `test_citations.py` | **passed** |
| `test_pipeline.py` (fake embedder + fake LLM) | **passed** |
| `test_pdf_extraction.py` | **NOT RUN** (PyMuPDF missing) |
| `test_api.py` | **NOT RUN** (FastAPI/httpx missing) |

## Additional one-off checks that were run (scripts are not shipped)

- **Frontend compile check:** all 13 JSX/JS source files bundled with esbuild: all imports resolve, no syntax errors. (Vite itself was not run.)
- **Frontend render smoke test:** each page and the message/citation components were server-rendered with sample data (14 checks passed, incl. citation card with page, insufficient-evidence state, retrieval-only banner, empty states). Rendered with React 19; the project pins React 18.3.1. No browser interaction, styling or responsive layout was visually inspected.
- **`api.js` with a mocked `fetch`:** URLs, multipart upload (field `file`), JSON body field names and error-message handling: passed.
- **Contract consistency:** the five paths in `api.js` match the five backend routes exactly; request field names match `schemas.py`.
- **Sample PDF:** generated with reportlab; `pdftotext` confirmed 3 pages with the expected text per page. Its text was passed through the real cleaner/chunker: every chunk is verbatim text from its own page with exact offsets.

## NOT verified (please do this on a real machine)

1. `pip install -r requirements.txt` succeeds with the pinned versions (PyMuPDF and sentence-transformers pins in particular were not checked against the package index).
2. The FastAPI app starts with `uvicorn app.main:app`, and `test_api.py` passes.
3. Real PyMuPDF extraction (`test_pdf_extraction.py`).
4. The embedding model downloads and ChromaDB stores/queries correctly (the ChromaDB code path has never been executed).
5. A real Gemini call works with your key and the configured model name.
6. `npm install` and `npm run dev`/`npm run build` with the pinned Vite/React versions; the app in a real browser.
7. Retrieval quality and the `MIN_RELEVANCE_SCORE` threshold with the real embedding model.
8. The GitHub Actions workflow.

## Manual test checklist (about 10 minutes)

| # | Action | Expected |
|---|---|---|
| 1 | Start backend, open `/api/health` | `status: ok`; `llm_configured` matches your `.env` |
| 2 | Open the UI with the backend stopped | red "Backend not reachable" banner |
| 3 | Upload `notes.txt` renamed or a `.docx` | error "Only PDF files (.pdf) are supported." |
| 4 | Upload a text file renamed to `.pdf` | error "does not look like a valid PDF" |
| 5 | Upload the sample PDF | status Processed, 3 pages, several chunks |
| 6 | Upload a scanned/image-only PDF | status "No text found" + "OCR is not included" message |
| 7 | Ask *What are the limitations of the study?* | answer citing **page 3** |
| 8 | Ask *What was the total budget of the project?* | amber **Insufficient evidence** state, no citations |
| 9 | Remove the API key, restart, ask any question | "Retrieval-only mode" label, evidence shown, **no** AI answer |
| 10 | Open Evaluation | counts match what you asked; status "Usage counts only" |
| 11 | Restart the backend | documents still listed (ChromaDB + JSON persist on disk) |

## Tuning the relevance threshold (Member 4)

1. Upload your document, then ask 10 questions it *does* answer and 10 it does *not*.
2. Log or print `best_score` (see `RetrievalResult` in `retrieval/retriever.py`) for each.
3. Choose a `MIN_RELEVANCE_SCORE` that separates the two groups as well as possible, record the numbers you observed, and update `.env.example`.
