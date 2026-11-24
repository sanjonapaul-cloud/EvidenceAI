const ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "▦" },
  { id: "chat", label: "Ask Questions", icon: "✎" },
  { id: "evaluation", label: "Evaluation", icon: "◔" },
  { id: "audit", label: "Audit Trail", icon: "◷" },
];

export default function Sidebar({ page, onNavigate, health, healthError }) {
  let statusClass = "dot dot-grey";
  let statusText = "Checking server…";
  if (healthError) {
    statusClass = "dot dot-red";
    statusText = "Server offline";
  } else if (health) {
    statusClass = health.llm_configured ? "dot dot-green" : "dot dot-amber";
    statusText = health.llm_configured ? "Gemini connected" : "Retrieval-only mode";
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">E</span>
        <div>
          <div className="brand-name">EvidenceAI</div>
          <div className="brand-sub">Verifiable answers</div>
        </div>
      </div>

      <nav className="nav" aria-label="Main">
        {ITEMS.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${page === item.id ? "active" : ""}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="nav-icon" aria-hidden="true">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-status">
        <span className={statusClass} />
        {statusText}
      </div>
    </aside>
  );
}
