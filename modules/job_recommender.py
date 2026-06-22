"""
Job & Opportunity Recommender — Rank jobs, internships, hackathons, scholarships.
"""
import json
import logging
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parent.parent / "data"

CATEGORIES = ["jobs", "internships", "hackathons", "scholarships", "competitions"]


@lru_cache(maxsize=1)
def _load_opportunities() -> dict:
    with open(DATA_DIR / "opportunities.json", "r", encoding="utf-8") as f:
        return json.load(f)


def recommend_opportunities(
    user_skills: list[str],
    target_role: str,
    categories: list[str] = None,
    max_per_category: int = 6,
) -> dict:
    """
    Return ranked opportunities for all categories.
    """
    opps = _load_opportunities()
    cats = categories or CATEGORIES
    results = {}

    for cat in cats:
        items = opps.get(cat, [])
        scored = _score_opportunities(items, user_skills, target_role)
        results[cat] = scored[:max_per_category]

    return results


def _score_opportunities(items: list, user_skills: list[str], target_role: str) -> list:
    """Score and rank opportunities by relevance to user profile."""
    user_lower = {s.lower() for s in user_skills}
    role_lower = target_role.lower()
    scored = []

    for item in items:
        score = 0.0
        item_skills = [s.lower() for s in item.get("skills", [])]

        # Skill overlap
        overlap = sum(1 for s in item_skills if s in user_lower or _partial_match(s, user_lower))
        if item_skills:
            score += (overlap / len(item_skills)) * 50

        # Role title relevance
        title = item.get("title", "").lower() + " " + item.get("theme", "").lower()
        if role_lower in title or any(w in title for w in role_lower.split()):
            score += 30

        # Bonus for "Any" skill tag
        if "any" in item_skills:
            score += 10

        scored.append({**item, "relevance_score": round(score, 1)})

    scored.sort(key=lambda x: -x["relevance_score"])
    return scored


def _partial_match(skill: str, user_skills: set) -> bool:
    """Check if any user skill is contained in or contains the job skill."""
    for us in user_skills:
        if skill in us or us in skill:
            return True
    return False


def get_semantic_job_matches(user_skills: list[str], target_role: str, top_k: int = 5) -> list:
    """Use sentence-transformers for deeper job-to-profile matching."""
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        from config import EMBEDDING_MODEL

        opps  = _load_opportunities()
        jobs  = opps.get("jobs", []) + opps.get("internships", [])
        texts = [
            f"{j.get('title', '')} {j.get('company', '')} {' '.join(j.get('skills', []))}"
            for j in jobs
        ]
        user_text = f"{target_role} {' '.join(user_skills)}"

        model     = SentenceTransformer(EMBEDDING_MODEL)
        job_embs  = model.encode(texts,     normalize_embeddings=True)
        user_emb  = model.encode([user_text], normalize_embeddings=True)[0]
        sims      = job_embs @ user_emb

        top_indices = sims.argsort()[::-1][:top_k]
        return [
            {**jobs[i], "semantic_score": round(float(sims[i]) * 100, 1)}
            for i in top_indices
        ]
    except Exception as e:
        logger.debug(f"Semantic job match error: {e}")
        return []
