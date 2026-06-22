"""
Career Copilot AI — Main Streamlit Application
==============================================
8-page career intelligence platform powered by Gemini AI.
"""
import streamlit as st
import sys
import os

# ─── Path Setup ───────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from config import APP_TITLE, APP_ICON, COLORS, CHART_COLORS, GEMINI_MODEL
from ui.components import (
    inject_css, render_hero, render_section_header,
    render_score_card, render_four_scores,
    radar_chart, employability_donut, skill_gap_bar, score_history_line, roadmap_gantt,
    render_skill_pills, render_opportunity_card, render_course_card,
    render_progress_metric, render_empty_state,
)

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════
def init_session():
    defaults = {
        "api_key":          "",
        "parsed_resume":    None,
        "profile":          None,
        "gap_analysis":     None,
        "scores":           None,
        "roadmap":          None,
        "courses":          None,
        "opportunities":    None,
        "interview_qs":     None,
        "interview_results":[],
        "chat_assistant":   None,
        "chat_history":     [],
        "analysis_done":    False,
        "target_role":      "",
        "session_saved":    False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:1rem 0 0.5rem">
            <span style="font-size:2.5rem">🚀</span>
            <h2 style="background:linear-gradient(135deg,#00d2ff,#7b2ff7);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                       margin:0.25rem 0;font-family:'Space Grotesk',sans-serif">
                Career Copilot
            </h2>
            <p style="color:#64748b;font-size:0.75rem;margin:0">AI-Powered Career Intelligence</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── API Key ──────────────────────────────────────────────────────────
        st.markdown("### 🔑 Gemini API Key")
        api_key = st.text_input(
            "Enter Gemini API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="AIza...",
            help="Get free key at aistudio.google.com",
            label_visibility="collapsed",
        )
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            if st.session_state.chat_assistant:
                st.session_state.chat_assistant.api_key = api_key

        if st.session_state.api_key:
            st.success("✅ API Key Set", icon="🔒")
        else:
            st.info("💡 Add key for AI features\n\n[Get free key →](https://aistudio.google.com/)", icon="ℹ️")

        st.markdown("---")

        # ── Status Panel ─────────────────────────────────────────────────────
        if st.session_state.analysis_done and st.session_state.scores:
            scores = st.session_state.scores
            emp = scores.get("employability", {}).get("employability_score", 0)
            st.markdown("### 📊 Your Scores")
            cols = st.columns(2)
            with cols[0]:
                st.metric("🚀 Overall", f"{emp}/100")
                st.metric("📄 ATS",    f"{scores.get('ats',{}).get('ats_score',0)}/100")
            with cols[1]:
                st.metric("🎯 Skills", f"{int(scores.get('skill',{}).get('skill_match_score',0))}/100")
                st.metric("🎤 Interview", f"{scores.get('interview',{}).get('interview_readiness_score',0)}/100")

            st.markdown(f"**Target Role:** {st.session_state.target_role}")
            if st.session_state.profile:
                name = st.session_state.profile.get("name", "")
                if name:
                    st.markdown(f"**Candidate:** {name}")
            st.markdown("---")

        # ── Navigation Hint ───────────────────────────────────────────────────
        st.markdown("""
        <div style="padding:0.75rem;background:rgba(0,210,255,0.05);border-radius:10px;
                    border:1px solid rgba(0,210,255,0.15)">
            <p style="color:#94a3b8;font-size:0.75rem;margin:0;line-height:1.6">
            <b style="color:#00d2ff">How to use:</b><br>
            1️⃣ Upload resume on <b>Home</b><br>
            2️⃣ Enter your dream role<br>
            3️⃣ Click <b>Analyze</b><br>
            4️⃣ Explore all pages!
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<p style="color:#475569;font-size:0.7rem;text-align:center">Career Copilot AI v1.0<br>Powered by Gemini + LangChain</p>', unsafe_allow_html=True)


render_sidebar()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════
PAGES = {
    "🏠 Home":          "home",
    "📊 Dashboard":     "dashboard",
    "🗺️ Roadmap":       "roadmap",
    "💼 Opportunities": "opportunities",
    "📚 Courses":       "courses",
    "🎯 Interview Prep":"interview",
    "🤖 AI Chat":       "chat",
    "📋 History":       "history",
}

if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Home"

cols = st.columns(len(PAGES))
for i, (label, key) in enumerate(PAGES.items()):
    with cols[i]:
        is_active = st.session_state.current_page == label
        btn_style = (
            "background:linear-gradient(135deg,rgba(0,210,255,0.2),rgba(123,47,247,0.2));"
            "border:1px solid rgba(0,210,255,0.4);color:#00d2ff;"
            if is_active else
            "background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);color:#94a3b8;"
        )
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.current_page = label
            st.rerun()

st.markdown("<hr style='margin:0.75rem 0'>", unsafe_allow_html=True)

page = st.session_state.current_page


# ─── Analysis Runner (defined before pages) ───────────────────────────────────
def _run_full_analysis(uploaded_file, target_role: str, timeline: str, free_only: bool):
    """Run the full analysis pipeline with progress tracking."""
    from modules.resume_parser   import parse_resume
    from modules.skill_extractor import extract_skills
    from modules.gap_analyzer    import analyze_gap
    from modules.scoring_engine  import get_all_scores
    from modules.roadmap_generator  import generate_roadmap
    from modules.course_recommender import recommend_courses
    from modules.job_recommender    import recommend_opportunities
    from modules.chat_assistant     import CareerChatAssistant

    api_key  = st.session_state.api_key
    progress = st.progress(0, text="Starting analysis...")
    status   = st.empty()

    try:
        # 1. Parse Resume
        status.info("📄 Parsing resume...")
        progress.progress(10, text="Parsing resume...")
        file_bytes = uploaded_file.read()
        parsed     = parse_resume(file_bytes, uploaded_file.name)
        st.session_state.parsed_resume = parsed

        # 2. Extract Skills
        status.info("🔍 Extracting skills and profile data...")
        progress.progress(25, text="Extracting skills...")
        profile = extract_skills(parsed)
        st.session_state.profile = profile

        # 3. Gap Analysis
        status.info("🎯 Analyzing skill gaps...")
        progress.progress(40, text="Analyzing skill gaps...")
        gap = analyze_gap(profile["skills"], target_role)
        st.session_state.gap_analysis = gap

        # 4. Scoring
        status.info("📊 Calculating career scores...")
        progress.progress(55, text="Calculating scores...")
        scores = get_all_scores(parsed, profile, gap)
        st.session_state.scores = scores

        # 5. Roadmap
        status.info("🗺️ Generating personalized roadmap...")
        progress.progress(65, text="Generating roadmap...")
        roadmap = generate_roadmap(profile, gap, timeline, api_key)
        st.session_state.roadmap = roadmap

        # 6. Courses
        status.info("📚 Finding course recommendations...")
        progress.progress(75, text="Finding courses...")
        pref    = {"free_only": free_only, "platforms": ["Coursera", "Udemy", "edX", "YouTube"]}
        courses = recommend_courses(gap.get("all_missing", [])[:12], pref)
        st.session_state.courses = courses

        # 7. Opportunities
        status.info("💼 Matching opportunities...")
        progress.progress(85, text="Matching opportunities...")
        opps = recommend_opportunities(profile["skills"], target_role)
        st.session_state.opportunities = opps

        # 8. Chat Assistant
        status.info("🤖 Initializing career assistant...")
        progress.progress(93, text="Setting up chat assistant...")
        assistant = CareerChatAssistant(api_key=api_key)
        assistant.update_profile_context(profile, gap)
        st.session_state.chat_assistant = assistant

        # 9. Save to DB
        status.info("💾 Saving session...")
        progress.progress(98, text="Saving...")
        try:
            from modules.history_manager import save_session
            save_session(
                name=profile.get("name", "User"),
                email=profile.get("email", ""),
                filename=uploaded_file.name,
                target_role=target_role,
                profile=profile,
                gap_analysis=gap,
                scores=scores,
                roadmap=roadmap,
            )
            st.session_state.session_saved = True
        except Exception:
            pass

        progress.progress(100, text="Done!")
        st.session_state.analysis_done = True
        status.success("✅ Analysis complete!")
        st.rerun()

    except Exception as e:
        progress.empty()
        status.error(f"❌ Analysis error: {str(e)}")
        st.exception(e)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: HOME — Upload + Analysis
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    render_hero(
        "Career Copilot AI",
        "Upload your resume · Enter your dream role · Get AI-powered career intelligence",
        "🚀"
    )

    col_upload, col_config = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown("### 📁 Upload Resume")
        uploaded_file = st.file_uploader(
            "Drop your resume here",
            type=["pdf", "docx", "doc"],
            label_visibility="collapsed",
            help="Supports PDF and DOCX formats"
        )
        if uploaded_file:
            st.success(f"✅ Uploaded: **{uploaded_file.name}** ({uploaded_file.size // 1024} KB)")

    with col_config:
        st.markdown("### 🎯 Target Configuration")

        from modules.gap_analyzer import get_available_roles
        available_roles = get_available_roles()

        target_role = st.selectbox(
            "Select your dream role",
            [""] + available_roles,
            index=0,
            help="Select from 20+ curated roles",
        )

        custom_role = st.text_input(
            "Or enter a custom role",
            placeholder="e.g. Prompt Engineer, Data Engineer...",
            help="Type any role not in the list above",
        )

        final_role = custom_role.strip() if custom_role.strip() else target_role
        st.session_state.target_role = final_role

        timeline = st.selectbox(
            "⏱️ Learning Timeline",
            ["3 months", "6 months", "12 months", "2 years"],
            index=1,
        )

        free_only = st.toggle("🆓 Free courses only", value=False)

    st.markdown("<br>", unsafe_allow_html=True)

    if uploaded_file and final_role:
        if st.button("🚀 Analyze My Career Profile", use_container_width=True, type="primary"):
            _run_full_analysis(uploaded_file, final_role, timeline, free_only)
    elif uploaded_file and not final_role:
        st.warning("⚠️ Please select or enter your target role.")
    elif final_role and not uploaded_file:
        st.warning("⚠️ Please upload your resume.")
    else:
        st.info("👆 Upload your resume and select a target role to get started.")

    if st.session_state.analysis_done:
        st.success("✅ Analysis complete! Navigate using the tabs above to explore your results.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    render_hero("Career Dashboard", "Your complete career intelligence at a glance", "📊")

    if not st.session_state.analysis_done:
        render_empty_state("📊", "No Analysis Yet", "Upload your resume on the Home page to see your dashboard.")
        st.stop()

    scores  = st.session_state.scores
    profile = st.session_state.profile
    gap     = st.session_state.gap_analysis

    # Score cards
    st.markdown("### 🏆 Your Career Scores")
    render_four_scores(
        scores.get("ats", {}),
        scores.get("skill", {}),
        scores.get("interview", {}),
        scores.get("employability", {}),
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row 1
    col1, col2 = st.columns([1.3, 1], gap="medium")

    with col1:
        render_section_header("Skill Coverage Radar", "", "🕸️")
        req_skills = gap.get("required_skills", [])[:8]
        if req_skills:
            user_pct, role_pct = [], []
            user_set = {s.lower() for s in profile.get("skills", [])}
            for skill in req_skills:
                user_has = skill.lower() in user_set
                partial  = skill in gap.get("partial_required", [])
                user_pct.append(100 if user_has else (55 if partial else 10))
                role_pct.append(100)
            st.plotly_chart(
                radar_chart(req_skills, user_pct, role_pct, f"Skills for {gap.get('target_role','')}"),
                use_container_width=True, config={"displayModeBar": False}
            )
        else:
            st.info("Skill radar will appear after analysis.")

    with col2:
        render_section_header("Score Breakdown", "", "🍩")
        emp_breakdown = scores.get("employability", {}).get("breakdown", {})
        if emp_breakdown:
            st.plotly_chart(
                employability_donut(emp_breakdown),
                use_container_width=True, config={"displayModeBar": False}
            )

    # Charts Row 2
    col3, col4 = st.columns(2, gap="medium")

    with col3:
        render_section_header("Skill Gap Breakdown", "", "📊")
        matched  = gap.get("matched_required", []) + gap.get("matched_preferred", [])
        missing  = gap.get("missing_required",  []) + gap.get("missing_preferred", [])
        partial  = gap.get("partial_required",  []) + gap.get("partial_preferred", [])
        st.plotly_chart(
            skill_gap_bar(matched, missing, partial),
            use_container_width=True, config={"displayModeBar": False}
        )

    with col4:
        render_section_header("Profile Overview", "", "👤")
        exp = scores.get("experience", {})
        render_progress_metric("Experience Level",    min(100, exp.get("years", 0) * 15))
        render_progress_metric("Project Portfolio",   exp.get("project_count",       0) * 20)
        render_progress_metric("Certifications",      exp.get("certification_count", 0) * 25)
        render_progress_metric("Skill Completeness",  int(scores.get("skill", {}).get("skill_match_score", 0)))
        render_progress_metric("Resume Completeness", scores.get("ats", {}).get("ats_score", 0))

    # Skill details
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_header("Skill Gap Details", "", "🎯")

    t1, t2, t3 = st.tabs(["✅ Skills You Have", "❌ Missing Required", "⚠️ Partial Match"])
    with t1:
        render_skill_pills(gap.get("matched_required", []) + gap.get("matched_preferred", []), "have")
    with t2:
        missing_all = gap.get("missing_required", []) + gap.get("missing_preferred", [])
        if missing_all:
            render_skill_pills(missing_all, "missing")
        else:
            st.success("🎉 No missing skills detected!")
    with t3:
        partial_all = gap.get("partial_required", []) + gap.get("partial_preferred", [])
        if partial_all:
            render_skill_pills(partial_all, "partial")
        else:
            st.info("No partial matches.")

    # Profile card
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_header("Parsed Profile", "", "📄")
    with st.expander("View extracted profile data", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Name:** {profile.get('name','N/A')}")
            st.markdown(f"**Email:** {profile.get('email','N/A')}")
            st.markdown(f"**Phone:** {profile.get('phone','N/A')}")
            st.markdown(f"**LinkedIn:** {profile.get('linkedin','N/A')}")
            st.markdown(f"**GitHub:** {profile.get('github','N/A')}")
        with c2:
            st.markdown(f"**Experience:** {profile.get('experience_years',0)} years")
            st.markdown(f"**Projects:** {len(profile.get('projects',[]))}")
            st.markdown(f"**Certifications:** {len(profile.get('certifications',[]))}")
            degrees = profile.get("education",{}).get("degrees",[])
            st.markdown(f"**Degrees:** {', '.join(degrees) if degrees else 'N/A'}")

    # ATS Missing Sections
    ats = scores.get("ats", {})
    missing_secs = ats.get("missing_sections", [])
    if missing_secs:
        st.markdown("<br>", unsafe_allow_html=True)
        render_section_header("ATS Improvement Tips", "", "💡")
        st.warning(f"⚠️ Your resume is missing or has very thin content in: **{', '.join(missing_secs)}**")
        st.info("Add these sections to your resume to improve your ATS score significantly.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: ROADMAP
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Roadmap":
    render_hero("Learning Roadmap", "Your personalized path to becoming a top candidate", "🗺️")

    if not st.session_state.analysis_done:
        render_empty_state("🗺️", "No Roadmap Yet", "Complete the analysis on the Home page first.")
        st.stop()

    roadmap = st.session_state.roadmap
    if not roadmap:
        st.warning("Roadmap not generated. Please re-run the analysis.")
        st.stop()

    # Overview
    col1, col2 = st.columns([2, 1], gap="large")
    with col1:
        st.markdown(f"""
        <div class="glass-card">
            <h3 style="color:#00d2ff;margin-top:0">📋 Roadmap Overview</h3>
            <p style="color:#e2e8f0">{roadmap.get('overview','')}</p>
            <div style="display:flex;gap:1rem;margin-top:1rem">
                <div style="background:rgba(0,210,255,0.1);border:1px solid rgba(0,210,255,0.3);
                            border-radius:8px;padding:0.5rem 1rem;text-align:center">
                    <div style="color:#00d2ff;font-weight:700;font-size:1.2rem">{len(roadmap.get('phases',[]))}</div>
                    <div style="color:#94a3b8;font-size:0.75rem">Phases</div>
                </div>
                <div style="background:rgba(123,47,247,0.1);border:1px solid rgba(123,47,247,0.3);
                            border-radius:8px;padding:0.5rem 1rem;text-align:center">
                    <div style="color:#7b2ff7;font-weight:700;font-size:1.2rem">{roadmap.get('total_duration','N/A')}</div>
                    <div style="color:#94a3b8;font-size:0.75rem">Duration</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        target = st.session_state.gap_analysis.get("target_role", "")
        score  = st.session_state.scores.get("skill", {}).get("skill_match_score", 0)
        st.markdown(f"""
        <div class="glass-card" style="text-align:center">
            <div style="font-size:2rem">🎯</div>
            <div style="color:#94a3b8;font-size:0.8rem">Target Role</div>
            <div style="color:#00d2ff;font-weight:700;font-size:1.1rem;margin:0.5rem 0">{target}</div>
            <hr>
            <div style="color:#94a3b8;font-size:0.8rem">Current Match</div>
            <div style="color:#00e676;font-weight:700;font-size:1.5rem">{score:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gantt view
    render_section_header("Timeline View", "", "📅")
    phases = roadmap.get("phases", [])
    if phases:
        st.plotly_chart(roadmap_gantt(phases), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # Phase details
    render_section_header("Phase Details", "", "📌")
    for phase in phases:
        phase_color = CHART_COLORS[(phase["phase_number"] - 1) % len(CHART_COLORS)]
        with st.expander(f"Phase {phase['phase_number']}: {phase['title']} — {phase['duration']}", expanded=phase["phase_number"] == 1):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**🎯 Focus:** {phase.get('focus','')}")
                st.markdown("**📌 Goals:**")
                for g in phase.get("goals", []):
                    st.markdown(f"- ✅ {g}")
            with c2:
                st.markdown("**🔧 Actions:**")
                for a in phase.get("actions", []):
                    st.markdown(f"- 🔨 {a}")
                st.markdown("**🏆 Milestones:**")
                for m in phase.get("milestones", []):
                    st.markdown(f"- 🏅 {m}")
            if phase.get("skills_covered"):
                render_skill_pills(phase["skills_covered"], "have")

    if roadmap.get("final_advice"):
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"💡 **Final Advice:** {roadmap['final_advice']}")

    # Download roadmap
    from modules.roadmap_generator import roadmap_to_markdown
    md_content = roadmap_to_markdown(roadmap)
    st.download_button(
        "📥 Download Roadmap as Markdown",
        data=md_content.encode(),
        file_name=f"roadmap_{st.session_state.target_role.replace(' ','_')}.md",
        mime="text/markdown",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: OPPORTUNITIES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💼 Opportunities":
    render_hero("Opportunities", "Curated jobs, internships, hackathons, scholarships & competitions for you", "💼")

    if not st.session_state.analysis_done:
        render_empty_state("💼", "No Opportunities Yet", "Complete the analysis on the Home page first.")
        st.stop()

    opps    = st.session_state.opportunities or {}
    profile = st.session_state.profile

    cat_labels = {
        "jobs":          ("💼 Jobs",          "Full-time positions"),
        "internships":   ("🎓 Internships",    "Internship programs"),
        "hackathons":    ("⚡ Hackathons",     "Competitions & hackathons"),
        "scholarships":  ("🏆 Scholarships",  "Funding & scholarships"),
        "competitions":  ("🥇 Competitions",  "Programming contests"),
    }

    tabs = st.tabs([v[0] for v in cat_labels.values()])

    for tab, (cat, (label, desc)) in zip(tabs, cat_labels.items()):
        with tab:
            items = opps.get(cat, [])
            render_section_header(label.split(" ", 1)[1], f"{len(items)} opportunities matched your profile", label.split(" ")[0])
            if items:
                for item in items:
                    render_opportunity_card(item, cat)
            else:
                render_empty_state("🔍", "No matches yet", "Try re-running analysis with different skills.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5: COURSES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📚 Courses":
    render_hero("Course Recommendations", "Bridge your skill gaps with the best courses from top platforms", "📚")

    if not st.session_state.analysis_done:
        render_empty_state("📚", "No Recommendations Yet", "Complete the analysis on the Home page first.")
        st.stop()

    courses = st.session_state.courses or {}
    gap     = st.session_state.gap_analysis or {}

    # Summary stats
    total_courses = sum(len(c) for c in courses.values())
    free_count    = sum(1 for clist in courses.values() for c in clist if c.get("free"))
    skills_count  = len(courses)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("📚 Total Courses",     total_courses)
    with c2:
        st.metric("🆓 Free Courses",      free_count)
    with c3:
        st.metric("🎯 Skills Covered",    skills_count)

    st.markdown("<br>", unsafe_allow_html=True)

    # Filter options
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_platform = st.multiselect(
            "Filter by Platform",
            ["Coursera", "Udemy", "edX", "YouTube"],
            default=["Coursera", "Udemy", "edX", "YouTube"],
        )
    with col_f2:
        filter_free = st.toggle("Show free courses only", value=False)

    st.markdown("---")

    if not courses:
        st.info("No skill gaps found or no course matches. Great job on your skills!")
    else:
        for skill, course_list in courses.items():
            filtered = [
                c for c in course_list
                if c.get("platform") in filter_platform
                and (not filter_free or c.get("free", False))
            ]
            if not filtered:
                continue

            is_priority = skill in gap.get("missing_required", [])
            priority_tag = " 🔴 Priority" if is_priority else ""

            render_section_header(f"{skill}{priority_tag}", f"{len(filtered)} courses available", "📖")
            for course in filtered:
                render_course_card(course, skill)
            st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6: INTERVIEW PREP
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Interview Prep":
    render_hero("Interview Preparation", "AI-generated questions with real-time answer evaluation", "🎯")

    if not st.session_state.analysis_done:
        render_empty_state("🎯", "No Interview Prep Yet", "Complete the analysis on the Home page first.")
        st.stop()

    profile  = st.session_state.profile
    gap      = st.session_state.gap_analysis
    api_key  = st.session_state.api_key
    target   = st.session_state.target_role

    # Controls
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    with col_ctrl1:
        n_tech = st.slider("Technical Questions", 3, 10, 5)
    with col_ctrl2:
        n_hr   = st.slider("HR Questions", 3, 10, 5)
    with col_ctrl3:
        q_type = st.selectbox("Start with", ["Technical", "HR", "Both"])

    if st.button("🎲 Generate New Questions", use_container_width=True):
        from modules.interview_engine import generate_questions
        with st.spinner("Generating interview questions..."):
            qs = generate_questions(
                target_role=target,
                user_skills=profile.get("skills", []),
                experience_years=profile.get("experience_years", 0),
                n_technical=n_tech,
                n_hr=n_hr,
                api_key=api_key,
            )
            st.session_state.interview_qs      = qs
            st.session_state.interview_results = []
        st.success(f"✅ Generated {n_tech} technical + {n_hr} HR questions!")

    if not st.session_state.interview_qs:
        st.info("👆 Click **Generate New Questions** to begin your mock interview.")
        st.stop()

    qs = st.session_state.interview_qs
    results = st.session_state.interview_results
    results_map = {r["question"]: r for r in results}

    # Score summary if some attempted
    if results:
        scores_done = [r.get("score", 0) for r in results]
        avg_score   = sum(scores_done) / len(scores_done) if scores_done else 0
        intv_score  = min(100, round((avg_score / 10) * 100))

        sc1, sc2, sc3 = st.columns(3)
        with sc1: st.metric("Questions Attempted", len(results))
        with sc2: st.metric("Average Score",       f"{avg_score:.1f}/10")
        with sc3: st.metric("Interview Readiness", f"{intv_score}%")

        # Update session state interview score
        from modules.scoring_engine import calculate_interview_readiness_score
        ir_result = calculate_interview_readiness_score(results)
        if st.session_state.scores:
            st.session_state.scores["interview"] = ir_result

        st.markdown("---")

    # Technical Questions
    if q_type in ("Technical", "Both") and qs.get("technical_questions"):
        render_section_header("Technical Questions", f"Test your technical knowledge for {target}", "💻")
        for q in qs["technical_questions"]:
            qtext = q.get("question", "")
            diff  = q.get("difficulty", "Medium")
            topic = q.get("topic", "")
            kw    = q.get("expected_keywords", [])

            diff_colors = {"Easy": "#00e676", "Medium": "#ffab40", "Hard": "#ff6b6b"}
            diff_color  = diff_colors.get(diff, "#94a3b8")

            existing = results_map.get(qtext, {})

            with st.container():
                st.markdown(f"""
                <div class="question-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.75rem">
                        <span style="color:#00d2ff;font-weight:600;font-size:0.85rem">Q{q.get('id','')} · {topic}</span>
                        <span style="background:{diff_color}22;border:1px solid {diff_color}66;
                                     color:{diff_color};padding:2px 10px;border-radius:12px;font-size:0.75rem">
                            {diff}
                        </span>
                    </div>
                    <p style="color:#e2e8f0;margin:0;font-size:0.95rem;line-height:1.6">{qtext}</p>
                </div>
                """, unsafe_allow_html=True)

                ans_key = f"tech_ans_{q.get('id', '')}"
                answer  = st.text_area("Your Answer:", value=existing.get("answer", ""), key=ans_key, height=100, placeholder="Type your answer here...")

                eval_col, _ = st.columns([1, 3])
                with eval_col:
                    if st.button("⚡ Evaluate", key=f"eval_tech_{q.get('id','')}", use_container_width=True):
                        if answer.strip():
                            from modules.interview_engine import evaluate_answer
                            with st.spinner("Evaluating..."):
                                result = evaluate_answer(qtext, answer, "Technical", target, kw, api_key)
                                result["question"] = qtext
                                result["answer"]   = answer
                                result["type"]     = "technical"

                            # Update results
                            updated = [r for r in st.session_state.interview_results if r.get("question") != qtext]
                            updated.append(result)
                            st.session_state.interview_results = updated

                            score  = result.get("score", 0)
                            grade  = result.get("grade", "")
                            score_emoji = "🟢" if score >= 7 else "🟡" if score >= 5 else "🔴"
                            st.success(f"{score_emoji} Score: **{score}/10** (Grade: {grade})")
                            if result.get("feedback"):
                                st.markdown(f"**💬 Feedback:** {result['feedback']}")
                            if result.get("improvements"):
                                st.markdown("**🔧 Improvements:**")
                                for imp in result["improvements"]:
                                    st.markdown(f"- {imp}")
                        else:
                            st.warning("Please write an answer before evaluating.")

                # Show previous result if exists
                if existing and existing.get("score"):
                    st.markdown(f"*Previous: Score {existing['score']}/10 — {existing.get('feedback','')}*")

                st.markdown("<br>", unsafe_allow_html=True)

    # HR Questions
    if q_type in ("HR", "Both") and qs.get("hr_questions"):
        render_section_header("HR & Behavioral Questions", "Demonstrate your soft skills and work style", "🤝")
        for q in qs["hr_questions"]:
            qtext = q.get("question", "")
            cat   = q.get("category", "")
            focus = q.get("focus", "")

            existing = results_map.get(qtext, {})

            with st.container():
                st.markdown(f"""
                <div class="question-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.75rem">
                        <span style="color:#7b2ff7;font-weight:600;font-size:0.85rem">HR · {cat}</span>
                        <span style="color:#94a3b8;font-size:0.78rem">{focus}</span>
                    </div>
                    <p style="color:#e2e8f0;margin:0;font-size:0.95rem;line-height:1.6">{qtext}</p>
                </div>
                """, unsafe_allow_html=True)

                ans_key = f"hr_ans_{q.get('id', '')}"
                answer  = st.text_area("Your Answer:", value=existing.get("answer",""), key=ans_key, height=100, placeholder="Use STAR method: Situation, Task, Action, Result...")

                eval_col2, _ = st.columns([1, 3])
                with eval_col2:
                    if st.button("⚡ Evaluate", key=f"eval_hr_{q.get('id','')}", use_container_width=True):
                        if answer.strip():
                            from modules.interview_engine import evaluate_answer
                            with st.spinner("Evaluating..."):
                                result = evaluate_answer(qtext, answer, "HR", target, [], api_key)
                                result["question"] = qtext
                                result["answer"]   = answer
                                result["type"]     = "hr"

                            updated = [r for r in st.session_state.interview_results if r.get("question") != qtext]
                            updated.append(result)
                            st.session_state.interview_results = updated

                            score = result.get("score", 0)
                            grade = result.get("grade", "")
                            st.success(f"Score: **{score}/10** (Grade: {grade})")
                            if result.get("feedback"):
                                st.info(f"💬 {result['feedback']}")
                        else:
                            st.warning("Please write an answer before evaluating.")
                st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 7: AI CHAT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 AI Chat":
    render_hero("Career Assistant", "Your personal AI career advisor — ask anything!", "🤖")

    # Initialize chat assistant if needed
    if not st.session_state.chat_assistant:
        from modules.chat_assistant import CareerChatAssistant
        st.session_state.chat_assistant = CareerChatAssistant(
            api_key=st.session_state.api_key
        )
        if st.session_state.profile and st.session_state.gap_analysis:
            st.session_state.chat_assistant.update_profile_context(
                st.session_state.profile,
                st.session_state.gap_analysis
            )

    assistant = st.session_state.chat_assistant
    assistant.api_key = st.session_state.api_key

    # Chat controls
    col_a, col_b = st.columns([3, 1])
    with col_b:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            assistant.clear_history()
            st.rerun()

    # Quick prompts
    st.markdown("**💡 Quick Prompts:**")
    prompt_cols = st.columns(4)
    quick_prompts = [
        "How do I improve my ATS score?",
        "What skills should I learn first?",
        "Give me salary negotiation tips",
        "How to prepare for system design?",
    ]
    for i, prompt in enumerate(quick_prompts):
        with prompt_cols[i]:
            if st.button(prompt, key=f"qp_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.spinner("Thinking..."):
                    response = assistant.chat(prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

    st.markdown("---")

    # Chat history display
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center;padding:2rem;opacity:0.6">
                <div style="font-size:3rem">🤖</div>
                <p style="color:#94a3b8">I'm here to help with your career journey!</p>
                <p style="color:#64748b;font-size:0.85rem">
                    Ask me anything: resume tips, interview advice, salary insights, learning paths...
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                    st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Ask your career question here...", key="chat_input")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("CareerCopilot is thinking..."):
            response = assistant.chat(user_input)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 8: HISTORY & REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 History":
    render_hero("Session History & Reports", "Track your career progress over time and export reports", "📋")

    from modules.history_manager import get_all_sessions, get_session_by_id, delete_session, generate_pdf_report

    sessions = get_all_sessions()

    if not sessions:
        render_empty_state("📋", "No History Yet", "Your analysis sessions will appear here after you analyze a resume.")
        st.stop()

    # Progress chart
    if len(sessions) > 1:
        render_section_header("Score History", "Track your improvement over time", "📈")
        st.plotly_chart(score_history_line(sessions), use_container_width=True, config={"displayModeBar": False})
        st.markdown("<br>", unsafe_allow_html=True)

    # Sessions list
    render_section_header("Past Sessions", f"{len(sessions)} sessions found", "🗂️")

    for sesh in sessions:
        emp   = sesh.get("employability_score", 0)
        skill = sesh.get("skill_match_score", 0)
        ats   = sesh.get("ats_score", 0)
        dt    = sesh.get("created_at", "")[:16].replace("T", " ")

        col_info, col_scores, col_actions = st.columns([2, 2, 1])

        with col_info:
            st.markdown(f"**{sesh.get('name','Unknown')}** — {sesh.get('target_role','N/A')}")
            st.caption(f"📁 {sesh.get('filename','N/A')} | 📅 {dt}")

        with col_scores:
            s1, s2, s3 = st.columns(3)
            with s1: st.metric("🚀 Overall", f"{emp}%")
            with s2: st.metric("🎯 Skills",  f"{int(skill)}%")
            with s3: st.metric("📄 ATS",     f"{ats}%")

        with col_actions:
            if st.button("📥 PDF", key=f"pdf_{sesh['id']}", use_container_width=True):
                full = get_session_by_id(sesh["id"])
                pdf  = generate_pdf_report(full)
                if pdf:
                    st.download_button(
                        "💾 Download PDF",
                        data=pdf,
                        file_name=f"career_report_{sesh['id']}.pdf",
                        mime="application/pdf",
                        key=f"dl_{sesh['id']}"
                    )
                else:
                    st.error("PDF generation failed. Install reportlab.")

            if st.button("🗑️", key=f"del_{sesh['id']}", help="Delete this session"):
                delete_session(sesh["id"])
                st.rerun()

        st.markdown("---")

    # Export current session
    if st.session_state.analysis_done and st.session_state.scores:
        st.markdown("<br>", unsafe_allow_html=True)
        render_section_header("Export Current Session", "", "📤")
        if st.button("📥 Download Current Session as PDF", use_container_width=True):
            current_data = {
                "name":        st.session_state.profile.get("name", "User"),
                "target_role": st.session_state.target_role,
                "created_at":  __import__("datetime").datetime.now().isoformat(),
                "gap_analysis": st.session_state.gap_analysis,
                "scores":       st.session_state.scores,
                "roadmap":      st.session_state.roadmap,
            }
            pdf = generate_pdf_report(current_data)
            if pdf:
                st.download_button(
                    "💾 Download PDF",
                    data=pdf,
                    file_name=f"career_report_{st.session_state.target_role.replace(' ','_')}.pdf",
                    mime="application/pdf",
                )
            else:
                st.error("PDF generation failed. Make sure reportlab is installed.")
