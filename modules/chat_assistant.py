"""
Chat Assistant — LangChain conversational career assistant with Gemini + ChromaDB memory.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are CareerCopilot AI, an expert career advisor and mentor specializing in tech careers. 

You have access to the user's career profile:
{profile_context}

Your capabilities:
- Answering questions about career paths, skill development, and job market
- Providing personalized advice based on the user's resume and target role
- Explaining technical concepts and learning strategies
- Recommending resources, courses, and opportunities
- Helping with interview preparation
- Analyzing salary trends and market demand
- Providing resume improvement tips

Be conversational, encouraging, and specific. Always relate advice to the user's actual profile when possible.
Keep responses concise but comprehensive. Use emojis sparingly to make responses friendly.
"""


class CareerChatAssistant:
    """LangChain-powered conversational career assistant."""

    def __init__(self, api_key: str = "", profile_context: str = ""):
        self.api_key         = api_key
        self.profile_context = profile_context
        self.history         = []
        self._langchain_chain = None
        self._simple_model    = None

    def chat(self, user_message: str) -> str:
        """Send a message and get a response."""
        if self.api_key:
            response = self._gemini_chat(user_message)
        else:
            response = self._rule_based_response(user_message)

        self.history.append({"role": "user",      "content": user_message})
        self.history.append({"role": "assistant",  "content": response})
        return response

    def _gemini_chat(self, message: str) -> str:
        """Use Google Gemini for conversational AI."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)

            if not self._simple_model:
                self._simple_model = genai.GenerativeModel(
                    "gemini-1.5-flash",
                    system_instruction=SYSTEM_PROMPT.format(
                        profile_context=self.profile_context or "No profile loaded yet."
                    )
                )
                self._chat_session = self._simple_model.start_chat(history=[])

            response = self._chat_session.send_message(message)
            return response.text
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return self._rule_based_response(message)

    def _rule_based_response(self, message: str) -> str:
        """Intelligent rule-based fallback responses."""
        msg_lower = message.lower()

        if any(w in msg_lower for w in ["salary", "pay", "compensation", "ctc", "lpa"]):
            return (
                "💰 **Salary Insights**\n\n"
                "Salaries vary significantly by role, location, and experience:\n"
                "- **Entry Level (0-2 yrs)**: ₹4-12 LPA in India | $70K-90K in USA\n"
                "- **Mid Level (3-5 yrs)**: ₹12-25 LPA in India | $90K-130K in USA\n"
                "- **Senior (6+ yrs)**: ₹25-60 LPA in India | $130K-180K+ in USA\n\n"
                "Use platforms like **Glassdoor**, **Levels.fyi**, and **LinkedIn Salary** for role-specific data."
            )

        elif any(w in msg_lower for w in ["resume", "cv", "application"]):
            return (
                "📄 **Resume Tips**\n\n"
                "To maximize your ATS score and recruiter appeal:\n"
                "1. **Keywords**: Match skills from the job description\n"
                "2. **Quantify**: Use metrics (e.g., 'Reduced load time by 40%')\n"
                "3. **Format**: Clean, single-column, ATS-friendly format\n"
                "4. **Length**: 1 page for <5 yrs experience, 2 pages max\n"
                "5. **Tailor**: Customize for each application\n\n"
                "Check your **ATS Score** in the Dashboard for specific improvements!"
            )

        elif any(w in msg_lower for w in ["interview", "prepare", "question"]):
            return (
                "🎯 **Interview Preparation Guide**\n\n"
                "**Technical Prep:**\n"
                "- Practice on LeetCode, HackerRank, or CodeSignal daily\n"
                "- Study system design (Grokking System Design)\n"
                "- Review your tech stack deeply\n\n"
                "**Behavioral Prep:**\n"
                "- Use the **STAR method** (Situation, Task, Action, Result)\n"
                "- Prepare 5-7 stories from past experience\n\n"
                "Head to the **Interview Prep** tab for AI-generated questions tailored to your role!"
            )

        elif any(w in msg_lower for w in ["learn", "course", "study", "skill"]):
            return (
                "📚 **Learning Roadmap Tips**\n\n"
                "The most effective learning approach:\n"
                "1. **Focus** on 2-3 skills at a time, not everything\n"
                "2. **80/20 Rule**: 80% practice, 20% theory\n"
                "3. **Build projects** immediately after learning\n"
                "4. **Top Platforms**: Coursera (structured), Udemy (affordable), YouTube (free)\n\n"
                "Check your personalized **Course Recommendations** and **Roadmap** tabs!"
            )

        elif any(w in msg_lower for w in ["job", "placement", "hiring", "apply", "opportunity"]):
            return (
                "💼 **Job Search Strategy**\n\n"
                "**Where to apply:**\n"
                "- LinkedIn, Naukri, AngelList (startups), company career pages\n"
                "- Referrals: 3x higher success rate than cold applications\n\n"
                "**Application tips:**\n"
                "1. Apply to 10-20 roles per week\n"
                "2. Customize your resume for each JD\n"
                "3. Follow up after 1 week\n"
                "4. Network on LinkedIn: connect + message recruiters\n\n"
                "Browse **Opportunities** tab for curated jobs matching your profile!"
            )

        elif any(w in msg_lower for w in ["hello", "hi", "hey", "start"]):
            return (
                "👋 Hello! I'm **CareerCopilot AI**, your personal career advisor!\n\n"
                "I can help you with:\n"
                "- 📄 Resume improvement tips\n"
                "- 🎯 Interview preparation\n"
                "- 📚 Learning resources & roadmaps\n"
                "- 💼 Job search strategies\n"
                "- 💰 Salary negotiation advice\n"
                "- 🚀 Career growth planning\n\n"
                "Upload your resume first to get personalized advice. What would you like to know?"
            )

        elif any(w in msg_lower for w in ["hackathon", "competition", "scholarship", "internship"]):
            return (
                "🏆 **Opportunities for Students & Early Career Professionals**\n\n"
                "**Hackathons:**\n"
                "- Google Hack4Change, Smart India Hackathon, MLH Global Hackathons\n"
                "- Great for portfolio, networking, and prize money\n\n"
                "**Scholarships:**\n"
                "- Google Developer Scholarship, Microsoft MLSA, GitHub Campus Expert\n"
                "- AWS Educate for cloud learners\n\n"
                "**Internships:**\n"
                "- Google Summer of Code, Microsoft Research, Adobe Research\n\n"
                "See your full **Opportunities** tab for details and deadlines!"
            )

        else:
            return (
                "🤖 I'm here to help with your career journey! You can ask me about:\n\n"
                "- **Resume tips** — how to improve your resume\n"
                "- **Interview prep** — technical & HR question strategies\n"
                "- **Learning paths** — what to learn next\n"
                "- **Job opportunities** — where and how to apply\n"
                "- **Salary insights** — what to expect\n"
                "- **Career transitions** — how to switch roles\n\n"
                "What specific career challenge can I help you solve today?"
            )

    def clear_history(self):
        """Reset conversation history."""
        self.history = []
        self._simple_model   = None
        self._chat_session   = None

    def update_profile_context(self, profile: dict, gap_analysis: dict):
        """Update the assistant's knowledge of the user's profile."""
        skills   = profile.get("skills", [])
        role     = gap_analysis.get("target_role", "Unknown")
        missing  = gap_analysis.get("missing_required", [])
        score    = gap_analysis.get("skill_match_score", 0)

        self.profile_context = (
            f"Name: {profile.get('name', 'User')}\n"
            f"Target Role: {role}\n"
            f"Current Skills: {', '.join(skills[:15])}\n"
            f"Experience: {profile.get('experience_years', 0)} years\n"
            f"Missing Skills: {', '.join(missing[:10])}\n"
            f"Skill Match Score: {score}%\n"
            f"Projects: {len(profile.get('projects', []))} listed\n"
            f"Certifications: {len(profile.get('certifications', []))} listed"
        )
        # Reset model so system prompt is updated
        self._simple_model = None
