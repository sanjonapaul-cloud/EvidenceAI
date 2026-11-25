// One piece of supporting evidence. Everything shown here comes from the server's stored
// document chunks, never from text invented by the AI.
export default function CitationCard({ citation }) {
  return (
    <div className="citation">
      <div className="citation-head">
        <span className="evidence-id">{citation.evidence_id}</span>
        <span className="citation-file" title={citation.filename}>{citation.filename}</span>
        <span className="citation-page">Page {citation.page}</span>
      </div>

      <blockquote className="citation-excerpt">{citation.excerpt}</blockquote>

      <div className="muted tiny">Document ID: {citation.document_id}</div>

      {(citation.chunk_id || citation.chunk_index != null ||
        citation.char_start != null || citation.char_end != null) && (
        <div className="muted tiny">
          {citation.chunk_id && <div>Chunk ID: {citation.chunk_id}</div>}
          {citation.chunk_index != null && <div>Chunk index: {citation.chunk_index}</div>}
          {citation.char_start != null && citation.char_end != null && (
            <div>
              Character range: {citation.char_start} - {citation.char_end}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
