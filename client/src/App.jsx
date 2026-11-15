import { useCallback, useEffect, useState } from "react";
import { getHealth, listDocuments } from "./services/api.js";
import Sidebar from "./components/Sidebar.jsx";
import StatusBanner from "./components/StatusBanner.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";
import EvaluationPage from "./pages/EvaluationPage.jsx";

export default function App() {
  const [page, setPage] = useState("dashboard"); // simple navigation: no router library needed
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState("");

  // Chat state lives here so it is not lost when you switch pages.
  const [messages, setMessages] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [sessionId] = useState(() => `session_${crypto.randomUUID()}`);

  const refreshDocuments = useCallback(async () => {
    try {
      const data = await listDocuments();
      setDocuments(data.documents);
    } catch (err) {
      setHealthError(err.message);
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    getHealth()
      .then((h) => { setHealth(h); setHealthError(""); })
      .catch((err) => setHealthError(err.message));
    refreshDocuments();
  }, [refreshDocuments]);

  function askAbout(documentId) {
    setSelectedIds([documentId]);
    setPage("chat");
  }

  return (
    <div className="app-shell">
      <Sidebar page={page} onNavigate={setPage} health={health} healthError={healthError} />
      <main className="main">
        <StatusBanner health={health} healthError={healthError} />
        {page === "dashboard" && (
          <DashboardPage
            documents={documents}
            loading={loadingDocs}
            onUploaded={refreshDocuments}
            onAskAbout={askAbout}
            onNavigate={setPage}
          />
        )}
        {page === "chat" && (
          <ChatPage
            documents={documents}
            selectedIds={selectedIds}
            setSelectedIds={setSelectedIds}
            messages={messages}
            setMessages={setMessages}
            sessionId={sessionId}
            onNavigate={setPage}
          />
        )}
        {page === "evaluation" && <EvaluationPage />}
      </main>
    </div>
  );
}
