# Sample data

## `evidenceai_sample_paper.pdf`

A **fictional** 3-page "research paper" (*Cool Roofs and Neighbourhood Temperatures: A Fictional Pilot Study*) created for demonstrating EvidenceAI. The city, study, numbers and authors are all invented — do not cite it as real research.

It is self-created for this project and released under **CC0 (public domain)**: reuse, modify and redistribute freely.

| Page | Content | Good test questions |
|---|---|---|
| 1 | Abstract and introduction | *How many buildings were treated? How much cooler were coated roofs?* |
| 2 | Methods | *How often did the sensors record readings? Why were rainy days removed?* |
| 3 | Results and limitations | *What are the limitations? What future work is recommended?* |

**Not covered by the document** (should give *insufficient evidence*): budget, funding, coating brand, residents' opinions.

Regenerate it (needs `reportlab`, listed in `server/requirements-dev.txt`):

```powershell
python sample_data\generate_sample_pdf.py
```

Do **not** put your own or private PDFs in this folder: `.gitignore` blocks every `*.pdf` except the sample.
