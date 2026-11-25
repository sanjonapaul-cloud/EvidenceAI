import CitationCard from "./CitationCard.jsx";
import TrustReport from "./TrustReport.jsx";

const STATUS_LABEL = {
  answered: { text: "Answer based on your documents", cls: "badge-green" },
  insufficient_evidence: { text: "Insufficient evidence", cls: "badge-amber" },
  retrieval_only: { text: "Retrieval-only mode (no AI answer)", cls: "badge-blue" },
  llm_error: { text: "AI service unavailable", cls: "badge-red" },
};

const CLAIM_STATUS = {
  supported: { text: "Supported", cls: "badge-green" },
  partially_supported: { text: "Partially supported", cls: "badge-amber" },
  contradicted: { text: "Contradicted", cls: "badge-red" },
  insufficient: { text: "Insufficient evidence", cls: "badge-blue" },
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
  const claims = message.claims || [];

  return (
    <div className="msg">
      <div className={`bubble ${insufficient ? "bubble-insufficient" : "bubble-assistant"}`}>
        {label && <span className={`badge ${label.cls}`}>{label.text}</span>}
        <p className="answer-text">{message.text}</p>
        {message.note && <p className="muted small">{message.note}</p>}

        <TrustReport report={message.trustReport} />

        {claims.length > 0 && (
          <div className="citations">
            <div className="citations-title">
              Claim-level verification ({claims.length})
            </div>

            {claims.map((claim, index) => {
              const claimStatus = CLAIM_STATUS[claim.status];

              return (
                <div className="citation" key={`${index}-${claim.claim}`}>
                  <div className="citation-head">
                    <strong>Claim {index + 1}</strong>
                    {claimStatus && (
                      <span className={`badge ${claimStatus.cls}`}>
                        {claimStatus.text}
                      </span>
                    )}
                  </div>

                  <p className="answer-text">{claim.claim}</p>

                  {claim.explanation && (
                    <p className="muted small">{claim.explanation}</p>
                  )}

                  {claim.sources?.length > 0 && (
                    <div className="citations">
                      <div className="citations-title">
                        Sources for this claim ({claim.sources.length})
                      </div>
                      {claim.sources.map((source) => (
                        <CitationCard
                          key={`${source.evidence_id}-${source.document_id}`}
                          citation={source}
                        />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

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
