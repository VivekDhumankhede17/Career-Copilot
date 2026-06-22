"""
History Manager — SQLite-based session persistence and PDF report generation.
"""
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).parent.parent / "career_copilot.db"


def init_db():
    """Initialize the SQLite database schema."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT NOT NULL,
            name        TEXT,
            email       TEXT,
            filename    TEXT,
            target_role TEXT,
            profile     TEXT,
            gap_analysis TEXT,
            scores      TEXT,
            roadmap     TEXT,
            interview_results TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_session(
    name: str,
    email: str,
    filename: str,
    target_role: str,
    profile: dict,
    gap_analysis: dict,
    scores: dict,
    roadmap: dict = None,
    interview_results: list = None,
) -> int:
    """Save an analysis session to the database. Returns session ID."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    c    = conn.cursor()
    c.execute("""
        INSERT INTO sessions
        (created_at, name, email, filename, target_role, profile, gap_analysis, scores, roadmap, interview_results)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        name, email, filename, target_role,
        json.dumps(profile),
        json.dumps(gap_analysis),
        json.dumps(scores),
        json.dumps(roadmap) if roadmap else None,
        json.dumps(interview_results) if interview_results else None,
    ))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_all_sessions() -> list:
    """Retrieve all sessions as a list of dicts (summary view)."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    c    = conn.cursor()
    c.execute("""
        SELECT id, created_at, name, email, filename, target_role, scores
        FROM sessions ORDER BY created_at DESC
    """)
    rows = c.fetchall()
    conn.close()

    sessions = []
    for row in rows:
        try:
            scores = json.loads(row[6]) if row[6] else {}
            emp    = scores.get("employability", {}).get("employability_score", 0)
            skill  = scores.get("skill", {}).get("skill_match_score", 0)
            ats    = scores.get("ats", {}).get("ats_score", 0)
        except Exception:
            emp = skill = ats = 0

        sessions.append({
            "id":          row[0],
            "created_at":  row[1],
            "name":        row[2],
            "email":       row[3],
            "filename":    row[4],
            "target_role": row[5],
            "employability_score": emp,
            "skill_match_score":   skill,
            "ats_score":           ats,
        })
    return sessions


def get_session_by_id(session_id: int) -> dict:
    """Load full session data by ID."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    c    = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return {}

    cols = ["id", "created_at", "name", "email", "filename", "target_role",
            "profile", "gap_analysis", "scores", "roadmap", "interview_results"]
    data = dict(zip(cols, row))

    for key in ["profile", "gap_analysis", "scores", "roadmap", "interview_results"]:
        try:
            data[key] = json.loads(data[key]) if data[key] else {}
        except Exception:
            data[key] = {}

    return data


def delete_session(session_id: int):
    """Delete a session from the database."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def generate_pdf_report(session_data: dict) -> bytes:
    """
    Generate a comprehensive PDF career report.
    Returns PDF bytes.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import io

        buffer  = io.BytesIO()
        doc     = SimpleDocTemplate(buffer, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm,  bottomMargin=2*cm)
        styles  = getSampleStyleSheet()
        story   = []

        # ── Custom Styles ──────────────────────────────────────────────────
        title_style = ParagraphStyle('Title2', parent=styles['Title'],
                                     fontSize=22, textColor=colors.HexColor('#1a237e'),
                                     spaceAfter=6, alignment=TA_CENTER)
        h1_style    = ParagraphStyle('H1', parent=styles['Heading1'],
                                     fontSize=14, textColor=colors.HexColor('#1a237e'),
                                     spaceBefore=12, spaceAfter=4)
        h2_style    = ParagraphStyle('H2', parent=styles['Heading2'],
                                     fontSize=11, textColor=colors.HexColor('#283593'),
                                     spaceBefore=8, spaceAfter=3)
        body_style  = ParagraphStyle('Body2', parent=styles['Normal'],
                                     fontSize=9, leading=14)
        sub_style   = ParagraphStyle('Sub', parent=styles['Normal'],
                                     fontSize=8, textColor=colors.grey,
                                     alignment=TA_CENTER)

        # ── Header ────────────────────────────────────────────────────────
        name        = session_data.get("name", "Career Report")
        target_role = session_data.get("target_role", "Unknown Role")
        created_at  = session_data.get("created_at", "")[:10]

        story.append(Paragraph("🚀 Career Copilot AI", title_style))
        story.append(Paragraph(f"Career Analysis Report — {name}", h1_style))
        story.append(Paragraph(f"Target Role: {target_role} | Generated: {created_at}", sub_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a237e')))
        story.append(Spacer(1, 0.4*cm))

        # ── Scores Table ──────────────────────────────────────────────────
        scores = session_data.get("scores", {})
        emp    = scores.get("employability", {})
        skill  = scores.get("skill", {})
        ats    = scores.get("ats", {})
        intv   = scores.get("interview", {})

        story.append(Paragraph("📊 Career Scores", h1_style))
        score_data = [
            ["Metric",                   "Score", "Rating"],
            ["Overall Employability",    f"{emp.get('employability_score', 'N/A')}/100", emp.get('tier', '')],
            ["ATS Compatibility",        f"{ats.get('ats_score', 'N/A')}/100",           "ATS Ready" if ats.get('ats_score', 0) >= 70 else "Needs Work"],
            ["Skill Match",              f"{skill.get('skill_match_score', 'N/A')}/100", skill.get('tier', '')],
            ["Interview Readiness",      f"{intv.get('interview_readiness_score', 'N/A')}/100", intv.get('tier', 'Not Assessed')],
        ]
        score_table = Table(score_data, colWidths=[7*cm, 3*cm, 6*cm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR',   (0, 0), (-1, 0), colors.white),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8eaf6')]),
            ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#c5cae9')),
            ('ALIGN',       (1, 0), (-1, -1), 'CENTER'),
            ('PADDING',     (0, 0), (-1, -1), 6),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 0.4*cm))

        # ── Skill Gap ─────────────────────────────────────────────────────
        gap = session_data.get("gap_analysis", {})
        if gap:
            story.append(Paragraph("🎯 Skill Gap Analysis", h1_style))
            matched = gap.get("matched_required", [])
            missing = gap.get("missing_required", [])
            story.append(Paragraph(f"<b>Matched Skills ({len(matched)}):</b> {', '.join(matched[:10]) or 'None'}", body_style))
            story.append(Paragraph(f"<b>Missing Skills ({len(missing)}):</b> {', '.join(missing[:10]) or 'None'}", body_style))
            story.append(Spacer(1, 0.3*cm))

        # ── Roadmap ───────────────────────────────────────────────────────
        roadmap = session_data.get("roadmap", {})
        if roadmap and roadmap.get("phases"):
            story.append(Paragraph("🗺️ Learning Roadmap", h1_style))
            story.append(Paragraph(roadmap.get("overview", ""), body_style))
            story.append(Paragraph(f"<b>Total Duration:</b> {roadmap.get('total_duration', 'N/A')}", body_style))
            story.append(Spacer(1, 0.2*cm))
            for phase in roadmap["phases"][:4]:
                story.append(Paragraph(f"Phase {phase['phase_number']}: {phase['title']} ({phase['duration']})", h2_style))
                for goal in phase.get("goals", [])[:3]:
                    story.append(Paragraph(f"• {goal}", body_style))

        # ── Footer ────────────────────────────────────────────────────────
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Paragraph("Generated by Career Copilot AI | Your Personal Career Advisor", sub_style))

        doc.build(story)
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return b""
