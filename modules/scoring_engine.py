"""
Scoring Engine — Calculate ATS, Skill Match, Interview Readiness, and Employability scores.
"""
import re
import math
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ─── ATS Score ────────────────────────────────────────────────────────────────

ATS_SECTION_WEIGHTS = {
    "contact":        10,
    "summary":        10,
    "skills":         20,
    "experience":     25,
    "education":      20,
    "projects":       10,
    "certifications":  5,
}

ATS_FORMAT_SIGNALS = {
    "has_email":       5,
    "has_phone":       5,
    "has_linkedin":    3,
    "has_github":      2,
    "good_length":     5,   # 300-1000 words
    "no_tables":       0,   # hard to detect, skip
}


def calculate_ats_score(parsed_resume: dict, profile: dict) -> dict:
    """
    Calculate ATS (Applicant Tracking System) compatibility score.
    """
    section_score = 0
    section_details = {}

    for section, weight in ATS_SECTION_WEIGHTS.items():
        content = parsed_resume.get(section, "")
        words = len(content.split()) if content else 0

        # Score based on word count
        if words == 0:
            s = 0
        elif words < 10:
            s = 0.3
        elif words < 30:
            s = 0.6
        elif words < 60:
            s = 0.8
        else:
            s = 1.0

        section_score += s * weight
        section_details[section] = {
            "score": round(s * weight, 1),
            "max":   weight,
            "words": words,
            "present": words > 5,
        }

    # Format signals
    contact = profile.get("contact_info", {}) or parsed_resume.get("contact_info", {})
    fmt_score = 0
    if contact.get("email"):    fmt_score += 5
    if contact.get("phone"):    fmt_score += 5
    if contact.get("linkedin"): fmt_score += 3
    if contact.get("github"):   fmt_score += 2

    word_count = parsed_resume.get("word_count", 0)
    if 300 <= word_count <= 1200:
        fmt_score += 5
    elif word_count > 0:
        fmt_score += 2

    # Keyword density bonus
    skill_words = len(parsed_resume.get("skills", "").split())
    kw_bonus = min(10, skill_words // 3)

    raw_score = section_score + fmt_score + kw_bonus
    final_score = min(100, round(raw_score))

    return {
        "ats_score":       final_score,
        "section_details": section_details,
        "format_score":    fmt_score,
        "keyword_bonus":   kw_bonus,
        "word_count":      word_count,
        "missing_sections": [
            s for s, d in section_details.items() if not d["present"]
        ],
    }


# ─── Skill Match Score ────────────────────────────────────────────────────────

def calculate_skill_match_score(gap_analysis: dict) -> dict:
    """
    Calculate skill match score from gap analysis output.
    """
    score = gap_analysis.get("skill_match_score", 0.0)

    # Determine tier
    if score >= 85:
        tier = "Excellent Match"
        color = "#00e676"
    elif score >= 70:
        tier = "Strong Match"
        color = "#69f0ae"
    elif score >= 50:
        tier = "Moderate Match"
        color = "#ffab40"
    elif score >= 30:
        tier = "Weak Match"
        color = "#ff6b6b"
    else:
        tier = "Poor Match"
        color = "#ef5350"

    matched = len(gap_analysis.get("matched_required", [])) + len(gap_analysis.get("matched_preferred", []))
    total   = len(gap_analysis.get("required_skills", [])) + len(gap_analysis.get("preferred_skills", []))

    return {
        "skill_match_score": round(score, 1),
        "tier":              tier,
        "color":             color,
        "matched_count":     matched,
        "total_required":    total,
        "gap_count":         len(gap_analysis.get("all_missing", [])),
    }


# ─── Interview Readiness Score ────────────────────────────────────────────────

def calculate_interview_readiness_score(interview_results: Optional[list]) -> dict:
    """
    Calculate interview readiness from Q&A session results.
    Each result: {"question": str, "answer": str, "score": int (1-10), "feedback": str}
    """
    if not interview_results:
        return {
            "interview_readiness_score": 0,
            "tier": "Not Assessed",
            "color": "#94a3b8",
            "questions_attempted": 0,
            "avg_question_score": 0,
        }

    attempted = [r for r in interview_results if r.get("answer", "").strip()]
    if not attempted:
        return {
            "interview_readiness_score": 0,
            "tier": "Not Attempted",
            "color": "#94a3b8",
            "questions_attempted": 0,
            "avg_question_score": 0,
        }

    scores = [r.get("score", 5) for r in attempted]
    avg    = sum(scores) / len(scores)
    pct    = round((avg / 10) * 100, 1)
    coverage_bonus = min(20, len(attempted) * 4)
    final  = min(100, round(pct * 0.8 + coverage_bonus))

    if final >= 80:
        tier, color = "Interview Ready",   "#00e676"
    elif final >= 60:
        tier, color = "Mostly Prepared",   "#69f0ae"
    elif final >= 40:
        tier, color = "Needs Practice",    "#ffab40"
    else:
        tier, color = "Significant Gaps",  "#ff6b6b"

    return {
        "interview_readiness_score": final,
        "tier":                tier,
        "color":               color,
        "questions_attempted": len(attempted),
        "avg_question_score":  round(avg, 1),
        "score_breakdown":     scores,
    }


# ─── Experience Score ─────────────────────────────────────────────────────────

def calculate_experience_score(profile: dict, gap_analysis: dict) -> dict:
    """
    Score experience based on years, projects, and certifications.
    """
    years = profile.get("experience_years", 0)
    projects = profile.get("projects", [])
    certs    = profile.get("certifications", [])

    # Target role expected years
    role_info  = gap_analysis.get("role_info", {})
    target_exp = role_info.get("experience_years", {}).get("entry", 0)

    year_score = min(100, (years / max(target_exp + 2, 1)) * 100) if target_exp >= 0 else min(100, years * 15)
    proj_score = min(100, len(projects) * 20)
    cert_score = min(100, len(certs)    * 25)

    final = round(year_score * 0.5 + proj_score * 0.3 + cert_score * 0.2)

    return {
        "experience_score":  final,
        "years":             years,
        "project_count":     len(projects),
        "certification_count": len(certs),
    }


# ─── Overall Employability Score ──────────────────────────────────────────────

def calculate_employability_score(
    ats_result:       dict,
    skill_result:     dict,
    interview_result: dict,
    experience_result: dict,
) -> dict:
    """
    Weighted composite score — the headline number shown to users.
    """
    from config import EMPLOYABILITY_WEIGHTS

    ats   = ats_result.get("ats_score", 0)
    skill = skill_result.get("skill_match_score", 0)
    intv  = interview_result.get("interview_readiness_score", 0)
    exp   = experience_result.get("experience_score", 0)

    w = EMPLOYABILITY_WEIGHTS
    score = (
        ats   * w["ats_score"]                  +
        skill * w["skill_match_score"]           +
        intv  * w["interview_readiness_score"]   +
        exp   * w["experience_score"]
    )
    final = round(min(100, score))

    if final >= 85:
        tier, color, emoji = "Highly Employable",   "#00e676", "🚀"
    elif final >= 70:
        tier, color, emoji = "Strong Candidate",    "#69f0ae", "⭐"
    elif final >= 55:
        tier, color, emoji = "Competitive",         "#ffab40", "📈"
    elif final >= 40:
        tier, color, emoji = "Needs Improvement",   "#ff9800", "🎯"
    else:
        tier, color, emoji = "Early Stage",         "#ff6b6b", "🌱"

    return {
        "employability_score": final,
        "tier":    tier,
        "color":   color,
        "emoji":   emoji,
        "breakdown": {
            "ATS Score":               round(ats),
            "Skill Match":             round(skill),
            "Interview Readiness":     round(intv),
            "Experience & Projects":   round(exp),
        },
        "weights": w,
    }


def get_all_scores(parsed_resume, profile, gap_analysis, interview_results=None):
    """Convenience function — compute all scores at once."""
    ats_result        = calculate_ats_score(parsed_resume, profile)
    skill_result      = calculate_skill_match_score(gap_analysis)
    interview_result  = calculate_interview_readiness_score(interview_results)
    experience_result = calculate_experience_score(profile, gap_analysis)
    emp_result        = calculate_employability_score(
        ats_result, skill_result, interview_result, experience_result
    )
    return {
        "ats":           ats_result,
        "skill":         skill_result,
        "interview":     interview_result,
        "experience":    experience_result,
        "employability": emp_result,
    }
