from flask import Flask, render_template, request, make_response, redirect, url_for
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import re

app = Flask(__name__)

# ==========================================================
# CONSTANTS & DICTIONARIES
# ==========================================================

SKILLS = [
    "Python", "Java", "SQL", "JavaScript", "TypeScript", "React",
    "HTML", "CSS", "Git", "Docker", "Machine Learning",
    "Flask", "Django", "C++", "C", "AWS", "Azure",
    "Node.js", "MongoDB", "MySQL", "PostgreSQL"
]

SECTIONS = [
    "Education",
    "Skills",
    "Projects",
    "Experience",
    "Certifications"
]

KEYWORDS = [
    "develop", "developed", "build", "built",
    "design", "designed", "implement", "implemented",
    "analyze", "analysis", "database", "api",
    "testing", "deployment", "cloud", "debugging",
    "optimization", "problem solving", "teamwork",
    "communication"
]

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "you", "your",
    "will", "have", "has", "our", "their", "they", "into", "about", "using", "used",
    "must", "should", "would", "can", "all", "any", "who", "what", "where", "when",
    "how", "job", "role", "work", "working", "team", "years", "year", "required",
    "requirements", "responsibilities", "experience", "candidate", "candidates",
    "skills", "skill", "knowledge", "ability", "strong", "preferred", "duties"
}

# ==========================================================
# ACCURATE MATCHING HELPERS (OPTIMIZED WITH WORD BOUNDARIES)
# ==========================================================

def check_skill_match(skill, text_lower):
    """
    Check if a skill is in text using word boundaries to avoid false positives.
    For example: prevents 'C' from matching inside 'education' or 'Java' inside 'JavaScript'.
    """
    s = skill.lower()
    if s == "c":
        return bool(re.search(r"(?:^|[\s,;/()\[\]])c(?:$|[\s,;/()\[\]+])", text_lower))
    if s in ["c++", "c#", ".net", "node.js"]:
        escaped = re.escape(s)
        return bool(re.search(rf"(?:^|[\s/]){escaped}(?:$|[\s/,.;])", text_lower))
    return bool(re.search(rf"\b{re.escape(s)}\b", text_lower))


def check_word_match(word, text_lower):
    """Word boundary matching for keywords and section names."""
    return bool(re.search(rf"\b{re.escape(word.lower())}\b", text_lower))

# ==========================================================
# RESUME ANALYSIS LOGIC
# ==========================================================

def analyze_resume(text, filename="Resume.pdf"):
    text_lower = text.lower()
    words = text.split()
    word_count = len(words)
    char_count = len(text)

    # 1. Technical Skills
    found_skills = [s for s in SKILLS if check_skill_match(s, text_lower)]
    missing_skills = [s for s in SKILLS if s not in found_skills]
    skill_score = int((len(found_skills) / len(SKILLS)) * 100) if SKILLS else 0

    # 2. Standard Sections
    found_sections = [sec for sec in SECTIONS if check_word_match(sec, text_lower)]
    section_score = int((len(found_sections) / len(SECTIONS)) * 100) if SECTIONS else 0

    # 3. Action Keywords
    found_keywords = [kw for kw in KEYWORDS if check_word_match(kw, text_lower)]
    keyword_score = int((len(found_keywords) / len(KEYWORDS)) * 100) if KEYWORDS else 0

    # 4. Projects & Experience
    project_experience_score = 0
    if check_word_match("projects", text_lower) or check_word_match("project", text_lower):
        project_experience_score += 50
    if check_word_match("experience", text_lower):
        project_experience_score += 50

    # 5. Formatting & Readability Checks
    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text))
    has_phone = bool(re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", text))
    length_ok = 500 <= char_count <= 12000
    word_count_ok = word_count >= 150
    has_core_sections = check_word_match("education", text_lower) and check_word_match("skills", text_lower)

    formatting_checks = sum([has_email, has_phone, length_ok, word_count_ok, has_core_sections])
    format_score = formatting_checks * 20

    # 6. Overall Weighted ATS Score
    ats_score = int(
        (skill_score * 0.40) +
        (section_score * 0.20) +
        (keyword_score * 0.20) +
        (project_experience_score * 0.10) +
        (format_score * 0.10)
    )

    # 7. Actionable Recommendations
    suggestions = []
    if skill_score < 70:
        suggestions.append(f"Add key technical skills: consider including missing competencies such as {', '.join(missing_skills[:5])}.")
    if "Projects" not in found_sections:
        suggestions.append("Add a dedicated Projects section describing technical stack, implementation details, and outcomes.")
    if "Experience" not in found_sections:
        suggestions.append("Include an Experience section covering internships, open-source work, or project contributions.")
    if "Certifications" not in found_sections:
        suggestions.append("Consider listing relevant industry certifications or online coursework (e.g. AWS, Coursera, HackerRank).")
    if keyword_score < 60:
        suggestions.append("Incorporate stronger action verbs in your bullet points (e.g. developed, implemented, optimized, deployed).")
    if not has_email or not has_phone:
        suggestions.append("Ensure your primary contact information (email address and phone number) is clearly placed at the top.")
    if not length_ok:
        suggestions.append("Adjust resume length to a standard single or two-page format (between 500 and 12,000 characters).")
    if not suggestions:
        suggestions.append("Your resume satisfies all primary automated ATS screening heuristics.")

    return {
        "filename": filename,
        "word_count": word_count,
        "char_count": char_count,
        "analyzed_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "ats_score": ats_score,
        "found_skills": found_skills,
        "missing_skills": missing_skills,
        "skill_score": skill_score,
        "found_sections": found_sections,
        "section_score": section_score,
        "found_keywords": found_keywords,
        "keyword_score": keyword_score,
        "project_experience_score": project_experience_score,
        "format_score": format_score,
        "formatting_details": {
            "has_email": has_email,
            "has_phone": has_phone,
            "length_ok": length_ok,
            "word_count_ok": word_count_ok,
            "has_core_sections": has_core_sections
        },
        "suggestions": suggestions
    }

# ==========================================================
# JOB DESCRIPTION MATCHER LOGIC
# ==========================================================

def evaluate_job_match(resume_text, job_description):
    resume_lower = resume_text.lower()
    job_lower = job_description.lower()

    # Detect skills mentioned in job description
    job_skills = [s for s in SKILLS if check_skill_match(s, job_lower)]
    matched_skills = [s for s in job_skills if check_skill_match(s, resume_lower)]
    missing_skills = [s for s in job_skills if s not in matched_skills]

    # Extract keywords from job description (alphanumeric words)
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", job_lower)
    job_keywords = []
    for w in words:
        if w not in STOPWORDS and w not in job_keywords:
            job_keywords.append(w)
    job_keywords = job_keywords[:35]

    matched_keywords = [w for w in job_keywords if w in resume_lower]
    missing_keywords = [w for w in job_keywords if w not in matched_keywords]

    # Scores
    skill_match_score = int((len(matched_skills) / len(job_skills)) * 100) if job_skills else 100
    keyword_match_score = int((len(matched_keywords) / len(job_keywords)) * 100) if job_keywords else 100

    if job_skills and job_keywords:
        job_match_score = int((skill_match_score * 0.60) + (keyword_match_score * 0.40))
    elif job_skills:
        job_match_score = skill_match_score
    elif job_keywords:
        job_match_score = keyword_match_score
    else:
        job_match_score = 0

    return {
        "job_match_score": job_match_score,
        "skill_match_score": skill_match_score,
        "keyword_match_score": keyword_match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords
    }

# ==========================================================
# ROUTES
# ==========================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
@app.route("/upload", methods=["POST"])
@app.route("/match", methods=["POST"])
def process_analysis():
    resume_file = request.files.get("resume")
    job_description = request.form.get("job_description", "").strip()

    resume_text = ""
    filename = "Resume.pdf"

    if resume_file and resume_file.filename:
        filename = resume_file.filename
        try:
            reader = PdfReader(resume_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    resume_text += extracted + "\n"
        except Exception as e:
            return render_template("index.html", error=f"Could not read the PDF file: {str(e)}"), 400

        if not resume_text.strip():
            return render_template("index.html", error="No readable text found in the PDF. Please upload a standard text PDF, not a scanned image."), 400

        report = analyze_resume(resume_text, filename=filename)
        app.config["resume_text"] = resume_text
        app.config["filename"] = filename
    else:
        # Check if we already have an analyzed resume in memory
        resume_text = app.config.get("resume_text", "")
        report = app.config.get("report")
        filename = app.config.get("filename", "Resume.pdf")

        if not report or not resume_text:
            return render_template("index.html", error="Please upload a resume PDF to begin."), 400

    # Calculate job match if job description was supplied
    if job_description:
        report["job_match"] = evaluate_job_match(resume_text, job_description)
    elif "job_match" in report and resume_file:
        # Reset previous job match on new resume upload if no JD passed
        report.pop("job_match", None)

    app.config["report"] = report

    return render_template(
        "dashboard.html",
        report=report,
        total_skills=len(SKILLS),
        total_keywords=len(KEYWORDS),
        all_sections=SECTIONS
    )


@app.route("/download")
def download():
    report = app.config.get("report")
    if not report:
        return redirect(url_for("home"))

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 45
    y = height - 50

    def new_page():
        nonlocal y
        pdf.showPage()
        y = height - 50

    def draw_heading(title):
        nonlocal y
        if y < 80:
            new_page()
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColorRGB(0.12, 0.14, 0.16)
        pdf.drawString(margin, y, title)
        y -= 6
        pdf.setStrokeColorRGB(0.82, 0.85, 0.88)
        pdf.setLineWidth(0.5)
        pdf.line(margin, y, width - margin, y)
        y -= 16

    def draw_wrapped_text(text, font="Helvetica", size=9, max_w=500):
        nonlocal y
        pdf.setFont(font, size)
        pdf.setFillColorRGB(0.2, 0.2, 0.2)
        words = str(text).split()
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            if pdf.stringWidth(test, font, size) <= max_w:
                line = test
            else:
                if line:
                    if y < 50:
                        new_page()
                    pdf.drawString(margin, y, line)
                    y -= 13
                line = w
        if line:
            if y < 50:
                new_page()
            pdf.drawString(margin, y, line)
            y -= 13

    # Document Header - Clean, solid student project header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.setFillColorRGB(0.12, 0.14, 0.16)
    pdf.drawString(margin, y, "Resume & ATS Analysis Report")
    y -= 16

    pdf.setFont("Helvetica", 9)
    pdf.setFillColorRGB(0.4, 0.45, 0.5)
    meta_str = f"Document: {report.get('filename', 'Resume.pdf')}  |  Generated: {report.get('analyzed_at', '')}  |  Word Count: {report.get('word_count', 0)}"
    pdf.drawString(margin, y, meta_str)
    y -= 20

    # Summary Scores Box
    draw_heading("1. Executive Summary")
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y, f"Overall ATS Score: {report['ats_score']}%")
    if report.get("job_match"):
        pdf.drawString(margin + 200, y, f"Job Match Score: {report['job_match']['job_match_score']}%")
    y -= 18

    # ATS Breakdown Table
    draw_heading("2. ATS Criteria Breakdown")
    breakdown_items = [
        ("Technical Skills (40%)", f"{report['skill_score']}%"),
        ("Standard Sections (20%)", f"{report['section_score']}%"),
        ("Action Keywords (20%)", f"{report['keyword_score']}%"),
        ("Projects & Experience (10%)", f"{report['project_experience_score']}%"),
        ("ATS Formatting & Hygiene (10%)", f"{report['format_score']}%")
    ]
    for label, val in breakdown_items:
        if y < 50:
            new_page()
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.2, 0.2, 0.2)
        pdf.drawString(margin, y, label)
        pdf.drawRightString(width - margin, y, val)
        y -= 14
    y -= 8

    # Skills Analysis
    draw_heading("3. Skills Coverage")
    found_s = ", ".join(report["found_skills"]) if report["found_skills"] else "None detected"
    missing_s = ", ".join(report["missing_skills"]) if report["missing_skills"] else "All tracked skills present"
    draw_wrapped_text(f"Detected Skills ({len(report['found_skills'])}): {found_s}")
    draw_wrapped_text(f"Missing Tracked Skills ({len(report['missing_skills'])}): {missing_s}")
    y -= 8

    # Sections & Keywords
    draw_heading("4. Sections & Keywords")
    found_sec = ", ".join(report["found_sections"]) if report["found_sections"] else "None"
    found_kw = ", ".join(report["found_keywords"]) if report["found_keywords"] else "None"
    draw_wrapped_text(f"Detected Sections: {found_sec}")
    draw_wrapped_text(f"Detected Keywords: {found_kw}")
    y -= 8

    # Job Match (if present)
    if report.get("job_match"):
        jm = report["job_match"]
        draw_heading("5. Job Description Alignment")
        draw_wrapped_text(f"Job Match Score: {jm['job_match_score']}%  (Skills: {jm['skill_match_score']}%, Keywords: {jm['keyword_match_score']}%)")
        match_sk = ", ".join(jm["matched_skills"]) if jm["matched_skills"] else "None"
        miss_sk = ", ".join(jm["missing_skills"]) if jm["missing_skills"] else "None"
        draw_wrapped_text(f"Matched Job Skills: {match_sk}")
        draw_wrapped_text(f"Missing Job Skills: {miss_sk}")
        y -= 8

    # Recommendations
    draw_heading("Recommendations for Improvement")
    for i, suggestion in enumerate(report["suggestions"], start=1):
        draw_wrapped_text(f"{i}. {suggestion}")

    # Footer
    pdf.setFont("Helvetica", 8)
    pdf.setFillColorRGB(0.5, 0.5, 0.5)
    pdf.drawCentredString(width / 2, 28, "Resume Analyzer - Automated Student Project Report")

    pdf.save()
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=resume_analysis.pdf"
    return response

# ==========================================================
# MAIN EXECUTION
# ==========================================================

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print(f"\n* Resume Analyzer running at: http://127.0.0.1:{port} (or http://localhost:{port})\n")
    app.run(host="0.0.0.0", port=port, debug=True)