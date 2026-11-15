# API Contracts

Base URL (development): `http://localhost:8000/api`. All bodies are JSON except the upload (multipart).
The source of truth in code is `server/app/schemas.py`; the frontend client is `client/src/services/api.js`.
Interactive docs generated from the code: <http://localhost:8000/docs>.

**Error format.** Every error is `{"detail": "<safe, human-readable message>"}`. Stack traces and secrets are never returned (details go to the server log only). Request-validation errors (HTTP 422) may use FastAPI's standard list format; the frontend shows a generic message for those.

---

## GET /api/health

Response `200`:
```json
{
  "status": "ok",
  "app": "EvidenceAI",
  "llm_configured": false,
  "gemini_model": "gemini-2.5-flash",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```
`llm_configured` is `true` only if a non-placeholder `GEMINI_API_KEY` is set. The key itself is never returned.

---

## POST /api/documents/upload

Request: `multipart/form-data` with one file field named **`file`**.

Response `200` (the file was accepted; check `status` for the processing outcome):
```json
{
  "document_id": "doc_001",
  "filename": "research_paper.pdf",
  "status": "processed",
  "message": "Processed 3 page(s) into 9 searchable chunk(s).",
  "processing_summary": { "page_count": 3, "pages_with_text": 3, "chunk_count": 9, "size_bytes": 4803 }
}
```

`status` values:

| status | meaning |
|---|---|
| `processed` | text extracted, chunked, embedded and stored |
| `no_text` | no extractable text (scanned/image-only PDF). **OCR is not included in this version.** No chunks stored. |
| `failed` | accepted, but processing failed (corrupt or password-protected PDF, embedding/database problem). `message` explains. |
| `processing` | transient; uploads are processed synchronously so clients normally never see it |

Errors (file rejected, nothing stored):

| HTTP | when |
|---|---|
| 400 | not a `.pdf` name, content does not start like a PDF (`%PDF-`), or the file is empty |
| 413 | larger than `MAX_UPLOAD_MB` (default 20) |
| 422 | the `file` field is missing |

---

## GET /api/documents

Response `200`:
```json
{
  "documents": [
    {
      "document_id": "doc_001",
      "filename": "research_paper.pdf",
      "status": "processed",
      "message": "Processed 3 page(s) into 9 searchable chunk(s).",
      "size_bytes": 4803,
      "page_count": 3,
      "pages_with_text": 3,
      "chunk_count": 9,
      "uploaded_at": "2026-11-15T08:00:00+00:00",
      "pages": [ { "page": 1, "char_count": 912 }, { "page": 2, "char_count": 880 }, { "page": 3, "char_count": 1010 } ]
    }
  ]
}
```

---

## POST /api/chat/ask

Request:
```json
{
  "question": "What are the limitations of this model?",
  "document_ids": ["doc_001"],
  "session_id": "session_001"
}
```
- `question`: 3–2000 characters (trimmed).
- `document_ids`: optional. Empty or omitted = search **all processed** documents. Only documents with status `processed` are searchable.
- `session_id`: optional; accepted and stored by the client, **not used** for conversation memory in this version (each question is answered independently).

Response `200`:
```json
{
  "answer": "The study covered a single city and one summer [E1].",
  "status": "answered",
  "citations": [
    {
      "document_id": "doc_001",
      "filename": "research_paper.pdf",
      "page": 3,
      "evidence_id": "E1",
      "excerpt": "Limitations: The study covered a single city and only one summer..."
    }
  ],
  "note": null
}
```

`status` values:

| status | meaning | `citations` |
|---|---|---|
| `answered` | Gemini answered and at least one valid `[E#]` evidence marker was verified | only the evidence the answer actually cited |
| `insufficient_evidence` | nothing relevant was retrieved, the model said the evidence is not enough, or its reply cited no valid evidence | `[]` |
| `retrieval_only` | no Gemini key configured; **no AI answer was generated** | the retrieved evidence |
| `llm_error` | the Gemini request failed; **no AI answer was generated** | the retrieved evidence |

For `insufficient_evidence` the `answer` is exactly:
`"Insufficient evidence in the uploaded documents to answer this question reliably."` and `note` explains what to try.

Citation rules: `excerpt` is always the beginning (up to 300 characters) of a chunk stored in ChromaDB; `filename`, `page` and `document_id` come from the stored chunk metadata, never from the AI's text. `page` is the 1-based PDF page index.

Errors:

| HTTP | when |
|---|---|
| 400 | no processed documents exist, or none of the selected documents has searchable text |
| 404 | a `document_ids` entry does not exist |
| 422 | invalid request body (missing/too short/too long question) |
| 503 | the embedding model or vector database is unavailable |

---

## GET /api/evaluation/summary

Response `200`:
```json
{
  "documents_uploaded": 1,
  "documents_processed": 1,
  "chunks_processed": 9,
  "questions_asked": 4,
  "answers_returned": 2,
  "insufficient_evidence_responses": 1,
  "retrieval_only_responses": 1,
  "llm_error_responses": 0,
  "evaluation_status": "Usage counts only",
  "note": "These are usage counts only. No accuracy, faithfulness or relevance scores have been computed in this initial version."
}
```
`evaluation_status` is `"Not yet evaluated"` while `questions_asked` is 0. Only questions that completed (any of the four statuses above) are counted; requests rejected with an HTTP error are not.
