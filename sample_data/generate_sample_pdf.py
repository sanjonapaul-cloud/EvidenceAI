"""Generates sample_data/evidenceai_sample_paper.pdf (a FICTIONAL paper written for demos).

Everything in the PDF is invented for the EvidenceAI demonstration. The study, the numbers and
the authors do not exist. The content is released as CC0 (public domain): reuse it freely.

Usage (needs reportlab):  python sample_data/generate_sample_pdf.py
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

OUTPUT = Path(__file__).resolve().parent / "evidenceai_sample_paper.pdf"

styles = getSampleStyleSheet()
title = ParagraphStyle("T", parent=styles["Title"], fontSize=18, leading=22)
h = ParagraphStyle("H", parent=styles["Heading2"], fontSize=13, spaceBefore=10)
body = ParagraphStyle("B", parent=styles["BodyText"], fontSize=11, leading=16, spaceAfter=8)
note = ParagraphStyle("N", parent=body, fontSize=9, textColor="#555555")

story = [
    Paragraph("Cool Roofs and Neighbourhood Temperatures: A Fictional Pilot Study", title),
    Paragraph(
        "FICTIONAL DOCUMENT - written for the EvidenceAI demonstration. The study, data and "
        "authors are invented and must not be cited as real research.",
        note,
    ),
    Paragraph("1. Abstract and Introduction", h),
    Paragraph(
        "This pilot study examines whether reflective roof coatings, often called cool roofs, can "
        "reduce rooftop surface temperatures and indoor temperatures in a dense residential "
        "district of the imaginary city of Marlow Bay. Urban heat is a growing concern because "
        "dark roofing materials absorb sunlight and release heat into the surrounding air.",
        body,
    ),
    Paragraph(
        "The research team treated forty apartment buildings. Twenty buildings received a "
        "white reflective coating and twenty kept their original dark bitumen roofs. The main "
        "research question was how much cooler the coated roofs were during peak afternoon hours "
        "compared with the untreated roofs.",
        body,
    ),
    Paragraph(
        "The key finding is that coated roofs were on average 11.4 degrees Celsius cooler at "
        "the surface at 2 pm during the measurement period. Top-floor apartments under coated "
        "roofs were on average 1.9 degrees Celsius cooler indoors than comparable apartments "
        "under untreated roofs.",
        body,
    ),
    PageBreak(),
    Paragraph("2. Methods", h),
    Paragraph(
        "Each coated building was paired with an untreated building of similar height, age and "
        "orientation so that the comparison would be fair. Wireless temperature sensors were "
        "fixed to every roof surface and inside one top-floor apartment in each building. The "
        "sensors recorded a reading every ten minutes from 1 June to 31 August.",
        body,
    ),
    Paragraph(
        "Air temperature data from a public weather station two kilometres away was used to "
        "check that both groups experienced the same weather. Days with heavy rain were removed "
        "from the analysis because rain cools all roofs and hides the effect of the coating. "
        "In total 78 of the 92 days were kept.",
        body,
    ),
    Paragraph(
        "Residents gave consent for the indoor sensors. Sensor readings were averaged for each "
        "building and each hour. Differences between paired buildings were then averaged across "
        "all pairs. The team used a paired comparison because it removes differences between "
        "buildings that are unrelated to the roof coating.",
        body,
    ),
    PageBreak(),
    Paragraph("3. Results and Limitations", h),
    Paragraph(
        "Results: Over the 78 analysed days, coated roofs peaked at an average of 41.2 degrees "
        "Celsius at the surface, while untreated roofs peaked at 52.6 degrees Celsius. The "
        "difference was largest in July and smallest in late August when the sun was lower.",
        body,
    ),
    Paragraph(
        "Limitations: The study covered a single city and only one summer, so the results may "
        "not generalise to other climates or other years. The sample of forty buildings is "
        "small. The long-term durability of the coating was not measured, and the team did not "
        "assess how dirt build-up could reduce reflectivity over several years. Indoor "
        "temperature was measured in only one apartment per building.",
        body,
    ),
    Paragraph(
        "Future work: A multi-year study across several cities is recommended, together with "
        "measurements of coating durability and of the effect on neighbourhood air temperature "
        "at street level.",
        body,
    ),
    Spacer(1, 0.5 * cm),
]

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    title="Cool Roofs and Neighbourhood Temperatures: A Fictional Pilot Study",
    author="EvidenceAI demo (fictional)",
    leftMargin=2.2 * cm,
    rightMargin=2.2 * cm,
    topMargin=2.2 * cm,
    bottomMargin=2.2 * cm,
)
doc.build(story)
print(f"Wrote {OUTPUT}")
