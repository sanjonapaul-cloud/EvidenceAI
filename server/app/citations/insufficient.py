"""Insufficient-evidence handling (Member 5)."""
from __future__ import annotations

# Exact text required by the API contract.
INSUFFICIENT_ANSWER = (
    "Insufficient evidence in the uploaded documents to answer this question reliably."
)

# The word the LLM is told to reply with when the evidence cannot answer the question.
INSUFFICIENT_SENTINEL = "INSUFFICIENT_EVIDENCE"

NOTE_NO_RELEVANT_CHUNKS = (
    "No passage in the selected documents was similar enough to your question. "
    "Try rephrasing it, selecting different documents, or uploading a document that covers this topic."
)
NOTE_MODEL_DECLINED = (
    "The retrieved passages did not contain enough information to answer this question."
)
NOTE_UNVERIFIABLE = (
    "The AI reply did not reference any of the retrieved evidence, so it was not shown "
    "because it could not be verified against your documents."
)


def model_declined(llm_text: str) -> bool:
    """True if the model replied with the insufficient-evidence sentinel."""
    return INSUFFICIENT_SENTINEL in llm_text.upper().replace(" ", "_")
