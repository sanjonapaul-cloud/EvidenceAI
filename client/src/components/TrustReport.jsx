const STATUS = {
  supported: { label: "Supported", className: "badge-green" },
  partially_supported: { label: "Partial", className: "badge-amber" },
  contradicted: { label: "Contradicted", className: "badge-red" },
  insufficient: { label: "Insufficient", className: "badge-blue" },
};

export default function TrustReport({ report }) {
  if (!report) return null;

  const coverage = report.coverage_percent;
  const hasCoverage = coverage !== null && coverage !== undefined;
  const gaps = report.gaps ?? [];
  const warnings = report.warnings ?? [];

  return (
    <section className="trust-report" aria-label="Evidence trust report">
      <div className="trust-report-header">
        <h3>Evidence Coverage Report</h3>
        <span className="badge badge-blue">Evidence analysis</span>
      </div>

      <div className="trust-coverage">
        <div className="trust-coverage-score">
          {hasCoverage ? `${coverage.toFixed(2)}%` : "N/A"}
        </div>
        <div className="trust-coverage-description">
          <strong>Evidence coverage</strong>
          <p className="muted small">
            {hasCoverage
              ? "Weighted proportion of claims supported by evidence."
              : "Coverage cannot be calculated because no claims were assessed."}
          </p>
        </div>
      </div>

      {hasCoverage && (
        <div
          className="trust-progress-track"
          role="progressbar"
          aria-label="Evidence coverage"
          aria-valuenow={coverage}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="trust-progress-fill"
            style={{ width: `${Math.max(0, Math.min(100, coverage))}%` }}
          />
        </div>
      )}

      <div className="trust-stats">
        <div className="trust-stat">
          <strong>{report.total_claims}</strong>
          <span>Total claims</span>
        </div>
        <div className="trust-stat trust-supported">
          <strong>{report.supported}</strong>
          <span>Supported</span>
        </div>
        <div className="trust-stat trust-partial">
          <strong>{report.partially_supported}</strong>
          <span>Partial</span>
        </div>
        <div className="trust-stat trust-contradicted">
          <strong>{report.contradicted}</strong>
          <span>Contradicted</span>
        </div>
        <div className="trust-stat trust-insufficient">
          <strong>{report.insufficient}</strong>
          <span>Insufficient</span>
        </div>
        <div className="trust-stat trust-unsupported">
          <strong>{report.unsupported}</strong>
          <span>Unsupported</span>
        </div>
      </div>

      {gaps.length > 0 && (
        <div className="trust-gaps">
          <h4>Evidence gaps requiring attention ({gaps.length})</h4>

          {gaps.map((gap, index) => {
            const status = STATUS[gap.status];

            return (
              <article className="trust-gap" key={`${index}-${gap.claim}`}>
                <div className="trust-gap-header">
                  <strong>Claim {index + 1}</strong>
                  {status && (
                    <span className={`badge ${status.className}`}>
                      {status.label}
                    </span>
                  )}
                </div>

                <p className="trust-gap-claim">{gap.claim}</p>

                {gap.explanation && (
                  <p className="trust-gap-explanation">{gap.explanation}</p>
                )}

                {gap.sources?.length > 0 && (
                  <div className="trust-gap-sources">
                    <strong>Related sources:</strong>
                    {gap.sources.map((source, sourceIndex) => (
                      <span key={`${source.evidence_id}-${sourceIndex}`}>
                        {source.filename}, page {source.page}
                        {sourceIndex < gap.sources.length - 1 ? "; " : ""}
                      </span>
                    ))}
                  </div>
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
        Evidence coverage is a measure of evidence support, not a probability
        that the answer is correct. Contradictions and missing evidence require
        human review.
      </p>
    </section>
  );
}
