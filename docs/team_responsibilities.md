# Team Responsibilities

Each member **owns** a set of files. Owners write and review changes in them; anyone can suggest changes by opening a pull request. Files are split so that, in normal work, two members rarely edit the same file.

## Member 1 — Frontend
**Owns:** `client/` (everything), especially `src/pages/`, `src/components/`, `src/services/api.js`, `src/index.css`.
**First tasks:** run the UI against the backend; improve empty/error states; add keyboard accessibility checks; add Vitest tests.
**Depends on:** `docs/api_contracts.md` (Member 2). If you need a new field, ask Member 2 rather than guessing.
**Try it:** upload the sample PDF; follow how `ChatMessage.jsx` renders each `status`.

## Member 2 — Backend
**Owns:** `server/app/main.py`, `server/app/routes/*`, `server/app/schemas.py`, `server/app/core/errors.py`.
**First tasks:** read `schemas.py`; open `http://localhost:8000/docs`; add a `DELETE /api/documents/{id}` endpoint (must also call `store.delete_document`); keep `docs/api_contracts.md` in sync.
**Shared:** `document_processing/upload_service.py` with Member 3. Rule: Member 2 owns validation + HTTP mapping, Member 3 owns processing.

## Member 3 — PDF Processing
**Owns:** `server/app/document_processing/` (`extractor.py`, `cleaner.py`, `chunker.py`, `validation.py`, `processing.py`, `models.py`) and `tests/test_chunking.py`, `tests/test_pdf_extraction.py`.
**First tasks:** run `pytest tests/test_pdf_extraction.py` (needs PyMuPDF); try odd PDFs (two columns, tables); improve `clean_text` for headers/footers; tune `CHUNK_SIZE`/`CHUNK_OVERLAP`.
**Golden rule:** never let a chunk lose or change its page number.

## Member 4 — RAG Engine
**Owns:** `server/app/embeddings/`, `server/app/retrieval/`, `server/app/rag/` (`prompt.py`, `gemini_client.py`, `pipeline.py`, `chat_service.py`) and `tests/test_retrieval.py`.
**First tasks:** try retrieval with the real model on the sample PDF; **tune `MIN_RELEVANCE_SCORE`**; verify the Gemini model name in `.env`; experiment with `TOP_K` and the prompt.
**Golden rule:** the prompt may only contain retrieved evidence.

## Member 5 — Citations and Evaluation
**Owns:** `server/app/citations/`, `server/app/evaluation/`, `server/app/routes/evaluation.py` and `tests/test_citations.py`, `tests/test_pipeline.py` (insufficient-evidence cases).
**First tasks:** read `citations/evidence.py`; add a semantic support check (future work); build a small labelled question set (question → expected page) and report recall — **real measurements only, never invented scores**.
**Golden rule:** a citation's filename, page and excerpt must come from stored chunks only.

## Member 6 — Integration
**Owns:** `README.md`, `docs/`, `.github/`, `.gitignore`, `server/requirements*.txt`, `server/.env.example`, `server/app/core/config.py`, `server/app/core/dependencies.py`, `server/app/core/registry.py`, `server/tests/conftest.py`, `server/tests/helpers.py`, `tests/test_api.py`.
**First tasks:** run the full setup on a clean Windows machine and fix the guide; generate and commit `client/package-lock.json`; confirm the pinned versions install; run the whole test suite and update `docs/testing_guide.md` with real results; protect `main` on GitHub.
**Also:** reviews integration PRs and keeps the demo working at all times.

## Where members must coordinate

| Change | Tell |
|---|---|
| API field added/renamed | Members 1, 2, 6 (update `schemas.py`, `api.js`, `api_contracts.md` in one PR) |
| Chunk metadata changed | Members 3, 4, 5 |
| Evidence/citation format changed | Members 1, 2, 4, 5 |
| New dependency | Member 6 (`requirements.txt` / `package.json`) |
