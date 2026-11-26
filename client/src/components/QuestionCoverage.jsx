
const GAP_STATUS = {
  missing_information: {
    label: "Missing information",
    className: "badge-red",
  },
  incomplete_evidence: {
    label: "Incomplete evidence",
    className: "badge-amber",
  },
  conflicting_evidence: {
    label: "Conflicting evidence",
    className: "badge-red",
  },
};

export default function QuestionCoverage({ report }) {
  if (!report) return null;

  const total = report.total_parts ?? 0;
  const addressed = report.addressed_parts ?? 0;
  const unanswered = report.unanswered_parts ?? 0;
  const gaps = report.gaps ?? [];
  const warnings = report.warnings ?? [];

  const percentage =
    total > 0 ? Math.round((addressed / total) * 100) : null;

  return (
    <section
      className="trust-report"
      aria-label="Question coverage report"
    >
      <div className="trust-report-header">
        <h3>Question Coverage Report</h3>
        <span className="badge badge-blue">Question analysis</span>
      </div>

      <div className="trust-coverage">
        <div className="trust-coverage-score">
          {percentage !== null ? `${percentage}%` : "N/A"}
        </div>

        <div className="trust-coverage-description">
          <strong>Question coverage</strong>
          <p className="muted small">
            {percentage !== null
              ? "Proportion of question parts addressed by the retrieved evidence."
              : "Coverage cannot be calculated because the question has no assessed parts."}
          </p>
        </div>
      </div>

      {percentage !== null && (
        <div
          className="trust-progress-track"
          role="progressbar"
          aria-label="Question coverage"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="trust-progress-fill"
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}

      <div className="trust-stats">
        <div className="trust-stat">
          <strong>{total}</strong>
          <span>Question parts</span>
        </div>

        <div className="trust-stat trust-supported">
          <strong>{addressed}</strong>
          <span>Addressed</span>
        </div>

        <div className="trust-stat trust-insufficient">
          <strong>{unanswered}</strong>
          <span>Unanswered</span>
        </div>
      </div>

      {gaps.length > 0 && (
        <div className="trust-gaps">
          <h4>Question gaps requiring attention ({gaps.length})</h4>

          {gaps.map((gap, index) => {
            const status = GAP_STATUS[gap.status];

            return (
              <article
                className="trust-gap"
                key={`${index}-${gap.requested_part}`}
              >
                <div className="trust-gap-header">
                  <strong>Question part {index + 1}</strong>

                  {status && (
                    <span className={`badge ${status.className}`}>
                      {status.label}
                    </span>
                  )}
                </div>

                <p className="trust-gap-claim">{gap.requested_part}</p>

                {gap.explanation && (
                  <p className="trust-gap-explanation">
                    {gap.explanation}
                  </p>
                )}

                {gap.evidence_ids?.length > 0 && (
                  <p className="trust-gap-sources">
                    <strong>Related evidence:</strong>{" "}
                    {gap.evidence_ids.join(", ")}
                  </p>
                )}
              </article>
            );
          })}
        </div>
      )}

      {warnings.length > 0 && (
        <div className="trust-warnings" role="note">
          <h4>Warnings</h4>
          <ul>
            {warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="trust-report-disclaimer">
        Question coverage measures whether the retrieved evidence addresses
        each part of the question. It does not guarantee that the answer is
        correct or that all relevant information exists in the documents.
      </p>
    </section>
  );
}
