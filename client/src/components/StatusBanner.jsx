// Shows the most important system problem, if any, at the top of every page.
export default function StatusBanner({ health, healthError }) {
  if (healthError) {
    return (
      <div className="banner banner-error" role="alert">
        <strong>Backend not reachable.</strong> {healthError} Start it with{" "}
        <code>uvicorn app.main:app --reload --port 8000</code> in the <code>server</code> folder.
      </div>
    );
  }
  if (health && !health.llm_configured) {
    return (
      <div className="banner banner-warn" role="status">
        <strong>Gemini API key not configured.</strong> The app is in <em>retrieval-only mode</em>: it
        can find and show evidence from your documents, but it will not write AI answers. Set{" "}
        <code>GEMINI_API_KEY</code> in <code>server/.env</code> and restart the backend.
      </div>
    );
  }
  return null;
}
