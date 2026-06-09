"""
PDF Report Generator for Glowup Coach
Dark-mode premium report with 4-week glowup strategies and highlighted techniques.
"""
from __future__ import annotations

import os
from datetime import datetime
from fpdf import FPDF, XPos, YPos


# ── Dark Mode Color Palette ────────────────────────────────────────────────────
BG_DARK       = (10,  13,  26)
BG_CARD       = (18,  22,  42)
BG_HEADER     = (12,  15,  32)
BG_HIGHLIGHT  = (25,  30,  55)
ACCENT        = (108, 99,  255)
ACCENT_MALE   = (56,  189, 248)
ACCENT_FEMALE = (244, 114, 182)
GREEN         = (52,  211, 153)
AMBER         = (251, 191, 36)
RED           = (248, 113, 113)
PURPLE        = (167, 139, 250)
WHITE         = (255, 255, 255)
TEXT_1        = (226, 232, 240)
TEXT_2        = (148, 163, 184)
TEXT_3        = (100, 116, 139)
BORDER        = (30,  36,  60)

FEAT_COLORS: dict[str, tuple[int, int, int]] = {
    "Symmetry": (  0, 212, 255),
    "Eyes":     (168,  85, 247),
    "Eyebrows": (245, 158,  11),
    "Nose":     (249, 115,  22),
    "Lips":     (236,  72, 153),
    "Cheeks":   ( 16, 185, 129),
    "Jawline":  ( 59, 130, 246),
    "Ears":     (139,  92, 246),
    "Forehead": ( 20, 184, 166),
    "Chin":     (244,  63,  94),
}
POTENTIAL_GAINS: dict[str, int] = {
    "Symmetry": 12, "Eyes": 20, "Eyebrows": 25, "Nose":  8,
    "Lips":     20, "Cheeks": 18, "Jawline": 25, "Ears":  6,
    "Forehead": 12, "Chin": 20,
}
WEEK_COLORS = {
    "week1": (99,  102, 241),
    "week2": (56,  189, 248),
    "week3": (52,  211, 153),
    "week4": (244, 114, 182),
}
WEEK_LABELS = {
    "week1": "WEEK 1  |  Days 1-7",
    "week2": "WEEK 2  |  Days 8-14",
    "week3": "WEEK 3  |  Days 15-21",
    "week4": "WEEK 4  |  Days 22-28",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def score_color(score: float) -> tuple[int, int, int]:
    if score >= 80:
        return GREEN
    if score >= 60:
        return AMBER
    return RED


def score_label(score: float) -> str:
    if score >= 92: return "Elite"
    if score >= 82: return "Very Attractive"
    if score >= 70: return "Attractive"
    if score >= 55: return "Above Average"
    if score >= 40: return "Average"
    return "Needs Work"


def clamp(v: int) -> int:
    return max(0, min(255, v))


def dim(c: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """Return a dimmed version of a color (factor 0.0-1.0)."""
    return (clamp(int(c[0] * factor)), clamp(int(c[1] * factor)), clamp(int(c[2] * factor)))


# ── PDF Class ──────────────────────────────────────────────────────────────────

class GlowupPDF(FPDF):
    def __init__(self, username: str, gender: str):
        super().__init__()
        self.username = username
        self.gender   = gender
        self.accent: tuple[int, int, int] = (
            ACCENT_MALE   if gender == "male"   else
            ACCENT_FEMALE if gender == "female" else
            ACCENT
        )
        self.set_margins(16, 30, 16)
        self.set_auto_page_break(auto=True, margin=24)

    # -- Called automatically on every page ----------------------------------
    def header(self) -> None:
        # Dark background must be drawn first, before header content
        self.set_fill_color(*BG_DARK)
        self.rect(0, 0, 210, 297, style="F")

        # Header bar
        self.set_fill_color(*BG_HEADER)
        self.rect(0, 0, 210, 22, style="F")
        # Accent strip under header
        self.set_fill_color(*self.accent)
        self.rect(0, 22, 210, 1.5, style="F")

        self.set_xy(16, 5)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*WHITE)
        self.cell(60, 8, "GLOWUP COACH", new_x=XPos.RIGHT, new_y=YPos.TOP)

        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*TEXT_3)
        self.set_xy(78, 8)
        self.cell(40, 5, "AI Facial Analysis Report")

        date_str = datetime.now().strftime("%d %b %Y  |  %I:%M %p")
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*TEXT_2)
        self.set_xy(130, 7)
        self.cell(64, 8, date_str, align="R")

    def footer(self) -> None:
        self.set_y(-16)
        self.set_fill_color(*BG_HEADER)
        self.rect(0, self.get_y() - 1, 210, 20, "F")
        self.set_fill_color(*self.accent)
        self.rect(0, self.get_y() - 1, 210, 1, "F")
        self.set_font("Helvetica", "I", 6.5)
        self.set_text_color(*TEXT_3)
        self.set_y(self.get_y() + 2)
        self.cell(0, 4, "Cosmetic guidance only - Not medical advice. Consult a qualified healthcare professional.", align="C")
        self.ln(3.5)
        self.set_font("Helvetica", "", 6.5)
        self.cell(0, 4, f"Page {self.page_no()}  |  Glowup Coach  |  {self.username}", align="C")

    # -- Page helpers --------------------------------------------------------
    def fill_bg(self) -> None:
        """Redraw dark background (call after add_page if header() was already called)."""
        self.set_fill_color(*BG_DARK)
        self.rect(0, 0, 210, 297, style="F")
        # Redraw header over the bg
        self.set_fill_color(*BG_HEADER)
        self.rect(0, 0, 210, 22, style="F")
        self.set_fill_color(*self.accent)
        self.rect(0, 22, 210, 1.5, style="F")

    def new_dark_page(self) -> None:
        self.add_page()
        # fill_bg already called via header(); this is a no-op safety call

    # ── Reusable drawing helpers ─────────────────────────────────────────────
    def section_title(self, title: str, gap: int = 8) -> None:
        self.ln(gap)
        y = self.get_y()
        self.set_fill_color(*self.accent)
        self.rect(16, y, 3, 8, style="F")
        self.set_xy(22, y)
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(*self.accent)
        self.cell(0, 8, title.upper())
        self.ln(11)

    def card(self, x: float, y: float, w: float, h: float,
             bg: tuple = BG_CARD,
             border: tuple | None = None,
             lw: float = 0.5) -> None:
        self.set_fill_color(*bg)
        if border:
            self.set_draw_color(*border)
            self.set_line_width(lw)
            self.rect(x, y, w, h, style="DF")
        else:
            self.rect(x, y, w, h, style="F")


# ── Report Builder ─────────────────────────────────────────────────────────────

def _page1_hero(pdf: GlowupPDF, username: str, gender: str,
                total_score: float, frames_analyzed: int, rank: int | None) -> None:
    """Page 1 - hero score card + feature bar chart."""
    pdf.new_dark_page()
    accent = pdf.accent

    # ── Hero score card ───────────────────────────────────────────────────────
    pdf.ln(2)
    cy = pdf.get_y()
    pdf.card(16, cy, 178, 58, border=accent, lw=0.7)

    # Big score
    pdf.set_xy(22, cy + 6)
    pdf.set_font("Helvetica", "B", 54)
    pdf.set_text_color(*score_color(total_score))
    pdf.cell(52, 32, f"{total_score:.1f}", align="C")

    # /100
    pdf.set_xy(75, cy + 24)
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(*TEXT_2)
    pdf.cell(16, 8, "/100")

    # Verdict
    pdf.set_xy(22, cy + 42)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*accent)
    pdf.cell(52, 8, score_label(total_score), align="C")

    # Right info block
    info_x, info_y = 112, cy + 7
    rows = [
        ("User",    username),
        ("Gender",  gender.replace("_", " ").title()),
        ("Frames",  f"{frames_analyzed} analyzed"),
        ("Rank",    f"Global #{rank}" if rank else "Unranked"),
        ("Date",    datetime.now().strftime("%d %b %Y")),
    ]
    for label, val in rows:
        pdf.set_xy(info_x, info_y)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*TEXT_3)
        pdf.cell(26, 5, label.upper())
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*TEXT_1)
        pdf.cell(52, 5, val)
        info_y += 9

    pdf.ln(44)


def _page1_features(pdf: GlowupPDF, feature_scores: dict[str, float]) -> None:
    """Render feature score bars below the hero card."""
    pdf.section_title("Feature Scores: Now -> After Glowup")

    BAR_X      = 16
    BAR_W      = 178
    LABEL_W    = 46
    SCORE_W    = 30
    FILL_W     = BAR_W - LABEL_W - SCORE_W - 4   # ~98

    for feature, score in feature_scores.items():
        if pdf.get_y() > 248:
            pdf.new_dark_page()

        ry  = pdf.get_y()
        clr = FEAT_COLORS.get(feature, ACCENT)
        gain = POTENTIAL_GAINS.get(feature, 10)
        pot  = min(score + gain, 95.0)

        # Row bg
        pdf.set_fill_color(16, 20, 40)
        pdf.rect(BAR_X, ry, BAR_W, 11, style="F")
        # Left color stripe
        pdf.set_fill_color(*clr)
        pdf.rect(BAR_X, ry, 2.5, 11, style="F")

        # Feature label
        pdf.set_xy(BAR_X + 5, ry + 2)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*clr)
        pdf.cell(LABEL_W - 5, 5, feature)

        # Track area
        tx = BAR_X + LABEL_W
        ty = ry + 2.5

        # Potential (ghost) bar
        pdf.set_fill_color(*dim(clr, 0.18))
        pdf.rect(tx, ty, FILL_W, 3, style="F")
        pot_px = (pot / 100.0) * FILL_W
        pdf.set_fill_color(*dim(clr, 0.45))
        pdf.rect(tx, ty, max(pot_px, 0.5), 3, "F")

        # Current bar
        cur_px = (score / 100.0) * FILL_W
        pdf.set_fill_color(*clr)
        pdf.rect(tx, ty + 3.5, max(cur_px, 0.5), 2.5, "F")

        # Track labels
        pdf.set_xy(tx, ty + 7)
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(*TEXT_3)
        pdf.cell(FILL_W // 2, 3, "potential", align="L")
        pdf.set_text_color(*clr)
        pdf.cell(FILL_W // 2, 3, "current", align="R")

        # Score: now -> potential
        sx = tx + FILL_W + 3
        pdf.set_xy(sx, ry + 1.5)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*clr)
        pdf.cell(12, 4.5, f"{score:.0f}", align="R")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*TEXT_3)
        pdf.cell(4, 4.5, "->")
        pdf.set_font("Helvetica", "B", 8)
        pot_clr = dim(clr, 0.5)
        pdf.set_text_color(clamp(pot_clr[0]+80), clamp(pot_clr[1]+80), clamp(pot_clr[2]+80))
        pdf.cell(10, 4.5, f"{pot:.0f}")

        pdf.set_xy(sx, ry + 6.5)
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(*TEXT_3)
        pdf.cell(SCORE_W, 3, f"+{gain} gain", align="C")

        pdf.ln(12)


def _page2_techniques(pdf: GlowupPDF, tips: list[dict]) -> None:
    """Page 2 - highlighted glowup techniques."""
    pdf.new_dark_page()
    pdf.section_title("Top Glowup Techniques", gap=4)

    highlights = [t for t in tips if t.get("highlight")]
    if not highlights:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GREEN)
        pdf.cell(0, 8, "All features are performing excellently!", align="C")
        return

    for tip in highlights[:8]:
        if pdf.get_y() > 245:
            pdf.new_dark_page()

        sev   = tip.get("severity", "low")
        clr   = RED if sev == "high" else AMBER if sev == "medium" else GREEN
        feat  = tip.get("feature", "")
        high  = tip.get("highlight", "")
        text  = tip.get("tip", "")

        ty = pdf.get_y()
        pdf.card(16, ty, 178, 24, bg=BG_HIGHLIGHT)
        # Severity stripe
        pdf.set_fill_color(*clr)
        pdf.rect(16, ty, 3, 24, style="F")

        # Feature name + severity
        pdf.set_xy(22, ty + 2.5)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*WHITE)
        pdf.cell(65, 5, feat)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*clr)
        pdf.cell(10, 5, f"[{sev.upper()}]")

        # Key technique
        pdf.set_xy(22, ty + 9)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*PURPLE)
        pdf.cell(10, 5, "* KEY:")
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.cell(0, 5, high)

        # Tip text
        pdf.set_xy(22, ty + 15.5)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*TEXT_2)
        pdf.multi_cell(168, 4, text)

        pdf.ln(5)


def _page3_weekly_plan(pdf: GlowupPDF, tips: list[dict], gender: str) -> None:
    """Page 3 - 4-week transformation plan."""
    pdf.new_dark_page()
    pdf.section_title("4-Week Glowup Roadmap", gap=4)

    # Intro card
    iy = pdf.get_y()
    pdf.card(16, iy, 178, 14, bg=BG_HIGHLIGHT)
    pdf.set_fill_color(*PURPLE)
    pdf.rect(16, iy, 3, 14, style="F")
    pdf.set_xy(22, iy + 2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*PURPLE)
    pdf.cell(0, 5, "Your personalised 28-day transformation roadmap")
    pdf.set_xy(22, iy + 8)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*TEXT_2)
    pdf.cell(0, 5, f"Based on your {gender.replace('_', ' ')} profile - features scoring below 85/100")
    pdf.ln(18)

    low_tips = [t for t in tips if t.get("week1") and t.get("score", 100) < 85][:6]

    for tip in low_tips:
        if pdf.get_y() > 240:
            pdf.new_dark_page()

        feat  = tip.get("feature", "")
        score = tip.get("score", 0)
        clr   = score_color(score)

        # Feature header
        fhy = pdf.get_y()
        pdf.card(16, fhy, 178, 8, bg=(22, 27, 50))
        pdf.set_fill_color(*clr)
        pdf.rect(16, fhy, 3, 8, style="F")
        pdf.set_xy(22, fhy + 1.5)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*clr)
        pdf.cell(80, 5, f"{feat}  ({score:.0f}/100)")
        pdf.ln(10)

        for wk in ("week1", "week2", "week3", "week4"):
            wtext = tip.get(wk, "")
            if not wtext:
                continue
            if pdf.get_y() > 255:
                pdf.new_dark_page()

            wclr   = WEEK_COLORS[wk]
            wlabel = WEEK_LABELS[wk]

            wy = pdf.get_y()
            pdf.card(22, wy, 172, 13, bg=BG_CARD)
            pdf.set_fill_color(*wclr)
            pdf.rect(22, wy, 2.5, 13, style="F")

            pdf.set_xy(28, wy + 1.5)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*wclr)
            pdf.cell(55, 4, wlabel)
            pdf.ln(5)
            pdf.set_x(28)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*TEXT_2)
            pdf.multi_cell(160, 4, wtext)
            pdf.ln(2)

        pdf.ln(5)


def _page4_disclaimer(pdf: GlowupPDF) -> None:
    """Page 4 - medical disclaimer."""
    pdf.new_dark_page()
    pdf.section_title("Important Medical Disclaimer", gap=4)

    dy = pdf.get_y()
    pdf.set_fill_color(28, 18, 18)
    pdf.set_draw_color(*RED)
    pdf.set_line_width(0.6)
    pdf.rect(16, dy, 178, 155, style="DF")
    pdf.set_fill_color(*RED)
    pdf.rect(16, dy, 178, 4, style="F")

    pdf.set_xy(20, dy + 9)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*RED)
    pdf.cell(0, 6, "GLOWUP COACH - COSMETIC GUIDANCE ONLY")
    pdf.ln(9)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*TEXT_2)
    paragraphs = [
        (
            "This report is generated by an automated facial geometry analysis system. "
            "It is intended for EDUCATIONAL and COSMETIC GUIDANCE purposes ONLY. "
            "It does NOT constitute medical advice, diagnosis, or treatment."
        ),
        (
            "The scores and ratings are based on mathematical analysis of facial landmark "
            "proportions (symmetry, ratios, geometry) and do NOT reflect any medical assessment "
            "of your health, beauty, or worth as a person."
        ),
        (
            "BEFORE making any decisions regarding cosmetic procedures, dermatological treatments, "
            "or surgical interventions, you MUST consult a qualified and licensed professional:\n"
            "  - Dermatologist  |  Plastic or Cosmetic Surgeon  |  Maxillofacial Surgeon\n"
            "  - Ophthalmologist (eye concerns)  |  General Healthcare Professional"
        ),
        (
            "Results may vary based on lighting, camera angle, facial expression, and the "
            "inherent limitations of computer vision. This report must NOT be used as a basis "
            "for comparison with others or as a measure of self-worth."
        ),
        (
            "All facial imagery is processed entirely in real-time and is NEVER stored, "
            "transmitted, or shared. Only anonymised numerical metrics are retained with "
            "your explicit consent."
        ),
    ]
    for para in paragraphs:
        pdf.set_x(20)
        pdf.multi_cell(168, 5.2, para)
        pdf.ln(4)


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_pdf(
    username: str,
    gender: str,
    total_score: float,
    feature_scores: dict[str, float],
    tips: list[dict],
    frames_analyzed: int,
    rank: int | None,
    output_dir: str = ".",
) -> str:
    """
    Generate a dark-mode PDF report and return its absolute filepath.
    """
    pdf = GlowupPDF(username=username, gender=gender)

    _page1_hero(pdf, username, gender, total_score, frames_analyzed, rank)
    _page1_features(pdf, feature_scores)
    _page2_techniques(pdf, tips)
    _page3_weekly_plan(pdf, tips, gender)
    _page4_disclaimer(pdf)

    os.makedirs(output_dir, exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
    filename = f"glowup_report_{username}_{ts}.pdf"
    filepath = os.path.join(output_dir, filename)
    pdf.output(filepath)
    return filepath
