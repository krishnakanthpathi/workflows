---
name: exam-paper-generator
description: Automated Question Paper Generator (AQPG). Converts structured JSON into authentic, state-board compliant, print-ready examination PDFs with KaTeX math typesetting, right-aligned section marks, centered section headers, and official A4 pagination.
version: 1.0.0
author: Krishna Kanth
license: MIT
metadata:
  icon: "📝"
hermes:
  tags: [education, exam-generator, question-paper, pdf-generation, assessment, katex, school-board]
  related_skills: [python, pdf-generation]
---

# Exam Question Paper Generator (AQPG)

A production-grade, autonomous skill to generate authentic, print-ready school board examination papers (CBSE, AP SSC, TS SSC, ICSE) directly from structured JSON data.

```mermaid
flowchart LR
    A["Syllabus / Chapter Prompt"] --> B["LLM Generates Structured JSON"]
    B --> C["render_paper.py (Jinja2 Engine)"]
    C --> D["HTML + CSS + KaTeX Math"]
    D --> E["Headless Google Chrome Engine"]
    E --> F["Print-Ready A4 Exam PDF"]
    F --> G["Automatic Launch (macOS open)"]
```

---

## 📌 Architecture & Key Structures

The generator is built on three core pillars:

1. **Semantic JSON Data (`examples/*.json`)**:
   - Decouples exam content, marks distribution, and syllabus from the layout.
   - Models metadata (board title, subject, paper code, time, max marks, instructions).
   - Models sections (`section_id`, centered `title`, right-aligned `marks_total`, `instruction`).
   - Supports diverse question types: `mcq` (2-column layout), `short_answer` / VSAQ, `data_analysis` (tables with sub-questions), and `choice_a`/`choice_b` (internal choice essay/experiment questions).
   - Embeds LaTeX mathematical formulas directly with `$...$` (e.g. `$\\frac{1}{f} = \\frac{1}{v} - \\frac{1}{u}$`).

2. **Jinja2 + Print CSS Templates (`templates/`)**:
   - `universal_template.html`: Standard layout for Science (Physics, Chemistry, Biology), Mathematics, Social Studies.
   - `language_template.html`: Specialized layout for Languages (Hindi, Telugu, English) with blueprint tables, 3-column grammar tables, and Part B bits.
   - **Board Rules Compliant**:
     - Clean, pure white paper with high-contrast typography (Times New Roman / academic serif).
     - **Centered section headers** (`SECTION - I`, `SECTION - II`) with **right-aligned marks** (`6 × 1 = 6M`) on the exact same row.
     - Zero unnecessary side-heading descriptions.
     - `@page { size: A4 portrait; margin: 15mm 18mm; }` with dynamic page counters (`Page X`).
     - KaTeX auto-rendering before PDF capture (`renderMathInElement`).
     - Strict page-break prevention (`page-break-inside: avoid; break-inside: avoid;`).

3. **Compiler CLI Engine (`scripts/render_paper.py`)**:
   - Merges JSON data into templates.
   - Automatically detects whether to use universal or language template.
   - Invokes Headless Google Chrome (`--headless --disable-gpu --run-all-compositor-stages-before-draw --no-pdf-header-footer --print-to-pdf=...`).
   - Validates resulting PDF metadata and page count.
   - Supports instant macOS preview via `--open`.

---

## 📂 Directory Layout

```text
exam-paper-generator/
├── SKILL.md                          # Comprehensive skill guide & Hermes prompt contract
├── scripts/
│   ├── render_paper.py               # Main CLI compiler (JSON -> HTML -> PDF)
│   └── open_all_papers.py            # Batch compile & open all sample PDFs
├── templates/
│   ├── universal_template.html       # Science, Math, Social template
│   └── language_template.html        # AP SSC Hindi & Language template
└── examples/
    ├── physics_class10_model_paper.json
    ├── maths_class10_model_paper.json
    ├── biology_lesson2_respiration.json
    └── hindi_class10_model_paper.json
```

---

## 🚀 Quick CLI Usage

### 1. Compile a Single Paper & Open PDF
```bash
python3 /Users/krishnakanth/Projects/workflow/.agents/skills/exam-paper-generator/scripts/render_paper.py \
  /Users/krishnakanth/Projects/workflow/.agents/skills/exam-paper-generator/examples/physics_class10_model_paper.json \
  --open
```

### 2. Batch Compile & Open All Sample Papers
```bash
python3 /Users/krishnakanth/Projects/workflow/.agents/skills/exam-paper-generator/scripts/open_all_papers.py
```

### 3. Specify Custom Output Directory
```bash
python3 scripts/render_paper.py my_paper.json -d ./dist --open
```

### 4. Messaging Platform Delivery (WhatsApp, Telegram, Discord)
When the user asks via WhatsApp or any chat interface to create an exam paper:
1. Generate the structured JSON and save it to `/tmp/exam_paper.json` (or inside the skill directory).
2. Run the compiler:
   ```bash
   python3 scripts/render_paper.py /tmp/exam_paper.json
   ```
3. Deliver the PDF directly to the user by ending your response with the `MEDIA:` directive:
   ```text
   Here is your question paper!
   MEDIA:/tmp/exam_paper.pdf
   ```
   > [!NOTE]
   > The Hermes platform gateway automatically intercepts `MEDIA:<path>` directives, strips the tag from the text, and delivers the file as a native attachment (PDF document) to the chat.

---

## 🤖 Prompt Guide for Low-Tier Models (Hermes / Llama / Mistral)

To make smaller or lower-tier models reliably produce valid JSON without syntax bugs or formatting drifts, copy and paste the prompt template below:

### Prompt Template for Hermes / AI Agents
```text
You are an expert School Board Examination Paper Creator.
Generate a structured JSON question paper for:
- Class: 10th Class
- Subject: [Insert Subject, e.g. Mathematics / Physics / Biology]
- Topic/Chapter: [Insert Topic or Lesson Name]
- Total Marks: 50 Marks (Time: 1 Hour 15 Mins)

STRICT RULES:
1. Return ONLY valid JSON matching this schema. No conversational preamble.
2. Math equations must use LaTeX enclosed in single dollar signs, e.g. $f = +20\text{ cm}$.
3. Section titles MUST be clean: "SECTION - I", "SECTION - II", "SECTION - III", "SECTION - IV".
4. Do NOT include side headings or descriptions in the section title.
5. Provide marks_total for each section (e.g. "6 x 1 = 6M", "4 x 2 = 8M", "4 x 4 = 16M", "2 x 8 = 16M").

JSON FORMAT SCHEMA:
{
  "metadata": {
    "board_title": "BOARD OF SECONDARY EDUCATION, A.P. :: VIJAYAWADA\nSSC PUBLIC EXAMINATIONS - MODEL ASSESSMENT",
    "class": "CLASS X (10th)",
    "subject": "[Subject Name]",
    "chapter_name": "[Chapter Name]",
    "paper_code": "[Code e.g. 19E]",
    "medium": "ENGLISH MEDIUM",
    "time": "1 hour 15 minutes",
    "max_marks": 50,
    "instructions": [
      "First 15 minutes are allotted for reading the question paper thoroughly.",
      "All answers must be written in the answer booklet provided.",
      "The paper consists of 4 Sections: Section I, II, III and IV.",
      "Internal choice is available in Section IV (8 Marks questions)."
    ]
  },
  "sections": [
    {
      "section_id": "I",
      "title": "SECTION - I",
      "instruction": "Note: Answer ALL questions. Each question carries 1 Mark.",
      "marks_total": "6 x 1 = 6M",
      "questions": [
        {"q_no": 1, "type": "short_answer", "question": "Question text...", "marks": "1M"},
        {"q_no": 2, "type": "mcq", "question": "MCQ Question text...", "marks": "1M", "options": ["A) opt 1", "B) opt 2", "C) opt 3", "D) opt 4"]}
      ]
    },
    {
      "section_id": "II",
      "title": "SECTION - II",
      "instruction": "Note: Answer ALL questions in 3-4 sentences each. Each question carries 2 Marks.",
      "marks_total": "4 x 2 = 8M",
      "questions": [
        {"q_no": 7, "type": "short_answer", "question": "Question text...", "marks": "2M"}
      ]
    },
    {
      "section_id": "III",
      "title": "SECTION - III",
      "instruction": "Note: Answer ALL questions in 5-6 sentences each. Each question carries 4 Marks.",
      "marks_total": "4 x 4 = 16M",
      "questions": [
        {
          "q_no": 11,
          "type": "data_analysis",
          "heading": "Analyze the table below and answer questions:",
          "table": {
            "headers": ["Col 1", "Col 2"],
            "rows": [["Row 1 Val 1", "Row 1 Val 2"]]
          },
          "sub_questions": ["i) Sub-question 1?", "ii) Sub-question 2?"],
          "marks": "4M"
        }
      ]
    },
    {
      "section_id": "IV",
      "title": "SECTION - IV",
      "instruction": "Note: Answer ALL questions. Each question carries 8 Marks. Internal choice (A or B) is provided.",
      "marks_total": "2 x 8 = 16M",
      "questions": [
        {
          "q_no": 15,
          "heading": "Answer either (A) or (B):",
          "marks": "8M",
          "choice_a": {"type": "essay", "title": "A) First essay prompt...", "format": "Key points..."},
          "choice_b": {"type": "essay", "title": "B) Second essay prompt...", "format": "Key points..."}
        }
      ]
    }
  ]
}
```

---

## 🛠️ Verification & Troubleshooting

- **Google Chrome Binary**:
  The script automatically checks standard paths on macOS (`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`). If using Linux or a server, ensure `chromium` or `google-chrome` is installed.
- **KaTeX Math Rendering**:
  Formulas are rendered client-side before Chrome captures the PDF using KaTeX auto-render. `--run-all-compositor-stages-before-draw` guarantees that math formulas are completely drawn before the PDF raster is captured.
- **Pagination & Spacing**:
  If a question breaks awkwardly across pages, the CSS `.question-row` and `.choice-card` have `page-break-inside: avoid !important; break-inside: avoid !important;`.
