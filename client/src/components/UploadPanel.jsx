import { useRef, useState } from "react";
import { uploadDocument } from "../services/api.js";
import Spinner from "./Spinner.jsx";

const MAX_MB = 20; // keep in sync with MAX_UPLOAD_MB on the server (the server is the real check)

export default function UploadPanel({ onUploaded }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null); // { kind: "success" | "warning" | "error", text }

  async function handleFile(file) {
    if (!file) return;
    setResult(null);

    // Quick checks in the browser for a faster error message.
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setResult({ kind: "error", text: "Only PDF files are supported." });
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setResult({ kind: "error", text: `File is too large. The maximum size is ${MAX_MB} MB.` });
      return;
    }

    setBusy(true);
    try {
      const data = await uploadDocument(file);
      if (data.status === "processed") {
        setResult({ kind: "success", text: `${data.filename}: ${data.message}` });
      } else if (data.status === "no_text") {
        setResult({ kind: "warning", text: `${data.filename}: ${data.message}` });
      } else {
        setResult({ kind: "error", text: `${data.filename}: ${data.message}` });
      }
      onUploaded();
    } catch (err) {
      setResult({ kind: "error", text: err.message });
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = ""; // allow re-selecting the same file
    }
  }

  function onDrop(event) {
    event.preventDefault();
    setDragging(false);
    handleFile(event.dataTransfer.files?.[0]);
  }

  return (
    <section className="card">
      <h2 className="card-title">Upload a PDF</h2>
      <div
        className={`dropzone ${dragging ? "dragging" : ""} ${busy ? "busy" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        {busy ? (
          <Spinner label="Reading and indexing your PDF… the first upload can take a minute while the model loads." />
        ) : (
          <>
            <div className="drop-icon" aria-hidden="true">⇪</div>
            <p className="drop-text">Drag and drop a PDF here, or</p>
            <button className="btn btn-primary" onClick={() => inputRef.current?.click()}>
              Choose a PDF file
            </button>
            <p className="muted small">PDF only · up to {MAX_MB} MB · text-based PDFs (no OCR yet)</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      {result && (
        <div className={`alert alert-${result.kind}`} role={result.kind === "error" ? "alert" : "status"}>
          {result.text}
        </div>
      )}
    </section>
  );
}
