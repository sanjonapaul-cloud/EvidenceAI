import CitationCard from "./CitationCard.jsx";

const STATUS_LABEL = {
  answered: { text: "Answer based on your documents", cls: "badge-green" },
  insufficient_evidence: { text: "Insufficient evidence", cls: "badge-amber" },
  retrieval_only: { text: "Retrieval-only mode (no AI answer)", cls: "badge-blue" },
  llm_error: { text: "AI service unavailable", cls: "badge-red" },
};

export default function ChatMessage({ message }) {
  if (message.role === "user") {
    return (
      <div className="msg msg-user">
        <div className="bubble bubble-user">{message.text}</div>
      </div>
    );
  }

  if (message.role === "error") {
    return (
      <div className="msg">
        <div className="bubble bubble-error" role="alert">{message.text}</div>
      </div>
    );
  }

  const label = STATUS_LABEL[message.status];
  const insufficient = message.status === "insufficient_evidence";
  const citations = message.citations || [];

  return (
    <div className="msg">
      <div className={`bubble ${insufficient ? "bubble-insufficient" : "bubble-assistant"}`}>
        {label && <span className={`badge ${label.cls}`}>{label.text}</span>}
        <p className="answer-text">{message.text}</p>
        {message.note && <p className="muted small">{message.note}</p>}

        {citations.length > 0 && (
          <div className="citations">
            <div className="citations-title">
              {message.status === "answered" ? "Supporting evidence" : "Retrieved evidence"} ({citations.length})
            </div>
            {citations.map((c) => (
              <CitationCard key={`${c.evidence_id}-${c.document_id}-${c.page}`} citation={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
