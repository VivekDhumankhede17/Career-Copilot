# 🚀 Career Copilot AI

> **AI-Powered Career Intelligence Platform** — Upload your resume, enter your dream role, and get end-to-end career guidance powered by Gemini AI.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **Resume Parsing** | PDF & DOCX support with section extraction |
| 🔍 **Skill Extraction** | NLP + semantic skill matching |
| 🎯 **Skill Gap Analysis** | FAISS-powered comparison vs. role requirements |
| 🗺️ **AI Roadmap** | Personalized learning roadmap via Gemini |
| 💼 **Opportunities** | Jobs, internships, hackathons, scholarships, competitions |
| 📚 **Course Recommendations** | Coursera, Udemy, edX, YouTube per missing skill |
| 🎤 **Interview Prep** | AI Q&A generation + real-time answer evaluation |
| 📊 **Score Dashboard** | ATS, Skill Match, Interview Readiness, Employability scores |
| 🤖 **AI Chat Assistant** | Conversational career advisor |
| 📋 **History & Reports** | Session history + PDF export |

---

## 🛠️ Tech Stack

- **UI**: Streamlit + Plotly
- **LLM**: Google Gemini 1.5 Flash
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Search**: FAISS
- **Resume Parsing**: pdfplumber + python-docx
- **Orchestration**: LangChain
- **Storage**: SQLite
- **PDF Export**: ReportLab

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd "career copilot"
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure API Key

Option A — Sidebar (recommended for demo):
- Launch the app and enter your Gemini API key in the sidebar

Option B — Environment file:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

Get a free Gemini API key at: https://aistudio.google.com/



---

## 📁 Project Structure

```
career copilot/
├── app.py                     # Main Streamlit application
├── config.py                  # Central configuration
├── requirements.txt
├── .env.example
├── modules/
│   ├── resume_parser.py       # PDF/DOCX extraction
│   ├── skill_extractor.py     # NLP skill extraction
│   ├── gap_analyzer.py        # Skill gap analysis (FAISS)
│   ├── roadmap_generator.py   # AI roadmap (Gemini)
│   ├── job_recommender.py     # Opportunity recommendations
│   ├── course_recommender.py  # Course recommendations
│   ├── interview_engine.py    # Q&A generation + evaluation
│   ├── scoring_engine.py      # ATS, Skill, Employability scores
│   ├── chat_assistant.py      # Conversational AI assistant
│   └── history_manager.py     # SQLite + PDF reports
├── data/
│   ├── skills_db.json         # 500+ skills taxonomy
│   ├── job_roles.json         # 20+ roles with requirements
│   ├── courses_db.json        # 200+ courses across platforms
│   └── opportunities.json     # Jobs, internships, hackathons, etc.
└── ui/
    ├── styles.css             # Dark glassmorphism theme
    └── components.py          # Reusable UI components
```





