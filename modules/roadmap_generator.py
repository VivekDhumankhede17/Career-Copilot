"""
Roadmap Generator — AI-powered learning roadmap via LangChain + Gemini.
"""
import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


ROADMAP_PROMPT_TEMPLATE = """
You are an expert career coach and technical mentor. Generate a detailed, personalized learning roadmap.

## User Profile:
- **Name**: {name}
- **Current Skills**: {current_skills}
- **Target Role**: {target_role}
- **Experience Level**: {experience_level}
- **Missing Required Skills**: {missing_skills}
- **Priority Skills to Learn**: {priority_skills}
- **Timeline Preference**: {timeline}

## Instructions:
Create a structured learning roadmap with {num_phases} phases. For each phase:
1. Give it a descriptive title
2. Specify duration (e.g., "Weeks 1-4")
3. List 3-5 specific learning goals
4. Recommend 2-3 specific actions (courses, projects, practice)
5. Define success milestones

Format your response as valid JSON with this exact structure:
{{
  "overview": "Brief 2-sentence overview of the roadmap strategy",
  "total_duration": "X months",
  "phases": [
    {{
      "phase_number": 1,
      "title": "Phase title",
      "duration": "Weeks 1-4",
      "focus": "Core area of focus",
      "goals": ["goal 1", "goal 2", "goal 3"],
      "actions": ["action 1", "action 2", "action 3"],
      "milestones": ["milestone 1", "milestone 2"],
      "skills_covered": ["skill1", "skill2"]
    }}
  ],
  "final_advice": "2-3 sentences of motivational closing advice"
}}

Be specific, actionable, and realistic. Focus on the most impactful learning path.
"""


def generate_roadmap(profile: dict, gap_analysis: dict, timeline: str = "6 months", api_key: str = "") -> dict:
    """
    Generate a personalized learning roadmap using Gemini AI.
    Falls back to a rule-based roadmap if AI is unavailable.
    """
    missing_skills   = gap_analysis.get("missing_required", []) + gap_analysis.get("missing_preferred", [])
    priority_skills  = gap_analysis.get("priority_skills", missing_skills[:5])
    current_skills   = profile.get("skills", [])
    experience_years = profile.get("experience_years", 0)

    if experience_years == 0:
        experience_level = "Entry Level (0-1 years)"
    elif experience_years <= 3:
        experience_level = "Junior (1-3 years)"
    elif experience_years <= 6:
        experience_level = "Mid-Level (3-6 years)"
    else:
        experience_level = "Senior (6+ years)"

    # Determine number of phases
    months_map = {"3 months": 3, "6 months": 4, "12 months": 5, "1 year": 5, "2 years": 6}
    num_phases = months_map.get(timeline, 4)

    prompt_vars = {
        "name":             profile.get("name", "User"),
        "current_skills":   ", ".join(current_skills[:20]) or "General programming knowledge",
        "target_role":      gap_analysis.get("target_role", "Software Engineer"),
        "experience_level": experience_level,
        "missing_skills":   ", ".join(missing_skills[:15]) or "None identified",
        "priority_skills":  ", ".join(priority_skills[:8])  or "Core programming",
        "timeline":         timeline,
        "num_phases":       num_phases,
    }

    roadmap_json = _call_gemini_roadmap(prompt_vars, api_key)

    if not roadmap_json:
        roadmap_json = _generate_fallback_roadmap(profile, gap_analysis, timeline, num_phases)

    return roadmap_json


def _call_gemini_roadmap(prompt_vars: dict, api_key: str) -> Optional[dict]:
    """Call Gemini API to generate roadmap."""
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = ROADMAP_PROMPT_TEMPLATE.format(**prompt_vars)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=3000,
            )
        )

        text = response.text
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        logger.error(f"Gemini roadmap error: {e}")
        return None


def _generate_fallback_roadmap(profile: dict, gap_analysis: dict, timeline: str, num_phases: int) -> dict:
    """
    Rule-based fallback roadmap when AI is not available.
    """
    missing   = gap_analysis.get("missing_required", [])
    preferred = gap_analysis.get("missing_preferred", [])
    role      = gap_analysis.get("target_role", "your target role")
    all_gap   = missing + preferred

    # Distribute skills across phases
    chunk_size = max(1, len(all_gap) // num_phases) if all_gap else 2
    phases     = []

    phase_templates = [
        {"title": "Foundation & Core Skills",    "focus": "Master fundamental prerequisites"},
        {"title": "Core Technical Development",  "focus": "Build role-specific technical skills"},
        {"title": "Advanced Specialization",     "focus": "Deep-dive into advanced concepts"},
        {"title": "Projects & Portfolio",        "focus": "Apply skills through real projects"},
        {"title": "Interview Preparation",       "focus": "Prepare for technical interviews"},
        {"title": "Job Search & Networking",     "focus": "Land your target role"},
    ]

    weeks_per_phase = {3: 4, 4: 6, 5: 5, 6: 4}
    wpf = weeks_per_phase.get(num_phases, 5)

    for i in range(num_phases):
        tmpl = phase_templates[i % len(phase_templates)]
        skill_chunk = all_gap[i * chunk_size:(i + 1) * chunk_size]
        start_week  = i * wpf + 1
        end_week    = (i + 1) * wpf

        phases.append({
            "phase_number":   i + 1,
            "title":          tmpl["title"],
            "duration":       f"Weeks {start_week}–{end_week}",
            "focus":          tmpl["focus"],
            "goals":          [
                f"Master {'and '.join(skill_chunk[:2]) if skill_chunk else 'core concepts'}",
                f"Complete 1 hands-on project using new skills",
                "Review and practice interview questions for this phase",
            ],
            "actions":        [
                f"Enroll in online courses for {', '.join(skill_chunk[:2]) if skill_chunk else 'relevant topics'}",
                "Build a mini project and push to GitHub",
                "Solve 10 LeetCode problems related to current phase",
            ],
            "milestones":     [
                f"Completed learning modules for phase {i+1}",
                "Project added to portfolio",
            ],
            "skills_covered": skill_chunk if skill_chunk else ["General skills"],
        })

    return {
        "overview":        f"This roadmap guides you step-by-step toward becoming a {role}. Focus on closing skill gaps systematically while building a strong portfolio.",
        "total_duration":  timeline,
        "phases":          phases,
        "final_advice":    f"Consistency is key. Dedicate 2-3 hours daily, track your progress weekly, and network with professionals in the {role} space. You've got this! 🚀",
    }


def roadmap_to_markdown(roadmap: dict) -> str:
    """Convert roadmap dict to readable Markdown."""
    lines = []
    lines.append(f"## 🗺️ Your Learning Roadmap")
    lines.append(f"\n**Overview**: {roadmap.get('overview', '')}")
    lines.append(f"\n**Total Duration**: {roadmap.get('total_duration', 'N/A')}\n")

    for phase in roadmap.get("phases", []):
        lines.append(f"---\n### Phase {phase['phase_number']}: {phase['title']}")
        lines.append(f"📅 **{phase['duration']}** | 🎯 {phase['focus']}\n")
        lines.append("**Goals:**")
        for g in phase.get("goals", []):
            lines.append(f"- ✅ {g}")
        lines.append("\n**Actions:**")
        for a in phase.get("actions", []):
            lines.append(f"- 🔧 {a}")
        lines.append("\n**Success Milestones:**")
        for m in phase.get("milestones", []):
            lines.append(f"- 🏆 {m}")
        if phase.get("skills_covered"):
            lines.append(f"\n**Skills Covered**: {', '.join(phase['skills_covered'])}")
        lines.append("")

    if roadmap.get("final_advice"):
        lines.append(f"---\n💡 **Final Advice**: {roadmap['final_advice']}")

    return "\n".join(lines)
