"""
PDF Report Generator for Glowup Coach
Dark-mode premium report with 4-week glowup strategies and highlighted techniques.
"""
from fpdf import FPDF, XPos, YPos
from datetime import datetime
import os


# --- Dark Mode Color Palette --------------------------------------------------
BG_DARK      = (10,  13,  26)     # near-black page background
BG_CARD      = (18,  22,  42)     # card/section background
BG_HEADER    = (12,  15,  32)     # header bar
ACCENT       = (108, 99,  255)    # indigo
ACCENT_MALE  = (56,  189, 248)    # sky blue
ACCENT_FEMALE= (244, 114, 182)    # pink
GREEN        = (52,  211, 153)    # success
AMBER        = (251, 191, 36)     # warning
RED          = (248, 113, 113)    # danger
PURPLE       = (167, 139, 250)    # light purple for highlights
WHITE        = (255, 255, 255)
TEXT_1       = (226, 232, 240)    # primary text
TEXT_2       = (148, 163, 184)    # secondary text
TEXT_3       = (100, 116, 139)    # muted text
BORDER       = (30,  36,  60)     # subtle border
HIGHLIGHT_BG = (25,  30,  55)     # highlight card bg


def score_color(score: float):
    if score >= 80: return GREEN
    if score >= 60: return AMBER
    return RED


def score_label(score: float) -> str:
    if score >= 92: return "Elite"
    if score >= 82: return "Very Attractive"
    if score >= 70: return "Attractive"
    if score >= 55: return "Above Average"
    if score >= 40: return "Average"
    return "Needs Work"


class GlowupPDF(FPDF):
    def __init__(self, username: str, gender: str):
        super().__init__()
        self.username = username
        self.gender   = gender
        self.accent   = (
            ACCENT_MALE   if gender == "male"   else
            ACCENT_FEMALE if gender == "female" else
            ACCENT
        )
        self.set_margins(16, 28, 16)
        self.set_auto_page_break(auto=True, margin=22)

    def header(self):
        # Full-width dark header bar
        self.set_fill_color(*BG_HEADER)
        self.rect(0, 0, 210, 24, "F")
        # Accent bottom strip
        self.set_fill_color(*self.accent)
        self.rect(0, 24, 210, 2, "F")

        # Logo
        self.set_xy(16, 6)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*WHITE)
        self.cell(70, 10, "GLOWUP COACH", new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Tag line
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*TEXT_3)
        self.set_xy(86, 9)
        self.cell(50, 5, "AI Facial Analysis Report")

        # Date right
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*TEXT_2)
        date_str = datetime.now().strftime("%d %b %Y  |  %I:%M %p")
        self.set_xy(130, 8)
        self.cell(64, 8, date_str, align="R")

        self.ln(4)

    def footer(self):
        self.set_y(-18)
        self.set_fill_color(*BG_HEADER)
        self.rect(0, self.get_y() - 2, 210, 22, "F")
        # Accent top strip
        self.set_fill_color(*self.accent)
        self.rect(0, self.get_y() - 2, 210, 1.2, "F")
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*TEXT_3)
        self.set_y(self.get_y() + 1)
        self.cell(0, 5, "Cosmetic guidance only - Not medical advice. Consult a qualified healthcare professional before any decisions.", align="C")
        self.ln(4)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*TEXT_3)
        self.cell(0, 4, f"Page {self.page_no()}  |  Glowup Coach  |  {self.username}", align="C")

    def dark_page(self):
        """Fill current page background with dark color."""
        self.set_fill_color(*BG_DARK)
        self.rect(0, 0, 210, 297, "F")

    def section_title(self, title: str, gap_before: int = 8):
        self.ln(gap_before)
        y = self.get_y()
        # Accent left bar
        self.set_fill_color(*self.accent)
        self.rect(16, y, 3.5, 8, "F")
        self.set_xy(22, y)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.accent)
        self.cell(0, 8, title.upper())
        self.ln(10)

    def dark_card(self, x, y, w, h, border_color=None):
        """Draw a dark card with optional colored border."""
        self.set_fill_color(*BG_CARD)
        if border_color:
            self.set_draw_color(*border_color)
            self.set_line_width(0.6)
            self.rect(x, y, w, h, "DF")
        else:
            self.rect(x, y, w, h, "F")

    def highlight_pill(self, x, y, text, color):
        """Draw a colored highlight pill/badge."""
        self.set_fill_color(*color)
        self.rect(x, y, 3, 5.5, "F")
        self.set_xy(x + 5, y)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*color)
        self.cell(0, 5.5, text)
        self.ln(6)


def generate_pdf(
    username: str,
    gender: str,
    total_score: float,
    feature_scores: dict,
    tips: list,
    frames_analyzed: int,
    rank: int | None,
    output_dir: str = ".",
) -> str:
    pdf = GlowupPDF(username=username, gender=gender)
    accent = pdf.accent

    # --- PAGE 1: HERO SCORE + FEATURE BREAKDOWN -------------------------------
    pdf.add_page()
    pdf.dark_page()

    # -- Hero score card --------------------------------------------------------
    pdf.ln(2)
    card_y = pdf.get_y()
    pdf.dark_card(16, card_y, 178, 60, border_color=accent)

    # Big score number
    pdf.set_xy(22, card_y + 8)
    pdf.set_font("Helvetica", "B", 58)
    pdf.set_text_color(*score_color(total_score))
    pdf.cell(55, 34, f"{total_score:.1f}", align="C")

    # /100
    pdf.set_xy(77, card_y + 26)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*TEXT_2)
    pdf.cell(18, 8, "/100")

    # Verdict
    pdf.set_xy(22, card_y + 44)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*accent)
    pdf.cell(55, 8, score_label(total_score), align="C")

    # Right info block
    info_x = 112
    info_y = card_y + 9
    info_rows = [
        ("User",    username),
        ("Gender",  gender.replace("_", " ").title()),
        ("Frames",  f"{frames_analyzed} analyzed"),
        ("Rank",    f"Global #{rank}" if rank else "N/A"),
        ("Date",    datetime.now().strftime("%d %b %Y")),
    ]
    for label, val in info_rows:
        pdf.set_xy(info_x, info_y)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*TEXT_3)
        pdf.cell(28, 5, label.upper())
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*TEXT_1)
        pdf.cell(52, 5, val)
        info_y += 9.5

    pdf.ln(46)

    # -- Feature Breakdown: Current vs Potential --------------------------------
    pdf.section_title("Feature Scores: Now vs After Glowup")

    FEAT_COLORS = {
        "Symmetry":  (  0, 212, 255),  # cyan
        "Eyes":      (168,  85, 247),  # violet
        "Eyebrows":  (245, 158,  11),  # amber
        "Nose":      (249, 115,  22),  # orange
        "Lips":      (236,  72, 153),  # pink
        "Cheeks":    ( 16, 185, 129),  # emerald
        "Jawline":   ( 59, 130, 246),  # blue
        "Ears":      (139,  92, 246),  # purple
        "Forehead":  ( 20, 184, 166),  # teal
        "Chin":      (244,  63,  94),  # rose
    }
    POTENTIAL_GAINS = {
        "Symmetry": 12,  "Eyes": 20, "Eyebrows": 25, "Nose":  8,
        "Lips": 20, "Cheeks": 18, "Jawline": 25, "Ears":  6,
        "Forehead": 12, "Chin": 20,
    }

    BAR_X      = 16
    BAR_W      = 178
    LABEL_W    = 48
    SCORE_W    = 28   # now + gain
    BAR_FILL_W = BAR_W - LABEL_W - SCORE_W - 6

    for feature, score in feature_scores.items():
        if pdf.get_y() > 248:
            pdf.add_page()
            pdf.dark_page()

        row_y   = pdf.get_y()
        clr     = FEAT_COLORS.get(feature, ACCENT)
        gain    = POTENTIAL_GAINS.get(feature, 10)
        pot     = min(score + gain, 95)

        # Row background
        pdf.set_fill_color(16, 20, 40)
        pdf.rect(BAR_X, row_y, BAR_W, 11, "F")
        # Left color stripe per feature
        pdf.set_fill_color(*clr)
        pdf.rect(BAR_X, row_y, 2.5, 11, "F")

        # Feature label
        pdf.set_xy(BAR_X + 5, row_y + 2)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*clr)
        pdf.cell(LABEL_W - 5, 5, feature)

        # Bar track area
        track_x = BAR_X + LABEL_W
        track_y = row_y + 2.5

        # Potential bar (background ghost)
        pot_fill = (pot / 100.0) * BAR_FILL_W
        pdf.set_fill_color(clr[0]//5, clr[1]//5, clr[2]//5)
        pdf.rect(track_x, track_y, BAR_FILL_W, 3, "F")
        pdf.set_fill_color(clr[0]//2, clr[1]//2, clr[2]//2)
        pdf.rect(track_x, track_y, max(pot_fill, 0.5), 3, "F")

        # Current bar (solid, on top)
        cur_fill = (score / 100.0) * BAR_FILL_W
        pdf.set_fill_color(*clr)
        pdf.rect(track_x, track_y + 3.5, max(cur_fill, 0.5), 2.5, "F")

        # Track labels
        pdf.set_xy(track_x, track_y + 7)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(*TEXT_3)
        pdf.cell(BAR_FILL_W // 2, 3, "potential", align="L")
        pdf.set_text_color(*clr)
        pdf.cell(BAR_FILL_W // 2, 3, "current", align="R")

        # Score values: now -> potential
        score_x = track_x + BAR_FILL_W + 3
        pdf.set_xy(score_x, row_y + 1.5)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*clr)
        pdf.cell(SCORE_W - 14, 4.5, f"{score:.0f}", align="R")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*TEXT_3)
        pdf.cell(4, 4.5, ">")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(clr[0]//2 + 80, clr[1]//2 + 80, clr[2]//2 + 80)
        pdf.cell(10, 4.5, f"{pot:.0f}")
        pdf.set_xy(score_x, row_y + 6.5)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(*TEXT_3)
        pdf.cell(SCORE_W, 3.5, f"+{gain} potential", align="C")

        pdf.ln(12)


    # --- PAGE 2: GLOWUP TECHNIQUES + PERSONALIZED TIPS ------------------------
    pdf.add_page()
    pdf.dark_page()

    pdf.section_title("Highlighted Glowup Techniques", gap_before=4)

    # Filter tips that have a highlight technique
    tips_with_highlight = [t for t in tips if t.get("highlight")]

    if tips_with_highlight:
        for tip in tips_with_highlight[:8]:
            if pdf.get_y() > 245:
                pdf.add_page()
                pdf.dark_page()

            sev   = tip.get("severity", "low")
            clr   = RED if sev == "high" else AMBER if sev == "medium" else GREEN
            feat  = tip.get("feature", "")
            high  = tip.get("highlight", "")
            tipTx = tip.get("tip", "")

            ty = pdf.get_y()

            # Card background
            pdf.set_fill_color(*HIGHLIGHT_BG)
            pdf.rect(16, ty, 178, 22, "F")
            # Severity left stripe
            pdf.set_fill_color(*clr)
            pdf.rect(16, ty, 3, 22, "F")

            # Feature name + severity badge
            pdf.set_xy(22, ty + 2)
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.set_text_color(*WHITE)
            pdf.cell(60, 5.5, feat)

            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*clr)
            pdf.cell(0, 5.5, f"  [{sev.upper()}]")

            # Highlight technique (purple star)
            pdf.set_xy(22, ty + 8)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*PURPLE)
            pdf.cell(8, 5, "KEY:")
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*PURPLE)
            pdf.cell(0, 5, high)

            # Tip text
            pdf.set_xy(22, ty + 14.5)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*TEXT_2)
            pdf.multi_cell(170, 4.2, tipTx)

            pdf.ln(4)
    else:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GREEN)
        pdf.cell(0, 8, "All features are in excellent shape. Keep up the great work!", align="C")
        pdf.ln(10)

    # --- PAGE 3: 4-WEEK GLOWUP STRATEGY ---------------------------------------
    pdf.add_page()
    pdf.dark_page()

    pdf.section_title("4-Week Glowup Strategy Plan", gap_before=4)

    # Intro card
    intro_y = pdf.get_y()
    pdf.set_fill_color(*HIGHLIGHT_BG)
    pdf.rect(16, intro_y, 178, 14, "F")
    pdf.set_fill_color(*PURPLE)
    pdf.rect(16, intro_y, 3, 14, "F")
    pdf.set_xy(22, intro_y + 2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*PURPLE)
    pdf.cell(0, 5, "Your personalized 28-day transformation roadmap")
    pdf.set_xy(22, intro_y + 8)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*TEXT_2)
    pdf.cell(0, 5, f"Based on your {gender.replace('_', ' ')} profile and areas scoring below 85/100")
    pdf.ln(18)

    WEEK_COLORS = {
        "week1": (99,  102, 241),   # indigo
        "week2": (56,  189, 248),   # sky
        "week3": (52,  211, 153),   # green
        "week4": (244, 114, 182),   # pink
    }
    WEEK_LABELS = {
        "week1": "WEEK 1  Days 1-7",
        "week2": "WEEK 2  Days 8-14",
        "week3": "WEEK 3  Days 15-21",
        "week4": "WEEK 4  Days 22-28",
    }

    # Only show 4-week plans for low-scoring features
    low_tips = [t for t in tips if t.get("week1") and t.get("score", 100) < 85][:6]

    for tip in low_tips:
        if pdf.get_y() > 240:
            pdf.add_page()
            pdf.dark_page()

        feat   = tip.get("feature", "")
        score  = tip.get("score", 0)
        clr    = score_color(score)

        # Feature header
        fh_y = pdf.get_y()
        pdf.set_fill_color(22, 27, 50)
        pdf.rect(16, fh_y, 178, 8, "F")
        pdf.set_fill_color(*clr)
        pdf.rect(16, fh_y, 3, 8, "F")
        pdf.set_xy(22, fh_y + 1.5)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*clr)
        pdf.cell(80, 5, f"{feat}  ({score:.0f}/100)")
        pdf.ln(9)

        # 4 week rows
        for week_key in ("week1", "week2", "week3", "week4"):
            week_text = tip.get(week_key, "")
            if not week_text:
                continue
            if pdf.get_y() > 255:
                pdf.add_page()
                pdf.dark_page()

            wclr   = WEEK_COLORS[week_key]
            wlabel = WEEK_LABELS[week_key]

            wy = pdf.get_y()
            pdf.set_fill_color(18, 22, 42)
            pdf.rect(22, wy, 172, 12, "F")
            pdf.set_fill_color(*wclr)
            pdf.rect(22, wy, 2.5, 12, "F")

            pdf.set_xy(27, wy + 1.2)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*wclr)
            pdf.cell(52, 4.5, wlabel)
            pdf.ln(5)
            pdf.set_x(27)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*TEXT_2)
            pdf.multi_cell(161, 4, week_text)
            pdf.ln(2)

        pdf.ln(4)

    # --- PAGE 4: DISCLAIMER ---------------------------------------------------
    pdf.add_page()
    pdf.dark_page()

    pdf.section_title("Important Medical Disclaimer", gap_before=4)

    disc_y = pdf.get_y()
    # Red border card
    pdf.set_fill_color(28, 18, 18)
    pdf.set_draw_color(*RED)
    pdf.set_line_width(0.6)
    pdf.rect(16, disc_y, 178, 150, "DF")
    pdf.set_fill_color(*RED)
    pdf.rect(16, disc_y, 178, 4, "F")

    pdf.set_xy(20, disc_y + 8)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*RED)
    pdf.cell(0, 6, "GLOWUP COACH  -  COSMETIC GUIDANCE ONLY")
    pdf.ln(8)
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*TEXT_2)

    disclaimer_paragraphs = [
        (
            "This report is generated by an automated facial geometry analysis system. "
            "It is intended for EDUCATIONAL and COSMETIC GUIDANCE purposes ONLY. "
            "It does NOT constitute medical advice, diagnosis, or treatment."
        ),
        (
            "The scores and ratings in this report are based on mathematical analysis of facial "
            "landmark proportions (symmetry, proportions, geometry) and do NOT reflect any medical "
            "assessment of your health, beauty, or worth as a person."
        ),
        (
            "BEFORE making any decisions regarding cosmetic procedures, dermatological treatments, "
            "or surgical interventions, you MUST consult a qualified and licensed professional:\n"
            "  - Dermatologist  |  Plastic or Cosmetic Surgeon  |  Maxillofacial Surgeon\n"
            "  - Ophthalmologist (for eye-related concerns)  |  General Healthcare Professional"
        ),
        (
            "Results may vary based on lighting conditions, camera angle, facial expression, "
            "and the inherent limitations of computer vision technology. This report should NOT "
            "be used as a basis for comparison with others or as a measure of self-worth."
        ),
        (
            "All facial imagery captured during analysis is processed entirely in real-time "
            "in your browser and is NEVER stored, transmitted, or shared. Only numerical "
            "metrics are retained with your explicit consent."
        ),
    ]

    for para in disclaimer_paragraphs:
        pdf.set_x(20)
        pdf.multi_cell(168, 5.2, para)
        pdf.ln(4)

    # --- Save with unique timestamp (never overwrite) -------------------------
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
    filename  = f"glowup_report_{username}_{timestamp}.pdf"
    filepath  = os.path.join(output_dir, filename)
    pdf.output(filepath)
    return filepath
