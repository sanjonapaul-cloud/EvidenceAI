import UploadPanel from "../components/UploadPanel.jsx";
import DocumentCard from "../components/DocumentCard.jsx";

export default function DashboardPage({ documents, loading, onUploaded, onAskAbout, onNavigate }) {
  const processed = documents.filter((d) => d.status === "processed").length;

  return (
    <div className="page">
      <header className="page-header">
        <h1>EvidenceAI</h1>
        <p className="lead">
          Upload research papers or reports, ask questions, and get answers that point to the exact
          page and passage they came from. If your documents do not contain the answer, EvidenceAI
          says so instead of guessing.
        </p>
        <p className="muted small">
          Student prototype for educational demonstration. Not a production research tool and not for
          medical or other high-stakes decisions.
        </p>
      </header>

      <UploadPanel onUploaded={onUploaded} />

      <section className="card">
        <div className="card-head">
          <h2 className="card-title">Your documents</h2>
          <button
            className="btn btn-primary"
            disabled={processed === 0}
            onClick={() => onNavigate("chat")}
          >
            Go to chat →
          </button>
        </div>

        {loading && documents.length === 0 ? (
          <p className="muted">Loading documents…</p>
        ) : documents.length === 0 ? (
          <div className="empty">
            <div className="empty-icon" aria-hidden="true">📄</div>
            <p><strong>No documents yet.</strong></p>
            <p className="muted">Upload a PDF above to get started. A sample is included in the <code>sample_data</code> folder.</p>
          </div>
        ) : (
          <div className="doc-grid">
            {documents.map((doc) => (
              <DocumentCard key={doc.document_id} doc={doc} onAsk={onAskAbout} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
