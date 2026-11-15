const STATUS = {
  processed: { label: "Processed", cls: "badge-green" },
  processing: { label: "Processing", cls: "badge-blue" },
  no_text: { label: "No text found", cls: "badge-amber" },
  failed: { label: "Failed", cls: "badge-red" },
};

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentCard({ doc, onAsk }) {
  const status = STATUS[doc.status] || { label: doc.status, cls: "badge-grey" };
  return (
    <article className="doc-card">
      <div className="doc-top">
        <div className="doc-icon" aria-hidden="true">PDF</div>
        <div className="doc-main">
          <h3 className="doc-name" title={doc.filename}>{doc.filename}</h3>
          <div className="muted small">
            {doc.document_id} · {formatSize(doc.size_bytes)} · {doc.page_count} page(s) ·{" "}
            {doc.chunk_count} chunk(s)
          </div>
        </div>
        <span className={`badge ${status.cls}`}>{status.label}</span>
      </div>
      <p className="doc-message small">{doc.message}</p>
      {doc.status === "processed" && (
        <button className="btn btn-secondary" onClick={() => onAsk(doc.document_id)}>
          Ask questions about this document
        </button>
      )}
    </article>
  );
}
