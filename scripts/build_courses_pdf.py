#!/usr/bin/env python3
"""Build the AI Product Development course-description PDFs.

Parses the curriculum markdown files directly so the PDFs always match the
source, and emits four files into this repo: one per emphasis (foundation core
+ that track) and one complete file (foundation core + all three tracks).
Mirrors the USHE "Course Description" layout (summary tables, section bars,
course rows with right-aligned credits/hours, description paragraph, bulleted
objectives) with all institutional branding removed.

Usage:
    pip install reportlab
    python scripts/build_courses_pdf.py

Reads the curriculum markdown from the sibling vault folder
"Projects/AI Product Development Program" and writes the PDFs next to the
page in MTECH-pages/. Rerun after editing any curriculum markdown, then
commit the regenerated PDFs.
"""
import re
import pathlib
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether,
)
from reportlab.pdfgen import canvas as pdfcanvas

# Paths derive from this file's location: scripts/ -> MTECH-pages/ -> vault root.
OUTDIR = pathlib.Path(__file__).resolve().parents[1]
VAULT = OUTDIR.parent
PROJ = VAULT / "Projects/AI Product Development Program"

FILES = {
    "core": "AI Product Development Core Curriculum.md",
    "design": "AI Product Development Design Track Curriculum.md",
    "web": "AI Product Development Web Track Curriculum.md",
    "ios": "AI Product Development iOS Track Curriculum.md",
}

# ── styles ──
styles = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=14,
                            leading=18, alignment=1, spaceAfter=2),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=10,
                               leading=14, alignment=1, spaceAfter=14),
    "sectionhead": ParagraphStyle("sectionhead", fontName="Helvetica-Bold",
                                  fontSize=10, leading=13, alignment=1,
                                  spaceBefore=10, spaceAfter=4),
    "coursename": ParagraphStyle("coursename", fontName="Helvetica-Bold",
                                 fontSize=9.5, leading=12),
    "colnum": ParagraphStyle("colnum", fontName="Helvetica-Bold", fontSize=9.5,
                             leading=12, alignment=2),
    "barlabel": ParagraphStyle("barlabel", fontName="Helvetica-Bold",
                               fontSize=9.5, leading=12),
    "barcolsm": ParagraphStyle("barcolsm", fontName="Helvetica-Bold",
                               fontSize=8, leading=10, alignment=2),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9,
                           leading=12.5, spaceBefore=3, spaceAfter=2),
    "objhead": ParagraphStyle("objhead", fontName="Helvetica-Bold", fontSize=9,
                              leading=12.5, spaceBefore=2, spaceAfter=1),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9,
                             leading=12.5, leftIndent=14, bulletIndent=4),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=9, leading=12),
    "cellnum": ParagraphStyle("cellnum", fontName="Helvetica", fontSize=9,
                              leading=12, alignment=2),
}

CONTENT_W = letter[0] - 1.5 * inch
SUMMARY_COLS = [CONTENT_W - 110, 55, 55]


def P(text, style):
    return Paragraph(escape(text), style)


# ── markdown parsing ──
def parse(path):
    text = path.read_text()
    label = None
    for line in text.splitlines():
        m = re.match(r'^##\s+(.*\(Required Hours.*\))\s*$', line)
        if m:
            label = m.group(1).strip()
            break
    body = text.split("## Course Descriptions", 1)[1]
    courses = []
    for block in re.split(r'\n###\s+', body)[1:]:
        lines = block.splitlines()
        title = lines[0].strip()
        rest = "\n".join(lines[1:])
        m = re.search(r'\*([\d.]+)\s+credits?\s*/\s*([\d.]+)\s+hours\*', rest)
        credits, hours = float(m.group(1)), float(m.group(2))
        after = rest[m.end():]
        desc_part, _, obj_part = after.partition("Course Objectives:")
        desc = " ".join(l.strip() for l in desc_part.strip().splitlines() if l.strip())
        objectives = []
        for l in obj_part.strip().splitlines():
            l = l.strip()
            if l.startswith("- "):
                objectives.append(l[2:].strip())
            elif l.startswith("---"):
                break
        courses.append((title, credits, hours, desc, objectives))
    return label, courses


SECTIONS = {key: parse(PROJ / name) for key, name in FILES.items()}


# ── flowable builders ──
def summary_table(label, courses):
    data = [[P(label, styles["barlabel"]),
             P("Credits", styles["barcolsm"]),
             P("Hours", styles["barcolsm"])]]
    for title, credits, hours, _, _ in courses:
        data.append([P(title, styles["cell"]),
                     P(f"{credits:.2f}", styles["cellnum"]),
                     P(f"{hours:.2f}", styles["cellnum"])])
    t = Table(data, colWidths=SUMMARY_COLS, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.88, 0.88, 0.88)),
        ("LINEABOVE", (0, 0), (-1, 0), 0.75, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.Color(0.6, 0.6, 0.6)),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def section_bar(label):
    t = Table([[P(label, styles["barlabel"]),
                P("Credits", styles["barcolsm"]),
                P("Hours", styles["barcolsm"])]],
              colWidths=SUMMARY_COLS)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.Color(0.88, 0.88, 0.88)),
        ("LINEABOVE", (0, 0), (-1, 0), 0.75, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def course_block(title, credits, hours, desc, objectives):
    head = Table([[P(title, styles["coursename"]),
                   P(f"{credits:.2f}", styles["colnum"]),
                   P(f"{hours:.2f}", styles["colnum"])]],
                 colWidths=SUMMARY_COLS)
    head.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.Color(0.6, 0.6, 0.6)),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow = [Spacer(1, 8), head, P(desc, styles["body"]),
            P("Course Objectives:", styles["objhead"])]
    for o in objectives:
        flow.append(Paragraph(escape(o), styles["bullet"], bulletText="•"))
    return KeepTogether(flow)


class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self.setFont("Helvetica", 8)
            self.drawCentredString(letter[0] / 2, 0.5 * inch,
                                   f"{self._pageNumber} of {total}")
            super().showPage()
        super().save()


def build(out_name, title, subtitle, section_keys):
    story = [P(title, styles["title"]), P(subtitle, styles["subtitle"])]
    # summary tables
    for i, key in enumerate(section_keys):
        label, courses = SECTIONS[key]
        story.append(summary_table(label, courses))
        story.append(Spacer(1, 10 if i < len(section_keys) - 1 else 16))
    # full descriptions
    for i, key in enumerate(section_keys):
        label, courses = SECTIONS[key]
        if i:
            story.append(Spacer(1, 14))
        story.append(P(label.replace(" (", " Courses (", 1), styles["sectionhead"]))
        story.append(section_bar(label))
        for c in courses:
            story.append(course_block(*c))

    doc = BaseDocTemplate(str(OUTDIR / out_name), pagesize=letter,
                          leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                          topMargin=0.75 * inch, bottomMargin=0.85 * inch,
                          title=title)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame])])
    doc.build(story, canvasmaker=NumberedCanvas)
    print("wrote", out_name)


EMPHASIS_SUB = "Catalog Year: 2027, Required Hours: 720, Credits: 24"

build("ai-product-development-design.pdf",
      "AI Product Development: Design Course Description",
      EMPHASIS_SUB, ["core", "design"])
build("ai-product-development-web.pdf",
      "AI Product Development: Web Course Description",
      EMPHASIS_SUB, ["core", "web"])
build("ai-product-development-ios.pdf",
      "AI Product Development: iOS Course Description",
      EMPHASIS_SUB, ["core", "ios"])
build("ai-product-development-full.pdf",
      "AI Product Development Course Description",
      "Catalog Year: 2027  ·  Foundation Core and All Specialization Tracks",
      ["core", "design", "web", "ios"])
