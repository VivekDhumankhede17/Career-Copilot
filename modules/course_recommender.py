"""
Course Recommender — Map missing skills to curated courses.
"""
import json
import logging
from pathlib import Path
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parent.parent / "data"

PLATFORM_ICONS = {
    "Coursera": "🎓",
    "Udemy":    "🎯",
    "edX":      "🏛️",
    "YouTube":  "▶️",
}


@lru_cache(maxsize=1)
def _load_courses_db() -> dict:
    with open(DATA_DIR / "courses_db.json", "r", encoding="utf-8") as f:
        return json.load(f)


def recommend_courses(
    missing_skills: list[str],
    user_preferences: Optional[dict] = None,
    max_per_skill: int = 3,
) -> dict:
    """
    Return a dict of {skill: [course_list]} for missing skills.
    """
    courses_db = _load_courses_db().get("courses", {})
    pref       = user_preferences or {}
    free_only  = pref.get("free_only", False)
    platforms  = pref.get("platforms", ["Coursera", "Udemy", "edX", "YouTube"])

    recommendations = {}

    for skill in missing_skills:
        matches = _find_courses_for_skill(skill, courses_db)

        # Filter by preferences
        if free_only:
            matches = [c for c in matches if c.get("free", False)]
        if platforms:
            matches = [c for c in matches if c.get("platform") in platforms]

        # Sort by rating desc, free first
        matches.sort(key=lambda c: (not c.get("free", False), -c.get("rating", 0)))
        recommendations[skill] = matches[:max_per_skill]

    # Fill gaps with semantic matching
    unfound = [s for s in missing_skills if not recommendations.get(s)]
    if unfound:
        semantic_recs = _semantic_course_matching(unfound, courses_db)
        for skill, courses in semantic_recs.items():
            if not recommendations.get(skill):
                recommendations[skill] = courses[:max_per_skill]

    return recommendations


def _find_courses_for_skill(skill: str, courses_db: dict) -> list:
    """Direct key lookup with fuzzy fallback."""
    skill_lower = skill.lower()

    # Exact match
    for key, courses in courses_db.items():
        if key.lower() == skill_lower:
            return courses

    # Partial match
    matches = []
    for key, courses in courses_db.items():
        if skill_lower in key.lower() or key.lower() in skill_lower:
            matches.extend(courses)

    return matches


def _semantic_course_matching(skills: list[str], courses_db: dict) -> dict:
    """Use sentence-transformers to match skills to closest course category."""
    if not skills:
        return {}

    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        from config import EMBEDDING_MODEL

        model      = SentenceTransformer(EMBEDDING_MODEL)
        categories = list(courses_db.keys())
        cat_embs   = model.encode(categories, normalize_embeddings=True)
        skill_embs = model.encode(skills, normalize_embeddings=True)
        sims       = skill_embs @ cat_embs.T  # (n_skills, n_cats)

        results = {}
        for i, skill in enumerate(skills):
            best_idx = int(sims[i].argmax())
            if sims[i][best_idx] > 0.45:
                results[skill] = courses_db[categories[best_idx]]
        return results
    except Exception as e:
        logger.debug(f"Semantic course matching error: {e}")
        return {}


def get_all_courses_flat(recommendations: dict) -> list:
    """Flatten recommendations into a single sorted list."""
    all_courses = []
    for skill, courses in recommendations.items():
        for course in courses:
            c = dict(course)
            c["for_skill"] = skill
            all_courses.append(c)
    all_courses.sort(key=lambda c: -c.get("rating", 0))
    return all_courses


def format_course_card(course: dict, skill: str = "") -> str:
    """Format a single course as a markdown card."""
    platform = course.get("platform", "Unknown")
    icon     = PLATFORM_ICONS.get(platform, "📚")
    free_tag = "🆓 Free" if course.get("free") else "💰 Paid"
    rating   = "⭐" * round(course.get("rating", 0)) + f" {course.get('rating', 'N/A')}"

    return (
        f"{icon} **[{course['title']}]({course['url']})**  \n"
        f"Platform: `{platform}` | {free_tag} | {rating}  \n"
        f"Level: {course.get('level', 'All')} | Duration: {course.get('duration', 'N/A')}"
    )
