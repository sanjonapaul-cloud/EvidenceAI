import { useCallback, useEffect, useState } from "react";
import { listAuditEvents } from "../services/api.js";
import Spinner from "../components/Spinner.jsx";

const PAGE_SIZE = 20;

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

function ClaimCounts({ counts = {} }) {
  const entries = [
    ["supported", "Supported", "badge-green"],
    ["partially_supported", "Partially supported", "badge-amber"],
    ["contradicted", "Contradicted", "badge-red"],
    ["insufficient", "Insufficient", "badge-red"],
  ];

  return (
    <div className="audit-counts">
      {entries.map(([key, label, className]) => (
        <span className={`badge ${className}`} key={key}>
          {label}: {counts[key] ?? 0}
        </span>
      ))}
    </div>
  );
}

export default function AuditPage() {
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [eventType, setEventType] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [activeApiKey, setActiveApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadEvents = useCallback(async () => {
    if (!activeApiKey) return;

    setLoading(true);
    setError("");

    try {
      const data = await listAuditEvents({
        limit: PAGE_SIZE,
        offset,
        eventType,
        apiKey: activeApiKey,
      });

      setEvents(data.events ?? []);
      setTotal(data.total ?? 0);
    } catch (err) {
      setError(err.message);
      setEvents([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [offset, eventType, activeApiKey]);

  useEffect(() => {
    if (activeApiKey) {
      loadEvents();
    }
  }, [activeApiKey, loadEvents]);

  function unlockAudit(event) {
    event.preventDefault();
    const submittedKey = apiKey.trim();

    if (!submittedKey) {
      setError("Enter the audit API key to continue.");
      return;
    }

    setOffset(0);
    setError("");
    setActiveApiKey(submittedKey);
  }

  function changeFilter(value) {
    setEventType(value);
    setOffset(0);
  }

  const pageNumber = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="page">
      <header className="page-header">
        <h1>Audit Trail</h1>
        <p className="lead">
          Review recorded system activity, document references, and
          claim-verification outcomes.
        </p>
        <p className="muted small">
          This audit view contains metadata only. It does not expose raw
          questions, answers, or evidence excerpts.
        </p>
      </header>

      <form className="card audit-auth-form" onSubmit={unlockAudit}>
        <h2 className="card-title">Administrator access</h2>
        <p className="muted small">
          Enter the audit API key provided by your server administrator.
        </p>
        <label htmlFor="audit-api-key">Audit API key</label>
        <input
          id="audit-api-key"
          className="input"
          type="password"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          autoComplete="off"
          placeholder="Enter audit API key"
        />
        <button className="btn btn-primary" type="submit" disabled={!apiKey.trim()}>
          Unlock audit trail
        </button>
      </form>

      <div className="stat-grid" hidden={!activeApiKey}>
        <div className="stat">
          <div className="stat-value">{total}</div>
          <div className="stat-label">Total matching events</div>
        </div>
        <div className="stat">
          <div className="stat-value">{events.length}</div>
          <div className="stat-label">Events on this page</div>
        </div>
      </div>

      <section className="card" hidden={!activeApiKey}>
        <div className="card-head">
          <h2 className="card-title">Event history</h2>

          <div className="audit-filters">
            <label htmlFor="audit-event-type">Event type</label>
            <select
              id="audit-event-type"
              value={eventType}
              onChange={(event) => changeFilter(event.target.value)}
            >
              <option value="">All events</option>
              <option value="chat_response_answered">Successful responses</option>
              <option value="chat_response_insufficient_evidence">
                Insufficient-evidence responses
              </option>
              <option value="chat_response_llm_error">AI service errors</option>
              <option value="chat_response_retrieval_only">
                Retrieval-only responses
              </option>
            </select>

            <button
              className="btn btn-secondary"
              onClick={() => {
                if (offset === 0) loadEvents();
                else setOffset(0);
              }}
              disabled={loading}
            >
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="alert alert-error" role="alert">
            {error}
          </div>
        )}

        {loading ? (
          <Spinner label="Loading audit events..." />
        ) : error ? (
          <div className="empty">
            <p>Could not load audit events.</p>
            <button className="btn btn-primary" onClick={loadEvents}>
              Try again
            </button>
          </div>
        ) : events.length === 0 ? (
          <div className="empty">
            <div className="empty-icon" aria-hidden="true">◷</div>
            <p><strong>No audit events found.</strong></p>
            <p className="muted">
              Events will appear here after the system records activity.
            </p>
          </div>
        ) : (
          <>
            <div className="audit-event-list">
              {events.map((item) => (
                <article className="audit-event" key={item.event_id}>
                  <div className="audit-event-header">
                    <div>
                      <strong>{item.event_type}</strong>
                      <p className="muted small">
                        {formatDate(item.created_at)}
                      </p>
                    </div>
                    <span className="badge badge-blue">
                      {item.event_id.slice(0, 8)}
                    </span>
                  </div>

                  <ClaimCounts counts={item.claim_status_counts} />

                  <div className="audit-metadata">
                    <div>
                      <strong>Request ID</strong>
                      <code>{item.request_id || "—"}</code>
                    </div>
                    <div>
                      <strong>Documents</strong>
                      <span>{item.document_ids?.length ?? 0}</span>
                    </div>
                    <div>
                      <strong>Evidence references</strong>
                      <span>{item.evidence_ids?.length ?? 0}</span>
                    </div>
                  </div>

                  <details className="audit-details">
                    <summary>View recorded identifiers</summary>

                    <p><strong>Event ID:</strong></p>
                    <code>{item.event_id}</code>

                    <p><strong>Document IDs:</strong></p>
                    {item.document_ids?.length ? (
                      <ul>
                        {item.document_ids.map((id) => (
                          <li key={id}><code>{id}</code></li>
                        ))}
                      </ul>
                    ) : (
                      <p className="muted">No document IDs recorded.</p>
                    )}

                    <p><strong>Evidence IDs:</strong></p>
                    {item.evidence_ids?.length ? (
                      <ul>
                        {item.evidence_ids.map((id) => (
                          <li key={id}><code>{id}</code></li>
                        ))}
                      </ul>
                    ) : (
                      <p className="muted">No evidence IDs recorded.</p>
                    )}
                  </details>
                </article>
              ))}
            </div>

            <div className="audit-pagination">
              <span className="muted small">
                Page {pageNumber} of {totalPages} · {total} events
              </span>

              <div>
                <button
                  className="btn btn-ghost"
                  disabled={offset === 0 || loading}
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                >
                  Previous
                </button>
                <button
                  className="btn btn-primary"
                  disabled={offset + PAGE_SIZE >= total || loading}
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
