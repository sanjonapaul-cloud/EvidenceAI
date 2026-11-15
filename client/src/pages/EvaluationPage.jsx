import { useEffect, useState } from "react";
import { getEvaluationSummary } from "../services/api.js";
import Spinner from "../components/Spinner.jsx";

const STATS = [
  ["documents_uploaded", "Documents uploaded"],
  ["documents_processed", "Documents processed"],
  ["chunks_processed", "Chunks processed"],
  ["questions_asked", "Questions asked"],
  ["answers_returned", "Answers returned"],
  ["insufficient_evidence_responses", "Insufficient-evidence responses"],
  ["retrieval_only_responses", "Retrieval-only responses (no API key)"],
  ["llm_error_responses", "AI service errors"],
];

export default function EvaluationPage() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getEvaluationSummary().then(setSummary).catch((err) => setError(err.message));
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <h1>Evaluation</h1>
        <p className="muted">Basic usage counts for this demo. These are not accuracy scores.</p>
      </header>

      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {!summary && !error && <Spinner label="Loading summary…" />}

      {summary && (
        <>
          <div className="stat-grid">
            {STATS.map(([key, label]) => (
              <div className="stat" key={key}>
                <div className="stat-value">{summary[key]}</div>
                <div className="stat-label">{label}</div>
              </div>
            ))}
          </div>
          <section className="card">
            <h2 className="card-title">Evaluation status</h2>
            <p><strong>{summary.evaluation_status}</strong></p>
            <p className="muted small">{summary.note}</p>
          </section>
        </>
      )}
    </div>
  );
}
