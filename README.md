# Resume Analyzer

A lightweight, automated resume analysis and ATS screening tool built with Python and Flask. Designed with a clean, solid interface (zero icons, zero clutter) for transparent and accurate resume auditing.

## Features

- **Automated Text Extraction**: Reads and parses text directly from PDF resumes in memory using PyPDF.
- **ATS Criteria Audit**:
  - Technical skills detection across major programming languages, databases, and frameworks using exact word-boundary regex patterns.
  - Verification of standard resume sections (Education, Skills, Projects, Experience, Certifications).
  - Identification of high-impact engineering action keywords.
  - Document formatting hygiene checks (contact info, word count, character bounds).
- **Target Job Description Matching**:
  - Compares candidate resume against pasted job postings.
  - Computes skill match percentage and keyword overlap.
  - Highlights matched vs missing requirements.
- **PDF Report Generation**: Exports an ATS audit summary as a downloadable PDF report generated with ReportLab.
- **Zero Privacy Risk**: Resumes are processed in memory and never stored permanently on external servers.

## Tech Stack

- **Backend**: Python 3, Flask, PyPDF, ReportLab
- **Frontend**: Semantic HTML5, Vanilla CSS (modular design tokens, no external framework or icon font dependencies)

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/arthsingh108-a11y/ResumeAnalyzer.git
cd ResumeAnalyzer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python app.py
```

### 4. Access the web interface
Open your browser and navigate to:
```
http://localhost:5001
```
*(Default port is set to `5001` to prevent macOS AirPlay port 5000 conflicts).*

## Project Structure

```
├── app.py              # Flask server, text analysis & PDF generation logic
├── requirements.txt    # Project dependencies
├── .gitignore          # Git ignore configuration
├── static/
│   └── style.css       # Clean, solid stylesheet
└── templates/
    ├── index.html      # Upload & input interface
    └── dashboard.html  # Results dashboard & metrics breakdown
```

## License

MIT License. Open for educational and personal use.
