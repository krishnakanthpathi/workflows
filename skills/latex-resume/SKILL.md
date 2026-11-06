---
name: latex-resume
description: "CRITICAL MUST-USE: Compile, render, preview, and update single-page ATS-optimized LaTeX resumes using Tectonic and Poppler. Trigger whenever the user asks to view, edit, recompile, preview, or print their resume or CV."
version: 1.0.0
author: Krishna Kanth
license: MIT
metadata:
  icon: "📄"
hermes:
  tags: [resume, cv, latex, tectonic, career, pdf-generation]
  related_skills: [python, pdf-generation]
---

# 📄 ATS LaTeX Resume Engine

Automated single-page ATS-compliant resume compilation, previewing, and editing engine powered by **Tectonic** and **Poppler**.

---

## 🚀 Strict Execution Protocol

Whenever the user asks to **view**, **update**, **compile**, **preview**, or **print** their resume:

1. **Active Files**:
   * **LaTeX Source**: [`resume.tex`](file:///Users/krishnakanth/.gemini/antigravity/scratch/latex-resume/resume.tex)
   * **Compiled Output**: [`resume.pdf`](file:///Users/krishnakanth/.gemini/antigravity/scratch/latex-resume/resume.pdf)
   * **Visual Render**: [`resume_preview-1.png`](file:///Users/krishnakanth/.gemini/antigravity/scratch/latex-resume/resume_preview-1.png)

2. **Automated Compilation CLI**:
   Run the CLI directly:
   ```bash
   python3 /Users/krishnakanth/Projects/workflow/skills/latex-resume/scripts/build_resume.py [options]
   ```
   **Options**:
   * `--preview`: Compiles and opens the PDF immediately in macOS Preview (`open resume.pdf`).
   * `--no-render`: Skips generating the PNG image preview.
   * `--tex <path>`: Compiles a custom `.tex` file instead of the default.

3. **Return Media Protocol**:
   The CLI outputs:
   `MEDIA:<absolute_path_to_pdf>`
   Always include a link to the compiled PDF in your response:
   `[resume.pdf](file:///Users/krishnakanth/.gemini/antigravity/scratch/latex-resume/resume.pdf)`.

---

## 📐 Layout & ATS Guidelines

* **Strict 1-Page Rule**: Resumes for early-career / university graduates MUST fit on a single page. If content overflows, adjust `\vspace`, trim bullet points, or reduce font sizes slightly rather than spilling onto page 2.
* **ATS Compatibility**:
  * Single-column text flow across sections.
  * Standard font encodings and clickable hyperref links for GitHub, LinkedIn, and personal portfolio.
  * No graphic tables, floating text boxes, or non-standard icon fonts that confuse automated parser systems.
* **Bullet Point Formula**:
  * `[Action Verb] + [Specific Tech / Framework] + [Metric / Impact]`.
  * *Example*: *"Optimized database schemas across MongoDB and MySQLi, accelerating retrieval speeds by 35\% and enforcing strict data consistency."*
