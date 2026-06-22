"""
Interview Engine — Generate technical/HR questions and evaluate answers using Gemini.
"""
import json
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

QUESTION_GEN_PROMPT = """
You are an expert technical interviewer at a top tech company. Generate interview questions for:

**Role**: {role}
**Candidate Skills**: {skills}
**Experience Level**: {experience_level}

Generate exactly {n_technical} technical questions and {n_hr} HR/behavioral questions.

Return ONLY valid JSON in this exact format:
{{
  "technical_questions": [
    {{
      "id": 1,
      "question": "Question text here",
      "difficulty": "Easy|Medium|Hard",
      "topic": "Topic area",
      "expected_keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ],
  "hr_questions": [
    {{
      "id": 1,
      "question": "Question text here",
      "category": "Leadership|Teamwork|Problem-Solving|Communication|Work-Ethic",
      "focus": "What this question assesses"
    }}
  ]
}}
"""

EVALUATION_PROMPT = """
You are a senior interviewer evaluating a candidate's answer.

**Question**: {question}
**Question Type**: {q_type}
**Role**: {role}
**Expected Keywords/Concepts**: {keywords}

**Candidate's Answer**: {answer}

Evaluate the answer and respond ONLY with valid JSON:
{{
  "score": <integer 1-10>,
  "grade": "<A+|A|B|C|D|F>",
  "strengths": ["strength 1", "strength 2"],
  "improvements": ["improvement 1", "improvement 2"],
  "ideal_answer_hints": "2-3 sentences describing what a great answer would include",
  "feedback": "Concise 2-3 sentence overall feedback"
}}
"""


def generate_questions(
    target_role: str,
    user_skills: list[str],
    experience_years: int = 0,
    n_technical: int = 5,
    n_hr: int = 5,
    api_key: str = "",
) -> dict:
    """
    Generate interview questions using Gemini or fallback to curated questions.
    """
    if experience_years == 0:
        exp_level = "Entry Level"
    elif experience_years <= 3:
        exp_level = "Junior"
    elif experience_years <= 6:
        exp_level = "Mid-Level"
    else:
        exp_level = "Senior"

    if api_key:
        questions = _call_gemini_questions(
            target_role, user_skills, exp_level, n_technical, n_hr, api_key
        )
        if questions:
            return questions

    return _get_fallback_questions(target_role, user_skills, n_technical, n_hr)


def evaluate_answer(
    question: str,
    answer: str,
    q_type: str,
    target_role: str,
    expected_keywords: list[str] = None,
    api_key: str = "",
) -> dict:
    """
    Evaluate a candidate's answer using Gemini or rule-based scoring.
    """
    if api_key and answer.strip():
        result = _call_gemini_evaluate(question, answer, q_type, target_role, expected_keywords or [], api_key)
        if result:
            return result

    return _rule_based_evaluate(question, answer, expected_keywords or [])


def _call_gemini_questions(role, skills, exp_level, n_tech, n_hr, api_key) -> Optional[dict]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model  = genai.GenerativeModel("gemini-1.5-flash")
        prompt = QUESTION_GEN_PROMPT.format(
            role=role,
            skills=", ".join(skills[:15]),
            experience_level=exp_level,
            n_technical=n_tech,
            n_hr=n_hr,
        )
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.8, max_output_tokens=2000)
        )
        text = response.text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        logger.error(f"Gemini question gen error: {e}")
    return None


def _call_gemini_evaluate(question, answer, q_type, role, keywords, api_key) -> Optional[dict]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model  = genai.GenerativeModel("gemini-1.5-flash")
        prompt = EVALUATION_PROMPT.format(
            question=question,
            q_type=q_type,
            role=role,
            keywords=", ".join(keywords),
            answer=answer,
        )
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=800)
        )
        text = response.text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        logger.error(f"Gemini evaluation error: {e}")
    return None


def _rule_based_evaluate(question: str, answer: str, keywords: list[str]) -> dict:
    """Simple keyword + length based scoring."""
    if not answer.strip():
        return {
            "score": 0, "grade": "F",
            "strengths": [],
            "improvements": ["Please provide an answer"],
            "ideal_answer_hints": "A detailed, structured answer with examples would be ideal.",
            "feedback": "No answer provided."
        }

    words       = answer.lower().split()
    kw_matched  = [kw for kw in keywords if kw.lower() in " ".join(words)]
    kw_ratio    = len(kw_matched) / max(len(keywords), 1)

    length_score = min(1.0, len(words) / 80)  # 80 words = full length score
    kw_score     = kw_ratio
    score        = round((length_score * 4 + kw_score * 6))
    score        = max(1, min(10, score))

    grade_map = {10: "A+", 9: "A+", 8: "A", 7: "B", 6: "B", 5: "C", 4: "C", 3: "D", 2: "D", 1: "F"}

    return {
        "score": score,
        "grade": grade_map.get(score, "C"),
        "strengths":   ["Attempted the question", "Some relevant content present"] if score > 3 else [],
        "improvements": (
            ["Include more technical detail", f"Mention: {', '.join(keywords[:3])}"]
            if kw_matched < keywords else []
        ),
        "ideal_answer_hints": f"A strong answer covers: {', '.join(keywords[:5])}." if keywords else "Provide clear, structured explanation with examples.",
        "feedback": f"Score {score}/10. {'Good attempt!' if score >= 6 else 'Consider expanding your answer with more depth.'}"
    }


def _get_fallback_questions(role: str, skills: list[str], n_tech: int, n_hr: int) -> dict:
    """Curated fallback questions by role category."""
    tech_bank = {
        "default": [
            {"id": 1, "question": "Explain the difference between a stack and a queue.", "difficulty": "Easy", "topic": "Data Structures", "expected_keywords": ["LIFO", "FIFO", "push", "pop", "enqueue", "dequeue"]},
            {"id": 2, "question": "What is the time complexity of binary search and how does it work?", "difficulty": "Easy", "topic": "Algorithms", "expected_keywords": ["O(log n)", "sorted", "mid", "divide"]},
            {"id": 3, "question": "Explain SOLID principles in object-oriented programming.", "difficulty": "Medium", "topic": "OOP", "expected_keywords": ["Single Responsibility", "Open/Closed", "Liskov", "Interface", "Dependency"]},
            {"id": 4, "question": "What is a REST API and what are its key constraints?", "difficulty": "Medium", "topic": "Web/APIs", "expected_keywords": ["stateless", "HTTP", "resources", "JSON", "CRUD"]},
            {"id": 5, "question": "Describe a scenario where you would use a NoSQL database over a relational database.", "difficulty": "Medium", "topic": "Databases", "expected_keywords": ["schema-less", "horizontal scaling", "JSON", "MongoDB", "flexibility"]},
            {"id": 6, "question": "What is the CAP theorem?", "difficulty": "Hard", "topic": "Distributed Systems", "expected_keywords": ["Consistency", "Availability", "Partition tolerance"]},
            {"id": 7, "question": "How does garbage collection work in Python/Java?", "difficulty": "Medium", "topic": "Memory Management", "expected_keywords": ["reference counting", "mark-and-sweep", "heap", "GC"]},
            {"id": 8, "question": "Explain the concept of a binary tree and common traversal methods.", "difficulty": "Medium", "topic": "Data Structures", "expected_keywords": ["inorder", "preorder", "postorder", "root", "leaf", "node"]},
            {"id": 9, "question": "What is Docker and how is it different from a virtual machine?", "difficulty": "Medium", "topic": "DevOps", "expected_keywords": ["container", "lightweight", "kernel", "image", "isolation"]},
            {"id": 10, "question": "Explain the concept of concurrency vs parallelism.", "difficulty": "Hard", "topic": "Systems", "expected_keywords": ["thread", "process", "GIL", "async", "multi-core"]},
        ]
    }

    hr_bank = [
        {"id": 1, "question": "Tell me about yourself and why you're interested in this role.", "category": "Communication", "focus": "Self-presentation and motivation"},
        {"id": 2, "question": "Describe a challenging project you worked on. How did you overcome the challenges?", "category": "Problem-Solving", "focus": "Problem-solving and resilience"},
        {"id": 3, "question": "Tell me about a time you worked in a team and had a conflict. How did you resolve it?", "category": "Teamwork", "focus": "Conflict resolution and communication"},
        {"id": 4, "question": "Where do you see yourself in 5 years?", "category": "Leadership", "focus": "Career vision and ambition"},
        {"id": 5, "question": "What is your greatest weakness and what are you doing about it?", "category": "Self-Awareness", "focus": "Self-awareness and growth mindset"},
        {"id": 6, "question": "Describe a situation where you had to learn a new technology quickly.", "category": "Work-Ethic", "focus": "Adaptability and learning agility"},
        {"id": 7, "question": "How do you prioritize your work when you have multiple deadlines?", "category": "Work-Ethic", "focus": "Time management"},
        {"id": 8, "question": "Tell me about a time you took initiative without being asked.", "category": "Leadership", "focus": "Proactiveness and ownership"},
    ]

    # Role-specific question additions
    role_lower = role.lower()
    extra_tech = []
    if "ml" in role_lower or "machine learning" in role_lower or "data" in role_lower:
        extra_tech = [
            {"id": 11, "question": "Explain overfitting and how to prevent it.", "difficulty": "Medium", "topic": "ML", "expected_keywords": ["regularization", "dropout", "cross-validation", "train/test split", "bias-variance"]},
            {"id": 12, "question": "What is the difference between supervised, unsupervised, and reinforcement learning?", "difficulty": "Easy", "topic": "ML Fundamentals", "expected_keywords": ["labeled", "unlabeled", "reward", "classification", "clustering"]},
        ]
    elif "frontend" in role_lower or "react" in role_lower:
        extra_tech = [
            {"id": 11, "question": "Explain the React component lifecycle and hooks.", "difficulty": "Medium", "topic": "React", "expected_keywords": ["useState", "useEffect", "componentDidMount", "render", "props"]},
            {"id": 12, "question": "What is the Virtual DOM and how does React use it?", "difficulty": "Easy", "topic": "React", "expected_keywords": ["reconciliation", "diffing", "real DOM", "performance"]},
        ]

    all_tech = tech_bank["default"] + extra_tech
    return {
        "technical_questions": all_tech[:n_tech],
        "hr_questions":        hr_bank[:n_hr],
    }
