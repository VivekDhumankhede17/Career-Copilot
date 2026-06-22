"""
Reusable Streamlit UI components for Career Copilot.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from config import COLORS, CHART_COLORS


# ─── CSS Injection ────────────────────────────────────────────────────────────

def inject_css():
    """Inject the global CSS stylesheet."""
    css_path = __file__.replace("components.py", "../ui/styles.css").replace("ui/", "")
    import os
    css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "styles.css")
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ─── Header Components ────────────────────────────────────────────────────────

def render_hero(title: str, subtitle: str, emoji: str = "🚀"):
    st.markdown(f"""
    <div class="hero-section">
        <div style="font-size:3rem; margin-bottom:0.5rem">{emoji}</div>
        <h1 style="background:linear-gradient(135deg,#00d2ff,#7b2ff7);-webkit-background-clip:text;
                   -webkit-text-fill-color:transparent;font-size:2.5rem;margin:0;font-family:'Space Grotesk',sans-serif">
            {title}
        </h1>
        <p style="color:#94a3b8;font-size:1.1rem;margin-top:0.75rem;max-width:600px;margin-left:auto;margin-right:auto">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(title: str, subtitle: str = "", emoji: str = ""):
    st.markdown(f"""
    <div style="margin-bottom:1.5rem">
        <h2 style="color:#e2e8f0;font-family:'Space Grotesk',sans-serif;margin-bottom:0.25rem">
            {emoji} {title}
        </h2>
        {f'<p style="color:#94a3b8;margin:0">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


# ─── Score Cards ──────────────────────────────────────────────────────────────

def render_score_card(label: str, value: int, icon: str = "📊", color: str = "#00d2ff", tier: str = ""):
    pct = min(100, max(0, value))
    st.markdown(f"""
    <div class="score-card">
        <div style="font-size:2rem;margin-bottom:0.5rem">{icon}</div>
        <div class="score-value" style="background:linear-gradient(135deg,{color},{COLORS['secondary']});
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">
            {pct}
        </div>
        <div style="font-size:0.6rem;color:#94a3b8;margin:0.2rem 0">/ 100</div>
        <div class="score-label">{label}</div>
        {f'<div style="color:{color};font-size:0.8rem;margin-top:0.5rem;font-weight:600">{tier}</div>' if tier else ''}
    </div>
    """, unsafe_allow_html=True)


def render_four_scores(ats: dict, skill: dict, interview: dict, employability: dict):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_score_card("ATS Score",           ats.get("ats_score", 0),                        "📄", "#00d2ff")
    with c2:
        render_score_card("Skill Match",         int(skill.get("skill_match_score", 0)),          "🎯", "#7b2ff7",  skill.get("tier", ""))
    with c3:
        render_score_card("Interview Readiness", interview.get("interview_readiness_score", 0),   "🎤", "#ff6b6b",  interview.get("tier", ""))
    with c4:
        render_score_card("Employability",       employability.get("employability_score", 0),     "🚀", "#00e676",  employability.get("tier", ""))


# ─── Charts ───────────────────────────────────────────────────────────────────

def radar_chart(categories: list, user_values: list, role_values: list, title: str = "Skill Coverage") -> go.Figure:
    cats = categories + [categories[0]]
    uv   = user_values + [user_values[0]]
    rv   = role_values + [role_values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=rv, theta=cats, fill='toself',
        name='Role Requirements',
        line=dict(color='rgba(123,47,247,0.8)', width=2),
        fillcolor='rgba(123,47,247,0.1)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=uv, theta=cats, fill='toself',
        name='Your Skills',
        line=dict(color='rgba(0,210,255,0.9)', width=2),
        fillcolor='rgba(0,210,255,0.15)'
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.1)',
                            color='rgba(255,255,255,0.4)', tickfont=dict(size=9, color='#94a3b8')),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.1)', color='rgba(255,255,255,0.5)')
        ),
        showlegend=True,
        legend=dict(font=dict(color='#e2e8f0', size=11), bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title=dict(text=title, font=dict(color='#e2e8f0', size=14, family='Space Grotesk'),
                   x=0.5, xanchor='center'),
        margin=dict(t=60, b=20, l=20, r=20),
        height=380,
    )
    return fig


def employability_donut(breakdown: dict) -> go.Figure:
    labels = list(breakdown.keys())
    values = [abs(v) for v in breakdown.values()]

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.6,
        marker=dict(colors=CHART_COLORS[:len(labels)],
                    line=dict(color='rgba(10,15,30,1)', width=2)),
        textinfo='label+percent',
        textfont=dict(color='#e2e8f0', size=10),
        hovertemplate='%{label}: %{value:.0f}/100<extra></extra>',
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=300,
        margin=dict(t=20, b=20, l=20, r=20),
        annotations=[dict(
            text="Score<br>Mix",
            x=0.5, y=0.5, font_size=13,
            font_color='#e2e8f0', showarrow=False
        )]
    )
    return fig


def skill_gap_bar(matched: list, missing: list, partial: list) -> go.Figure:
    categories = ["Matched ✅", "Partial Match ⚠️", "Missing ❌"]
    values     = [len(matched), len(partial), len(missing)]
    colors_bar = ["#00e676", "#ffab40", "#ff6b6b"]

    fig = go.Figure(go.Bar(
        x=categories, y=values,
        marker=dict(
            color=colors_bar,
            line=dict(color='rgba(0,0,0,0)', width=0),
        ),
        text=values,
        textposition='outside',
        textfont=dict(color='#e2e8f0', size=13, family='Space Grotesk'),
        hovertemplate='%{x}: %{y} skills<extra></extra>',
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(255,255,255,0.06)', color='#94a3b8', title='Skills'),
        xaxis=dict(color='#e2e8f0'),
        height=280,
        margin=dict(t=20, b=10, l=10, r=10),
        font=dict(color='#e2e8f0'),
    )
    return fig


def score_history_line(sessions: list) -> go.Figure:
    if not sessions:
        return go.Figure()

    dates  = [s.get("created_at", "")[:10] for s in sessions[::-1]]
    emp    = [s.get("employability_score", 0)  for s in sessions[::-1]]
    skill  = [s.get("skill_match_score", 0)    for s in sessions[::-1]]
    ats    = [s.get("ats_score", 0)             for s in sessions[::-1]]

    fig = go.Figure()
    for name, vals, color in [
        ("Employability", emp,   "#00e676"),
        ("Skill Match",   skill, "#00d2ff"),
        ("ATS Score",     ats,   "#7b2ff7"),
    ]:
        fig.add_trace(go.Scatter(
            x=dates, y=vals, name=name, mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=8, color=color),
        ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(255,255,255,0.06)', color='#94a3b8', range=[0, 105]),
        xaxis=dict(color='#94a3b8'),
        legend=dict(font=dict(color='#e2e8f0'), bgcolor='rgba(0,0,0,0)'),
        height=250,
        margin=dict(t=20, b=10, l=10, r=10),
        font=dict(color='#e2e8f0'),
    )
    return fig


def roadmap_gantt(phases: list) -> go.Figure:
    """Render roadmap phases as a horizontal Gantt bar chart."""
    if not phases:
        return go.Figure()

    fig = go.Figure()
    for i, phase in enumerate(phases):
        color = CHART_COLORS[i % len(CHART_COLORS)]
        fig.add_trace(go.Bar(
            y=[f"Phase {phase['phase_number']}"],
            x=[1],
            base=[i],
            orientation='h',
            marker=dict(color=color, opacity=0.8),
            name=phase['title'],
            text=f"  {phase['title']} ({phase['duration']})",
            textposition='inside',
            hovertemplate=f"<b>{phase['title']}</b><br>{phase['duration']}<br>Focus: {phase.get('focus','')}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        barmode='stack',
        showlegend=False,
        yaxis=dict(color='#e2e8f0', autorange='reversed'),
        xaxis=dict(visible=False),
        height=max(200, len(phases) * 55),
        margin=dict(t=10, b=10, l=10, r=10),
        font=dict(color='#e2e8f0', size=11),
    )
    return fig


# ─── Skill Pills ──────────────────────────────────────────────────────────────

def render_skill_pills(skills: list, pill_type: str = "have", cols_per_row: int = 5):
    """Render skills as colored pills."""
    class_map = {
        "have":    "skill-pill skill-pill-have",
        "missing": "skill-pill skill-pill-missing",
        "partial": "skill-pill skill-pill-partial",
    }
    cls  = class_map.get(pill_type, "skill-pill skill-pill-have")
    html = "".join(f'<span class="{cls}">{s}</span>' for s in skills)
    st.markdown(f'<div style="line-height:2.2">{html}</div>', unsafe_allow_html=True)


# ─── Opportunity Card ─────────────────────────────────────────────────────────

def render_opportunity_card(item: dict, category: str):
    logo = item.get("logo", "💼")
    skills_html = "".join(
        f'<span style="background:rgba(0,210,255,0.1);border:1px solid rgba(0,210,255,0.3);'
        f'color:#00d2ff;padding:2px 8px;border-radius:12px;font-size:0.72rem;margin:2px">{s}</span>'
        for s in item.get("skills", [])[:4]
    )

    extra = ""
    if category == "jobs":
        extra = f"<br>💰 {item.get('salary','N/A')}"
    elif category == "internships":
        extra = f"<br>💵 {item.get('stipend','N/A')} · ⏳ {item.get('duration','N/A')}"
    elif category in ("hackathons", "competitions"):
        extra = f"<br>🏆 Prize: {item.get('prize','N/A')} · 📡 {item.get('mode', item.get('eligibility',''))}"
    elif category == "scholarships":
        extra = f"<br>🎁 {item.get('amount','N/A')}"

    url = item.get("url", "#")
    st.markdown(f"""
    <div class="opp-card">
        <div style="display:flex;align-items:flex-start;gap:1rem">
            <span style="font-size:2rem">{logo}</span>
            <div style="flex:1">
                <a href="{url}" target="_blank" style="color:#00d2ff;text-decoration:none;font-weight:600;font-size:1rem">
                    {item.get('title','Unknown')}
                </a>
                <div style="color:#94a3b8;font-size:0.85rem;margin-top:0.2rem">
                    🏢 {item.get('company', item.get('organizer','Unknown'))}
                    &nbsp;·&nbsp; 📍 {item.get('location', item.get('mode','Online'))}
                    {extra}
                    &nbsp;·&nbsp; 📅 Deadline: {item.get('deadline','Rolling')}
                </div>
                <div style="margin-top:0.5rem">{skills_html}</div>
            </div>
            <div style="text-align:right;min-width:60px">
                <span style="background:rgba(0,230,118,0.15);border:1px solid rgba(0,230,118,0.3);
                             color:#00e676;padding:3px 10px;border-radius:12px;font-size:0.75rem">
                    {item.get('type', category.rstrip('s').title())}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Course Card ──────────────────────────────────────────────────────────────

def render_course_card(course: dict, skill: str = ""):
    platform = course.get("platform", "Unknown")
    badge_cls = {
        "Coursera": "badge-coursera", "Udemy": "badge-udemy",
        "edX": "badge-edx",           "YouTube": "badge-youtube"
    }.get(platform, "badge-coursera")

    stars = "★" * int(course.get("rating", 0)) + "☆" * (5 - int(course.get("rating", 0)))
    free  = "🆓 Free" if course.get("free") else "💰 Paid"

    st.markdown(f"""
    <div class="course-card">
        <div style="display:flex;align-items:flex-start;gap:0.75rem">
            <div style="flex:1">
                <a href="{course.get('url','#')}" target="_blank"
                   style="color:#e2e8f0;text-decoration:none;font-weight:600;font-size:0.9rem">
                    {course.get('title','Unknown Course')}
                </a>
                <div style="margin-top:0.4rem;display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
                    <span class="platform-badge {badge_cls}">{platform}</span>
                    <span style="color:#94a3b8;font-size:0.78rem">{free}</span>
                    <span style="color:#ffab40;font-size:0.78rem">{stars} {course.get('rating','')}</span>
                    <span style="color:#94a3b8;font-size:0.78rem">📚 {course.get('level','')}</span>
                    <span style="color:#94a3b8;font-size:0.78rem">⏱️ {course.get('duration','')}</span>
                </div>
                {f'<div style="color:#7b2ff7;font-size:0.75rem;margin-top:0.3rem">For skill: {skill}</div>' if skill else ''}
            </div>
            <a href="{course.get('url','#')}" target="_blank"
               style="background:linear-gradient(135deg,#00d2ff,#7b2ff7);color:white;
                      padding:6px 14px;border-radius:8px;text-decoration:none;font-size:0.8rem;
                      font-weight:600;white-space:nowrap;display:inline-block">
                Enroll →
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Progress Bar ─────────────────────────────────────────────────────────────

def render_progress_metric(label: str, value: float, max_val: float = 100, color: str = "#00d2ff"):
    pct = min(100, round((value / max(max_val, 1)) * 100))
    st.markdown(f"""
    <div style="margin-bottom:0.75rem">
        <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem">
            <span style="color:#e2e8f0;font-size:0.85rem">{label}</span>
            <span style="color:{color};font-weight:600;font-size:0.85rem">{pct}%</span>
        </div>
        <div style="background:rgba(255,255,255,0.07);border-radius:4px;height:6px">
            <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{color},{COLORS['secondary']});
                        border-radius:4px;transition:width 0.5s ease"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Empty State ──────────────────────────────────────────────────────────────

def render_empty_state(emoji: str, title: str, subtitle: str):
    st.markdown(f"""
    <div style="text-align:center;padding:4rem 2rem;opacity:0.6">
        <div style="font-size:3rem;margin-bottom:1rem">{emoji}</div>
        <h3 style="color:#e2e8f0">{title}</h3>
        <p style="color:#94a3b8">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)
