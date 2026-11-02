from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Agentic_AI_Coworkers_Submission_Report.docx"


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def borders(table, color="D9D9D9"):
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    border = tbl_pr.first_child_found_in("w:tblBorders")
    if border is None:
        border = OxmlElement("w:tblBorders")
        tbl_pr.append(border)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = border.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            border.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_cell(cell, text, bold=False, color="17211F", size=9.5):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(text)
    run.bold = bold
    run.font.name = "Aptos"
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    borders(t)
    for i, h in enumerate(headers):
        set_cell(t.rows[0].cells[i], h, bold=True, color="FFFFFF", size=9)
        shade(t.rows[0].cells[i], "0E6B55")
    for row_i, row in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(row):
            set_cell(cells[i], str(value), size=9)
            if row_i % 2 == 1:
                shade(cells[i], "F3F7F3")
    if widths:
        for row in t.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.space_after = Pt(3)
    p.add_run(text)
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = RGBColor(0, 0, 0)
    return p


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(0.7)
section.bottom_margin = Inches(0.65)
section.left_margin = Inches(0.8)
section.right_margin = Inches(0.8)

styles = doc.styles
styles["Normal"].font.name = "Aptos"
styles["Normal"].font.size = Pt(10.5)
styles["Normal"].font.color.rgb = RGBColor(23, 33, 31)
styles["Normal"].paragraph_format.space_after = Pt(7)
styles["Normal"].paragraph_format.line_spacing = 1.08
for name, size in [("Title", 25), ("Heading 1", 17), ("Heading 2", 13), ("Heading 3", 11)]:
    styles[name].font.name = "Aptos Display"
    styles[name].font.size = Pt(size)
    styles[name].font.color.rgb = RGBColor(0, 0, 0)

header = section.header.paragraphs[0]
header.text = "SJSU · Agentic AI Coworkers · Project Report"
header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
header.runs[0].font.size = Pt(8)
header.runs[0].font.color.rgb = RGBColor(111, 125, 119)
footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer_run = footer.add_run("San José State University · November 2026")
footer_run.font.size = Pt(8)
footer_run.font.color.rgb = RGBColor(111, 125, 119)

title = doc.add_paragraph(style="Title")
title.add_run("Agentic AI Coworkers")
subtitle = doc.add_paragraph()
subtitle.paragraph_format.space_after = Pt(18)
r = subtitle.add_run("Daily technical learning and personalized career readiness")
r.bold = True
r.font.size = Pt(14)
r.font.color.rgb = RGBColor(14, 107, 85)

meta = doc.add_paragraph()
meta.add_run("Student project · San José State University\n").bold = True
meta.add_run("Prepared for the October 15, 2026 agentic AI assignment\n")
meta.add_run("Prototype date: November 1, 2026")

doc.add_paragraph(
    "This report documents two executable Agentic AI Coworkers. The Python runner is the working prototype: it retrieves and ranks technical sources, analyzes opportunity channels, generates exercises, evaluates learner answers, records state transitions, and persists shared memory. The HTML dashboard is a visual demonstration layer, not the agent implementation."
)

heading(doc, "Executive Summary", 1)
doc.add_paragraph(
    "The project implements a two-agent learning and career loop for an SJSU student preparing for AI and machine-learning engineering opportunities. DailyTechUpgradeAgent produces a 15–20 minute brief from authoritative technical sources and connects each recommendation to the learner’s active gaps. nextLevelPersonalCoachForCareerLevel analyzes a target role, identifies opportunity channels, asks technical questions, evaluates answers, generates a coding exercise and interview scenario, and stores the next preparation actions."
)
table(doc, ["Agent", "Primary outcome", "Executable command"], [
    ["DailyTechUpgradeAgent", "Daily Top 3 brief with source metadata, summary, relevance, and next action", "python3 agentic_workers.py daily"],
    ["nextLevelPersonalCoachForCareerLevel", "Career readiness assessment with feedback, opportunities, exercise, and plan", "python3 agentic_workers.py coach --interactive"],
])

heading(doc, "1 Agent Goals", 1)
heading(doc, "DailyTechUpgradeAgent", 2)
doc.add_paragraph("Goal: become a better technical learner every day through a focused, trustworthy reading habit.")
for item in [
    "Discover three relevant technical articles or blog posts from authoritative sources.",
    "Summarize the technical idea and state one practical takeaway.",
    "Personalize ranking using interests, active knowledge gaps, target role, and prior learning memory.",
    "Keep the session within 15–20 minutes and end with an applied next action.",
]: bullet(doc, item)
heading(doc, "nextLevelPersonalCoachForCareerLevel", 2)
doc.add_paragraph("Goal: prepare the learner for the next internship, job, research, or entrepreneurial opportunity through evidence-based practice.")
for item in [
    "Analyze a target role and identify internship, job, research, SJSU career, and startup opportunity channels.",
    "Generate technical questions, a coding exercise, and an interview scenario.",
    "Evaluate answers with a visible rubric, identify strengths and gaps, and ask a follow-up question.",
    "Persist progress, active gaps, completed sessions, and next actions in shared memory.",
]: bullet(doc, item)

heading(doc, "2 Architecture and Agent Workflow", 1)
doc.add_paragraph("Both workers use the same inspectable loop: observe learner memory, call tools, transition through explicit states, reflect against a constraint or rubric, and save the result.")
architecture = (
    "AUTHORITATIVE SOURCES / OPPORTUNITY CHANNELS\n"
    "                ↓\n"
    "RETRIEVER + SOURCE VERIFIER → INTENT / PRIORITY ROUTER\n"
    "                ↓                         ↓\n"
    "DailyTechUpgradeAgent       nextLevelPersonalCoachForCareerLevel\n"
    "RETRIEVE → RANK → SUMMARIZE  ANALYZE → PLAN → ASSESS → FOLLOW-UP\n"
    "                ↓                         ↓\n"
    "15–20 MIN BRIEF              READINESS REPORT + ACTION PLAN\n"
    "                ↘           ↙\n"
    "            SHARED LEARNER MEMORY"
)
p = doc.add_paragraph()
p.paragraph_format.left_indent = Inches(0.35)
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(12)
run = p.add_run(architecture)
run.font.name = "Courier New"
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(14, 107, 85)

table(doc, ["Component", "Role in the system", "Implementation evidence"], [
    ["Source retriever", "Collect live RSS items and verified fallback sources", "AWS, LangChain, and Google Cloud RSS attempts; official fallback records"],
    ["Opportunity analyzer", "Map target role to concrete opportunity paths", "LinkedIn search, SJSU Career Center, NSF REU, YC Co-Founder Matching"],
    ["Personalization scorer", "Rank content against interests and active gaps", "Tag overlap score stored in each recommendation"],
    ["Assessment engine", "Evaluate technical answers and follow-ups", "States, guardrails, recovery, persistence rubric"],
    ["Model adapter", "Generate richer summaries and feedback when configured", "OpenAI Responses API via OPENAI_API_KEY; offline fallback otherwise"],
    ["Memory store", "Persist learner profile, events, briefs, sessions, and gaps", ".agent_memory.json"],
])

heading(doc, "3 Working Prototype", 1)
doc.add_paragraph("The prototype is dependency-free and runs from a terminal. It can use the OpenAI Responses API when an API key is configured, but it does not require a key for demonstration or grading.")
heading(doc, "Run both agents", 2)
code = doc.add_paragraph()
code.paragraph_format.left_indent = Inches(0.25)
code.add_run('cd "agentic coworkers"\npython3 agentic_workers.py demo').font.name = "Courier New"
heading(doc, "Run the interactive coach", 2)
code = doc.add_paragraph()
code.paragraph_format.left_indent = Inches(0.25)
code.add_run("python3 agentic_workers.py coach --interactive\n\nThe coach asks a system-design question, evaluates the answer, asks a safety/observability follow-up, and saves the session.").font.name = "Courier New"
heading(doc, "Optional model-backed mode", 2)
doc.add_paragraph("To use model-generated summaries and coaching feedback, set an API key in the terminal session. The key is read from the environment and is never written to project files.")
code = doc.add_paragraph()
code.paragraph_format.left_indent = Inches(0.25)
code.add_run('export OPENAI_API_KEY="your-key"\npython3 agentic_workers.py demo').font.name = "Courier New"

heading(doc, "4 Sample Results", 1)
heading(doc, "Daily technical brief", 2)
table(doc, ["Article", "Source and date", "Technical insight", "Career connection"], [
    ["How we detect frontier model misalignment", "OpenAI · Oct 29, 2026", "Monitor agent reasoning, actions, and environmental effects to detect unauthorized behavior.", "Builds safety and observability judgment for agent-system interviews."],
    ["Gemini at Work 2026: Introducing the Gemini agent", "Google Cloud · Oct 8, 2026", "Production agents require memory, identity, authorization, sandboxing, and observability.", "Connects architecture decisions to secure deployment."],
    ["Advancing computer use with Ironclad", "OpenAI · Oct 6, 2026", "Professional agents need business rules, multi-step execution, and outcome verification.", "Improves ability to explain reliable tool-using systems."],
])
doc.add_paragraph("The fallback records link to the official source pages. When live RSS is reachable, the agent ranks current feed items first and preserves the same output schema.")

heading(doc, "Interactive career coaching session", 2)
doc.add_paragraph("Prompt: An agent may search the web, but a human must approve external side effects. Describe the state transitions, guardrails, and recovery path.")
doc.add_paragraph("Example learner answer: I would use Ready, ToolProposed, AwaitingApproval, Executing, Succeeded, and Failed states. Permission checks happen before side effects. I would persist the trace and retry transient failures.")
table(doc, ["Rubric dimension", "Result", "Evidence"], [
    ["States", "Pass", "Ready, ToolProposed, AwaitingApproval, Executing, Succeeded, Failed"],
    ["Guardrails", "Pass", "Permission and human approval before side effects"],
    ["Recovery", "Pass", "Retry transient failures and represent Failed state"],
    ["Persistence", "Pass", "Persist trace and approval decision"],
])
doc.add_paragraph("Generated coding exercise: implement an approval-aware agent trace function that returns READY, AWAITING_APPROVAL, EXECUTING, SUCCEEDED, or FAILED, rejects side effects without approval, and records a trace event.")
doc.add_paragraph("Generated interview scenario: explain how the agent would be observed, secured, and evaluated in production.")

heading(doc, "5 Personalization and Memory", 1)
table(doc, ["Memory field", "Current value", "How it changes behavior"], [
    ["Interests", "AI agents, evaluation, Python APIs", "Ranks articles with matching tags"],
    ["Target role", "AI/ML Engineer Intern", "Shapes opportunity analysis and coaching rubric"],
    ["Active gaps", "Observability, production system design", "Selects takeaways, coding exercise, and preparation plan"],
    ["Milestone", "Prepare a portfolio-ready agent system", "Converts reading into an applied next action"],
])
doc.add_paragraph("Every run saves timestamps, state transitions, recommendations, assessment results, opportunities, exercises, and next actions. This makes progress inspectable rather than inferred from chat length.")

heading(doc, "6 Evaluation", 1)
table(doc, ["Dimension", "Metric", "Target"], [
    ["Recommendation accuracy", "Verified title, date, source, URL, and faithful summary", "At least 90% citation correctness"],
    ["Relevance", "Learner rating of each article", "Average of 4/5 or higher"],
    ["Learning transfer", "Pre/post answer on a novel technical prompt", "Improvement in rubric score and application quality"],
    ["Coach calibration", "Agreement with a human rubric across 10 answers", "At least 80% agreement"],
    ["Career progress", "Skill evidence, artifacts, and interview performance", "One applied artifact per week"],
    ["Workflow reliability", "Completed runs and saved trace events", "No silent failure; fallback is labeled"],
])
doc.add_paragraph("Test procedure: run the daily brief for ten days; rate freshness, relevance, and actionability; submit ten technical answers; compare agent feedback with a human rubric; then complete an unseen system-design prompt and compare it with the baseline.")

heading(doc, "7 Limitations and Responsible Use", 1)
for item in [
    "RSS availability varies by source; the agent labels its fallback behavior and preserves official source URLs.",
    "Readiness scores are coaching signals, not hiring predictions.",
    "The learner should inspect and correct stored memory and avoid entering sensitive personal information.",
    "External actions remain outside the prototype; a production deployment should require explicit approval, authentication, rate limits, and tool-level audit logs.",
]: bullet(doc, item)

heading(doc, "8 Submission Checklist", 1)
table(doc, ["Required deliverable", "Where it is provided", "Status"], [
    ["Agent goals", "Sections 1 and 2", "Complete"],
    ["Architecture diagram", "Section 2", "Complete"],
    ["Working prototype", "agentic_workers.py and commands in Section 3", "Complete"],
    ["Sample results", "Section 4 and demo output", "Complete"],
    ["Evaluation", "Section 6", "Complete"],
    ["Supporting dashboard", "index.html", "Complete"],
])

doc.save(OUT)
print(OUT)
