# Architecture

Owner: Member 6 (with input from every module owner).

## Overview

```
┌──────────────────────┐   HTTP/JSON    ┌──────────────────────────────────────────────┐
│ React + Vite (client)│ ─────────────► │ FastAPI (server/app)                         │
│ Dashboard · Chat ·   │ ◄───────────── │  routes/  → thin wrappers, validation        │
│ Evaluation           │                │  schemas.py → API contract (Pydantic)        │
└──────────────────────┘                └───────┬───────────────┬──────────────────────┘
                                                │               │
                     upload                     │               │  question
                       ▼                        │               ▼
        document_processing/                    │        rag/chat_service → rag/pipeline
        extract → clean → chunk                 │          1 retrieval/retriever  ──► ChromaDB
                       │                        │          2 threshold → insufficient?
                       ▼                        │          3 rag/prompt + gemini_client ──► Gemini API
        embeddings/ (Sentence Transformers)     │          4 citations/ verify [E#] markers
                       │                        │
                       ▼                        │   core/registry.py  documents.json (document info)
                 ChromaDB (disk) ◄──────────────┘   evaluation/metrics.py  metrics.json (counters)
```

## Module map

| Package | Responsibility | Owner |
|---|---|---|
| `client/` | UI, API client (`services/api.js`) | Member 1 |
| `app/main.py`, `routes/`, `schemas.py` | App setup, CORS, error handlers, HTTP layer, contract | Member 2 |
| `document_processing/` | `extractor` (PyMuPDF), `cleaner`, `chunker`, `validation`, `processing`, `upload_service` | Member 3 |
| `embeddings/`, `retrieval/`, `rag/` | Embedding model, ChromaDB, retrieval + threshold, prompt, Gemini, pipeline | Member 4 |
| `citations/`, `evaluation/` | Evidence IDs, citation verification, insufficient-evidence rules, counters | Member 5 |
| `core/`, `tests/`, `docs/`, `.github/` | Config, errors, registry, dependency wiring, tests, docs, CI | Member 6 |

## Data flow: upload

1. `routes/documents.py` receives the multipart file and calls `upload_service.handle_upload`.
2. Validation: `.pdf` name, `%PDF-` header, size limit (streamed, so huge files are stopped early).
3. A record is created in the registry (`doc_001`, `doc_002`, …); the file is saved as `server/data/uploads/<doc_id>.pdf` (our own name, so user-supplied names cannot cause path tricks).
4. `extractor.extract_pdf` reads **one page at a time** (1-based page numbers).
5. `cleaner.clean_text` normalises each page. `chunker.chunk_pages` splits **each page separately** (default 800 chars, 150 overlap), so a chunk can never mix pages. Each chunk keeps `document_id`, `filename`, `page`, `chunk_index`, offsets.
6. `embedder.embed_documents` creates vectors; `ChromaVectorStore.add_chunks` stores text + vector + metadata.
7. The registry record is updated with status, page info and chunk count. Scanned PDFs end as `no_text` with an explicit "OCR is not included" message.

## Data flow: question

1. `chat_service.ask_question` checks the selected documents exist and are `processed`.
2. `Retriever` embeds the question, queries ChromaDB (filtered by document IDs), sorts by cosine similarity and **drops chunks below `MIN_RELEVANCE_SCORE`**.
3. No chunks left → `insufficient_evidence`, **Gemini is not called**.
4. No API key → `retrieval_only` (evidence only, clearly labelled). Gemini error → `llm_error`.
5. Otherwise the prompt contains only the retrieved passages, numbered `[E1]…`, with strict rules (use only the evidence, cite IDs, reply `INSUFFICIENT_EVIDENCE` if unsure, treat passage text as data not instructions).
6. The reply is verified: `[E#]` markers that were not provided are stripped; if no valid marker remains the answer is withheld as `insufficient_evidence`. Citation cards are built from the **stored chunks** that were validly cited.

## Why citations can't be fabricated (and what that does not guarantee)

- Filename, page, document ID and excerpt come from ChromaDB metadata/text, never from model output.
- Invented evidence IDs are removed.
- **Not guaranteed:** that a cited passage truly supports the sentence next to it. The check is structural (the ID exists), not semantic. Users must still read the cited excerpt. Semantic verification (e.g. an entailment check) is listed as future work.

## Key design decisions

- **Dependency injection** (`core/dependencies.py`): routes receive the embedder, vector store, LLM and registry through FastAPI `Depends`, so tests substitute fakes and heavy packages load lazily; the server starts even if a package is missing and reports a clear error on first use.
- **Thin routes, logic in services** (`upload_service`, `chat_service`, `pipeline`): testable without a web server.
- **Page-level chunking** trades slightly worse context across page breaks for guaranteed page numbers.
- **JSON files for the registry and counters**: simple to inspect for a demo; not safe for multi-process deployment (see limitations).
- **Synchronous processing** on upload: simplest to understand; large PDFs block that request (the route runs in a worker thread, so other requests continue).

## Security notes (what was done, not guaranteed)

Secrets only via environment variables; `.env` git-ignored; generic error messages; filename sanitisation; size and content-type checks; CORS limited to configured origins; Gemini key never returned or logged. No authentication, rate limiting or malware scanning exists. Do not expose this prototype to the public internet.
