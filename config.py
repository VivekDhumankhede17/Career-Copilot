"""
Central configuration for Career Copilot.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = BASE_DIR / "career_copilot.db"
CHROMA_DIR = BASE_DIR / ".chroma_db"

# ─── API Keys ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ─── Model Config ─────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-1.5-flash"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ─── Scoring Weights ──────────────────────────────────────────────────────────
EMPLOYABILITY_WEIGHTS = {
    "ats_score": 0.25,
    "skill_match_score": 0.40,
    "interview_readiness_score": 0.20,
    "experience_score": 0.15,
}

# ─── ATS Config ───────────────────────────────────────────────────────────────
ATS_SECTION_WEIGHTS = {
    "contact": 10,
    "summary": 10,
    "skills": 20,
    "experience": 25,
    "education": 20,
    "projects": 10,
    "certifications": 5,
}

# ─── UI Config ────────────────────────────────────────────────────────────────
APP_TITLE = "Career Copilot AI"
APP_ICON = "🚀"
APP_VERSION = "1.0.0"

MAX_COURSES_PER_SKILL = 3
MAX_JOBS_PER_CATEGORY = 6
MAX_INTERVIEW_QUESTIONS = 5

# ─── Color Palette ────────────────────────────────────────────────────────────
COLORS = {
    "primary": "#00d2ff",
    "secondary": "#7b2ff7",
    "accent": "#ff6b6b",
    "success": "#00e676",
    "warning": "#ffab40",
    "dark_bg": "#0a0f1e",
    "card_bg": "rgba(255,255,255,0.05)",
    "text": "#e2e8f0",
    "muted": "#94a3b8",
}

CHART_COLORS = [
    "#00d2ff", "#7b2ff7", "#ff6b6b", "#00e676",
    "#ffab40", "#40c4ff", "#ea80fc", "#69f0ae",
]
