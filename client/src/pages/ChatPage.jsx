import { useEffect, useRef, useState } from "react";
import { askQuestion } from "../services/api.js";
import ChatMessage from "../components/ChatMessage.jsx";
import Spinner from "../components/Spinner.jsx";

const EXAMPLE_QUESTIONS = [
  "What are the main findings?",
  "What are the limitations of this study?",
  "How was the study carried out?",
];

export default function ChatPage({
  documents,
  selectedIds,
  setSelectedIds,
  messages,
  setMessages,
  sessionId,
  onNavigate,
}) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef(null);
  const searchable = documents.filter((d) => d.status === "processed");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  function toggle(id) {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function send(text) {
    const trimmed = text.trim();
    if (trimmed.length < 3 || busy) return;
    setQuestion("");
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", text: trimmed }]);
    setBusy(true);
    try {
      const data = await askQuestion({
        question: trimmed,
        documentIds: selectedIds.filter((id) => searchable.some((d) => d.document_id === id)),
        sessionId,
      });
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: data.answer,
          status: data.status,
          citations: data.citations,
          note: data.note,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "error", text: err.message }]);
    } finally {
      setBusy(false);
    }
  }

  if (searchable.length === 0) {
    return (
      <div className="page">
        <header className="page-header"><h1>Ask Questions</h1></header>
        <section className="card empty">
          <div className="empty-icon" aria-hidden="true">💬</div>
          <p><strong>No searchable documents yet.</strong></p>
          <p className="muted">Upload a text-based PDF on the dashboard first.</p>
          <button className="btn btn-primary" onClick={() => onNavigate("dashboard")}>Go to dashboard</button>
        </section>
      </div>
    );
  }

  return (
    <div className="page chat-page">
      <header className="page-header">
        <h1>Ask Questions</h1>
        <p className="muted">
          {selectedIds.length === 0
            ? "No document selected: all processed documents will be searched."
            : `Searching ${selectedIds.length} selected document(s).`}
        </p>
      </header>

      <section className="card doc-picker" aria-label="Choose documents">
        {searchable.map((d) => (
          <label key={d.document_id} className={`chip ${selectedIds.includes(d.document_id) ? "chip-on" : ""}`}>
            <input
              type="checkbox"
              checked={selectedIds.includes(d.document_id)}
              onChange={() => toggle(d.document_id)}
            />
            {d.filename}
          </label>
        ))}
      </section>

      <section className="chat-window card" aria-live="polite">
        {messages.length === 0 && (
          <div className="empty">
            <div className="empty-icon" aria-hidden="true">🔎</div>
            <p><strong>Ask a question about your documents.</strong></p>
            <p className="muted">Answers always come with the page and passage that support them.</p>
            <div className="examples">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button key={q} className="btn btn-ghost" onClick={() => setQuestion(q)}>{q}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => <ChatMessage key={m.id} message={m} />)}
        {busy && (
          <div className="msg">
            <div className="bubble bubble-assistant"><Spinner label="Searching your documents…" /></div>
          </div>
        )}
        <div ref={bottomRef} />
      </section>

      <form className="composer" onSubmit={(e) => { e.preventDefault(); send(question); }}>
        <input
          className="input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about the selected documents…"
          maxLength={2000}
          aria-label="Your question"
        />
        <button className="btn btn-primary" type="submit" disabled={busy || question.trim().length < 3}>
          Ask
        </button>
      </form>
    </div>
  );
}
