// All calls to the FastAPI backend live here (Member 1 owns this file; keep it in sync with
// docs/api_contracts.md and server/app/schemas.py).

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api").replace(/\/$/, "");

// Turn whatever the server returned into a short, friendly message. Never shows raw errors.
function messageFromError(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (status === 422) return "The request was not valid. Please check your input.";
  return `Something went wrong (error ${status}).`;
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch {
    throw new Error("Cannot reach the EvidenceAI server. Is the backend running on port 8000?");
  }
  let data = null;
  try {
    data = await response.json();
  } catch {
    // response had no JSON body
  }
  if (!response.ok) throw new Error(messageFromError(data, response.status));
  return data;
}

// GET /api/health
export const getHealth = () => request("/health");

// GET /api/documents  ->  { documents: [...] }
export const listDocuments = () => request("/documents");

// POST /api/documents/upload  (multipart/form-data, field name "file")
export function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file); // do NOT set Content-Type yourself: the browser adds the boundary
  return request("/documents/upload", { method: "POST", body: form });
}

// POST /api/chat/ask  ->  { answer, status, citations, note }
export const askQuestion = ({ question, documentIds, sessionId }) =>
  request("/chat/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_ids: documentIds, session_id: sessionId }),
  });

// GET /api/evaluation/summary
export const getEvaluationSummary = () => request("/evaluation/summary");
// GET /api/audit/events -> paginated audit events
export const listAuditEvents = ({
  limit = 20,
  offset = 0,
  eventType = "",
  apiKey,
} = {}) => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  if (eventType) {
    params.set("event_type", eventType);
  }

  return request(`/audit/events?${params.toString()}`, {
    headers: {
      "X-Audit-API-Key": apiKey,
    },
  });
};
