# 5-Minute Demo Script

**Before you start (do this ahead of time):** backend and frontend running, `GEMINI_API_KEY` set (or be ready to demo retrieval-only mode), and **upload the sample PDF once beforehand** so the embedding model is already downloaded and loaded. Reset with a fresh `server\data` folder if you want an empty dashboard for step 2.

| Time | What to do | What to say / point out |
|---|---|---|
| 0:00 | Open the **Dashboard**. | "EvidenceAI answers questions from *your* documents and shows exactly where each answer came from. It is a student prototype, not a production tool." Point at the banner: it reports whether Gemini is configured. |
| 0:45 | Drag `sample_data/evidenceai_sample_paper.pdf` into the upload box. | "The backend reads each page with PyMuPDF, splits it into overlapping chunks, creates embeddings, and stores them in ChromaDB with the page number." Show the card: 3 pages, N chunks, status *Processed*. Mention the PDF is fictional. |
| 1:30 | Click **Ask questions about this document**. Ask: *"What are the limitations of the study?"* | Read the answer. Point at **E1 / page 3** in the citation card and the excerpt. "The page and excerpt come from our database, not from the AI." |
| 2:30 | Ask: *"How often did the sensors record readings?"* | The citation should now be from **page 2** (Methods). "Each chunk keeps its own page number." *(Retrieval with the real model was not verified when this was written; if another page ranks first, point out that the excerpt shown is still the real text from that page.)* |
| 3:15 | Ask something the PDF does not cover: *"What was the total budget of the project?"* | Show the amber **Insufficient evidence** state. "Instead of guessing, it refuses. Gemini was not even called when nothing relevant is found." *(If the real model finds a weakly related passage, say honestly that the relevance threshold needs tuning — see the limitations.)* |
| 4:00 | Open **Evaluation**. | "These are plain counts — documents, chunks, questions, answers, insufficient-evidence responses. We have not computed accuracy scores, and the page says so." |
| 4:30 | *(Optional)* Stop the backend and refresh, or remove the API key. | Show the clear red/amber banners: no silent fake answers. In retrieval-only mode the answer area says no AI answer was generated and shows only retrieved evidence. |
| 5:00 | Close. | Mention the limitations: no OCR, single user, evidence check is structural, thresholds untuned. |

## Sample questions for the bundled PDF

- Expected to work (verify with your setup): *What are the limitations?* · *How many buildings were treated?* · *How often did the sensors record readings?* · *What future work is recommended?*
- Should return **insufficient evidence**: *What was the total budget?* · *Who funded the research?* · *What coating brand was used?*

## If something goes wrong during the demo

- Red banner → backend is not running (Terminal 1).
- Very slow first answer/upload → embedding model loading; wait once.
- "AI service unavailable" status → check the API key/model name; the evidence is still shown.
