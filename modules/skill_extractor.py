"""
Skill Extractor — Extract and classify skills from resume text.
Uses regex pattern matching + semantic similarity with sentence-transformers.
"""
import re
import json
import logging
from pathlib import Path
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parent.parent / "data"


@lru_cache(maxsize=1)
def _load_skills_db() -> dict:
    with open(DATA_DIR / "skills_db.json", "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _get_all_skills() -> list[str]:
    db = _load_skills_db()
    all_skills = []
    for category in db.get("technical_skills", {}).values():
        all_skills.extend(category)
    all_skills.extend(db.get("soft_skills", []))
    return list(set(all_skills))


def extract_skills(parsed_resume: dict) -> dict:
    """
    Main entry — extract all skill categories from parsed resume.
    Returns structured profile dict.
    """
    full_text = parsed_resume.get("raw_text", "")
    skills_text = parsed_resume.get("skills", "") + "\n" + parsed_resume.get("experience", "")

    extracted_skills   = _extract_skills_from_text(skills_text + "\n" + full_text)
    education_info     = _parse_education(parsed_resume.get("education", ""))
    experience_info    = _parse_experience(parsed_resume.get("experience", ""))
    projects_info      = _parse_projects(parsed_resume.get("projects", ""))
    certifications     = _parse_certifications(parsed_resume.get("certifications", ""))
    contact            = parsed_resume.get("contact_info", {})

    return {
        "name":             contact.get("name", ""),
        "email":            contact.get("email", ""),
        "phone":            contact.get("phone", ""),
        "linkedin":         contact.get("linkedin", ""),
        "github":           contact.get("github", ""),
        "skills":           extracted_skills,
        "education":        education_info,
        "experience":       experience_info,
        "experience_years": experience_info.get("total_years", 0),
        "projects":         projects_info,
        "certifications":   certifications,
        "raw_skills_text":  skills_text,
    }


def _extract_skills_from_text(text: str) -> list[str]:
    """Match known skills from the skills database using case-insensitive regex."""
    all_skills = _get_all_skills()
    found = set()
    text_lower = text.lower()

    for skill in all_skills:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill)

    # Also try semantic extraction if sentence-transformers is available
    semantic_skills = _semantic_skill_extraction(text, found)
    found.update(semantic_skills)

    return sorted(list(found))


def _semantic_skill_extraction(text: str, already_found: set) -> set:
    """Use sentence-transformers to find additional skills semantically."""
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = _get_embedding_model()
        all_skills = _get_all_skills()
        remaining = [s for s in all_skills if s not in already_found]

        if not remaining:
            return set()

        # Encode skills and text chunks
        text_sentences = [s.strip() for s in text.split('\n') if len(s.strip()) > 5][:50]
        if not text_sentences:
            return set()

        skill_embeddings = model.encode(remaining, convert_to_numpy=True, show_progress_bar=False)
        text_embeddings  = model.encode(text_sentences, convert_to_numpy=True, show_progress_bar=False)

        # Cosine similarity
        text_norm  = text_embeddings  / (np.linalg.norm(text_embeddings,  axis=1, keepdims=True) + 1e-9)
        skill_norm = skill_embeddings / (np.linalg.norm(skill_embeddings, axis=1, keepdims=True) + 1e-9)
        scores     = text_norm @ skill_norm.T          # (n_sentences, n_skills)
        max_scores = scores.max(axis=0)               # (n_skills,)

        THRESHOLD = 0.82
        return {remaining[i] for i, s in enumerate(max_scores) if s >= THRESHOLD}
    except Exception as e:
        logger.debug(f"Semantic extraction skipped: {e}")
        return set()


@lru_cache(maxsize=1)
def _get_embedding_model():
    from sentence_transformers import SentenceTransformer
    from config import EMBEDDING_MODEL
    return SentenceTransformer(EMBEDDING_MODEL)


def _parse_education(text: str) -> dict:
    """Extract education details."""
    degree_patterns = [
        r'\b(B\.?Tech|B\.?E\.?|B\.?Sc|B\.?Com|BCA|MCA|M\.?Tech|M\.?Sc|MBA|Ph\.?D|Bachelor|Master|Doctorate)\b',
        r'\b(Computer Science|Information Technology|Electronics|Mechanical|Civil|Electrical)\b',
    ]
    degrees, fields = [], []
    for p in degree_patterns[:1]:
        degrees.extend(re.findall(p, text, re.IGNORECASE))
    for p in degree_patterns[1:]:
        fields.extend(re.findall(p, text, re.IGNORECASE))

    years = re.findall(r'\b(19|20)\d{2}\b', text)
    cgpa  = re.findall(r'(?:CGPA|GPA|Percentage)[:\s]*([0-9.]+)', text, re.IGNORECASE)

    return {
        "degrees": list(set(degrees)),
        "fields":  list(set(fields)),
        "years":   sorted(set(years)),
        "cgpa":    cgpa[0] if cgpa else "",
        "raw":     text[:500],
    }


def _parse_experience(text: str) -> dict:
    """Extract work experience info."""
    years_pattern = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience', text, re.IGNORECASE)
    year_ranges   = re.findall(r'\b(20\d{2})\s*[-–]\s*(20\d{2}|Present|Current)\b', text, re.IGNORECASE)

    total_years = 0
    if years_pattern:
        total_years = max(int(y) for y in years_pattern)
    elif year_ranges:
        import datetime
        current_year = datetime.datetime.now().year
        for start, end in year_ranges:
            end_y = current_year if end.lower() in ('present', 'current') else int(end)
            total_years += max(0, end_y - int(start))

    companies = re.findall(r'(?:at|@|with)\s+([A-Z][A-Za-z\s&]+(?:Inc|Ltd|Corp|Technologies|Solutions|Systems)?)', text)

    return {
        "total_years": min(total_years, 40),
        "year_ranges": year_ranges,
        "companies":   companies[:5],
        "raw":         text[:800],
    }


def _parse_projects(text: str) -> list[dict]:
    """Extract project entries."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    projects = []
    current = {}

    for line in lines:
        if len(line) < 80 and not line.startswith(('•', '-', '*', '–')):
            if current:
                projects.append(current)
            current = {"title": line, "description": ""}
        elif current:
            current["description"] += " " + line

    if current:
        projects.append(current)

    return projects[:10]


def _parse_certifications(text: str) -> list[str]:
    """Extract certification names."""
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 5]
    return lines[:15]


def get_skill_categories(skills: list[str]) -> dict:
    """Group extracted skills by category."""
    db = _load_skills_db()
    categories = {}
    for cat_name, cat_skills in db.get("technical_skills", {}).items():
        cat_lower = {s.lower(): s for s in cat_skills}
        matched = [s for s in skills if s.lower() in cat_lower]
        if matched:
            categories[cat_name.replace("_", " ").title()] = matched
    soft_matched = [s for s in skills if s in db.get("soft_skills", [])]
    if soft_matched:
        categories["Soft Skills"] = soft_matched
    return categories
