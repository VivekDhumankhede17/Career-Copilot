"""
Skill Gap Analyzer — Compare user skills vs. target role requirements.
Uses FAISS + sentence-transformers for semantic similarity.
"""
import json
import logging
import numpy as np
from pathlib import Path
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parent.parent / "data"


@lru_cache(maxsize=1)
def _load_job_roles() -> dict:
    with open(DATA_DIR / "job_roles.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_available_roles() -> list[str]:
    db = _load_job_roles()
    return list(db.get("roles", {}).keys())


def analyze_gap(user_skills: list[str], target_role: str) -> dict:
    """
    Compare user skills against role requirements.
    Returns detailed gap analysis with similarity scores.
    """
    roles_db = _load_job_roles()
    roles    = roles_db.get("roles", {})

    # Find the best matching role
    role_data = _find_best_role(target_role, roles)
    if not role_data:
        return _empty_gap_result(target_role)

    role_name         = role_data["name"]
    required_skills   = role_data["data"].get("required_skills", [])
    preferred_skills  = role_data["data"].get("preferred_skills", [])
    all_role_skills   = list(set(required_skills + preferred_skills))

    # Normalize to lowercase sets for direct comparison
    user_lower = {s.lower(): s for s in user_skills}
    req_lower  = {s.lower(): s for s in required_skills}
    pref_lower = {s.lower(): s for s in preferred_skills}

    # Direct matches
    matched_required  = [s for sl, s in req_lower.items()  if sl in user_lower]
    matched_preferred = [s for sl, s in pref_lower.items() if sl in user_lower]
    missing_required  = [s for sl, s in req_lower.items()  if sl not in user_lower]
    missing_preferred = [s for sl, s in pref_lower.items() if sl not in user_lower]

    # Semantic partial matches for missing skills
    partial_matches = _semantic_partial_match(
        user_skills, missing_required + missing_preferred
    )

    # Reclassify semantically matched as partial
    partial_required  = [s for s in missing_required  if s in partial_matches]
    partial_preferred = [s for s in missing_preferred if s in partial_matches]
    gap_required  = [s for s in missing_required  if s not in partial_matches]
    gap_preferred = [s for s in missing_preferred if s not in partial_matches]

    # Scores
    req_score  = (len(matched_required)  + 0.5 * len(partial_required))  / max(len(required_skills), 1)
    pref_score = (len(matched_preferred) + 0.5 * len(partial_preferred)) / max(len(preferred_skills), 1)
    overall_match = round((req_score * 0.7 + pref_score * 0.3) * 100, 1)

    return {
        "target_role":         role_name,
        "role_info":           role_data["data"],
        "required_skills":     required_skills,
        "preferred_skills":    preferred_skills,
        "matched_required":    matched_required,
        "matched_preferred":   matched_preferred,
        "partial_required":    partial_required,
        "partial_preferred":   partial_preferred,
        "missing_required":    gap_required,
        "missing_preferred":   gap_preferred,
        "all_missing":         gap_required + gap_preferred,
        "skill_match_score":   overall_match,
        "gap_percentage":      round(100 - overall_match, 1),
        "priority_skills":     gap_required[:5],
        "similarity_scores":   partial_matches,
    }


def _find_best_role(target_role: str, roles: dict) -> Optional[dict]:
    """Find the closest matching role from the database."""
    # Exact match first
    for role_name, role_data in roles.items():
        if role_name.lower() == target_role.lower():
            return {"name": role_name, "data": role_data}

    # Partial string match
    target_lower = target_role.lower()
    for role_name, role_data in roles.items():
        if target_lower in role_name.lower() or role_name.lower() in target_lower:
            return {"name": role_name, "data": role_data}

    # Semantic match using sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        from config import EMBEDDING_MODEL

        model = SentenceTransformer(EMBEDDING_MODEL)
        role_names = list(roles.keys())
        embs  = model.encode(role_names + [target_role], normalize_embeddings=True)
        query = embs[-1]
        sims  = embs[:-1] @ query
        best_idx = int(np.argmax(sims))
        if sims[best_idx] > 0.5:
            best_name = role_names[best_idx]
            return {"name": best_name, "data": roles[best_name]}
    except Exception as e:
        logger.debug(f"Semantic role matching failed: {e}")

    # Fallback: return the first role
    if roles:
        first = list(roles.items())[0]
        return {"name": first[0], "data": first[1]}
    return None


def _semantic_partial_match(user_skills: list[str], missing_skills: list[str]) -> dict:
    """
    Return a dict of {skill: similarity_score} for skills that partially match
    user knowledge (score between 0.55 and 0.85).
    """
    if not user_skills or not missing_skills:
        return {}

    try:
        from sentence_transformers import SentenceTransformer
        from config import EMBEDDING_MODEL

        model = SentenceTransformer(EMBEDDING_MODEL)
        user_embs    = model.encode(user_skills,    normalize_embeddings=True)
        missing_embs = model.encode(missing_skills, normalize_embeddings=True)
        sims = user_embs @ missing_embs.T   # (n_user, n_missing)
        max_sims = sims.max(axis=0)

        PARTIAL_LOW = 0.55
        PARTIAL_HIGH = 0.84
        return {
            missing_skills[i]: float(max_sims[i])
            for i in range(len(missing_skills))
            if PARTIAL_LOW <= max_sims[i] < PARTIAL_HIGH
        }
    except Exception as e:
        logger.debug(f"Partial match error: {e}")
        return {}


def _empty_gap_result(target_role: str) -> dict:
    return {
        "target_role":       target_role,
        "role_info":         {},
        "required_skills":   [],
        "preferred_skills":  [],
        "matched_required":  [],
        "matched_preferred": [],
        "partial_required":  [],
        "partial_preferred": [],
        "missing_required":  [],
        "missing_preferred": [],
        "all_missing":       [],
        "skill_match_score": 0.0,
        "gap_percentage":    100.0,
        "priority_skills":   [],
        "similarity_scores": {},
    }


def build_faiss_skill_index(role_name: str) -> Optional[object]:
    """Build a FAISS index for a specific role's required skills."""
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
        from config import EMBEDDING_MODEL

        roles = _load_job_roles().get("roles", {})
        if role_name not in roles:
            return None

        role_skills = roles[role_name]["required_skills"] + roles[role_name]["preferred_skills"]
        model = SentenceTransformer(EMBEDDING_MODEL)
        embeddings = model.encode(role_skills, normalize_embeddings=True)
        embeddings = embeddings.astype(np.float32)

        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        return index, role_skills
    except Exception as e:
        logger.debug(f"FAISS index build error: {e}")
        return None
