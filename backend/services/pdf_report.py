from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Color palette
# --------------------------------------------------------------------------
BRAND_BLUE = colors.HexColor("#2563EB")
BRAND_DARK = colors.HexColor("#1E293B")
LIGHT_GRAY = colors.HexColor("#F8FAFC")
MID_GRAY = colors.HexColor("#94A3B8")
POSITIVE_GREEN = colors.HexColor("#16A34A")
NEUTRAL_AMBER = colors.HexColor("#D97706")
NEGATIVE_RED = colors.HexColor("#DC2626")
BORDER_COLOR = colors.HexColor("#E2E8F0")

SENTIMENT_COLORS = {
    "positive": POSITIVE_GREEN,
    "neutral": NEUTRAL_AMBER,
    "negative": NEGATIVE_RED,
}

# --------------------------------------------------------------------------
# Helper: build styles
# --------------------------------------------------------------------------

def _build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=26,
        textColor=BRAND_BLUE,
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    styles["subtitle"] = ParagraphStyle(
        "ReportSubtitle",
        fontName="Helvetica",
        fontSize=11,
        textColor=MID_GRAY,
        spaceAfter=2,
        alignment=TA_CENTER,
    )
    styles["section_heading"] = ParagraphStyle(
        "SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=BRAND_DARK,
        spaceBefore=16,
        spaceAfter=6,
    )
    styles["theme_name"] = ParagraphStyle(
        "ThemeName",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=BRAND_BLUE,
        spaceAfter=2,
    )
    styles["body"] = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=10,
        textColor=BRAND_DARK,
        spaceAfter=4,
        leading=14,
    )
    styles["quote"] = ParagraphStyle(
        "Quote",
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        leftIndent=12,
        spaceAfter=4,
        leading=13,
    )
    styles["small"] = ParagraphStyle(
        "Small",
        fontName="Helvetica",
        fontSize=8,
        textColor=MID_GRAY,
        spaceAfter=2,
    )
    styles["rec_title"] = ParagraphStyle(
        "RecTitle",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=BRAND_DARK,
        spaceAfter=2,
    )
    styles["rec_body"] = ParagraphStyle(
        "RecBody",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#475569"),
        spaceAfter=6,
        leading=14,
    )
    return styles


# --------------------------------------------------------------------------
# Sentiment badge table cell helper
# --------------------------------------------------------------------------

def _sentiment_badge(label: str) -> Table:
    color = SENTIMENT_COLORS.get(label, MID_GRAY)
    cell = Table([[label.capitalize()]], colWidths=[1.8 * cm], rowHeights=[0.5 * cm])
    cell.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROUNDEDCORNERS", [3, 3, 3, 3]),
            ]
        )
    )
    return cell


# --------------------------------------------------------------------------
# Section builders
# --------------------------------------------------------------------------

def _build_header(styles, total_feedback: int, num_themes: int, generated_at: str):
    elements = []
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Customer Feedback Analysis Report", styles["title"]))
    elements.append(Paragraph(f"Generated {generated_at}", styles["subtitle"]))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_BLUE))
    elements.append(Spacer(1, 0.4 * cm))

    # Summary stats table
    stat_data = [
        ["Total Feedback", "Themes Found", "Report Date"],
        [str(total_feedback), str(num_themes), generated_at.split(" ")[0]],
    ]
    stat_table = Table(stat_data, colWidths=[5 * cm, 5 * cm, 5 * cm])
    stat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, 1), 14),
                ("TEXTCOLOR", (0, 1), (-1, 1), BRAND_DARK),
                ("ROWBACKGROUNDS", (0, 1), (-1, 1), [LIGHT_GRAY]),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("ROWHEIGHT", (0, 0), (-1, -1), 0.7 * cm),
            ]
        )
    )
    elements.append(stat_table)
    elements.append(Spacer(1, 0.6 * cm))
    return elements


def _build_overall_sentiment(styles, overall_sentiment: Dict[str, int]):
    elements = []
    elements.append(Paragraph("Overall Sentiment Breakdown", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    elements.append(Spacer(1, 0.3 * cm))

    total = sum(overall_sentiment.values()) or 1
    rows = [["Sentiment", "Count", "Percentage"]]
    for label in ["positive", "neutral", "negative"]:
        count = overall_sentiment.get(label, 0)
        pct = f"{count / total * 100:.1f}%"
        rows.append([label.capitalize(), str(count), pct])

    tbl = Table(rows, colWidths=[5 * cm, 3 * cm, 3 * cm])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("ROWHEIGHT", (0, 0), (-1, -1), 0.6 * cm),
                # Color the sentiment labels
                ("TEXTCOLOR", (0, 1), (0, 1), POSITIVE_GREEN),
                ("TEXTCOLOR", (0, 2), (0, 2), NEUTRAL_AMBER),
                ("TEXTCOLOR", (0, 3), (0, 3), NEGATIVE_RED),
                ("FONTNAME", (0, 1), (0, 3), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(tbl)
    elements.append(Spacer(1, 0.5 * cm))
    return elements


def _build_themes_summary(styles, themes: List[Dict[str, Any]]):
    elements = []
    elements.append(Paragraph("Theme Summary", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    elements.append(Spacer(1, 0.3 * cm))

    rows = [["#", "Theme", "Mentions", "%", "Pos", "Neu", "Neg"]]
    for i, t in enumerate(themes, 1):
        counts = t.get("sentiment_counts", {})
        rows.append(
            [
                str(i),
                t["theme_name"],
                str(t["count"]),
                f"{t['percentage']}%",
                str(counts.get("positive", 0)),
                str(counts.get("neutral", 0)),
                str(counts.get("negative", 0)),
            ]
        )

    col_widths = [0.8 * cm, 5.5 * cm, 1.8 * cm, 1.5 * cm, 1.2 * cm, 1.2 * cm, 1.2 * cm]
    tbl = Table(rows, colWidths=col_widths)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("ROWHEIGHT", (0, 0), (-1, -1), 0.55 * cm),
                ("TEXTCOLOR", (4, 1), (4, -1), POSITIVE_GREEN),
                ("TEXTCOLOR", (5, 1), (5, -1), NEUTRAL_AMBER),
                ("TEXTCOLOR", (6, 1), (6, -1), NEGATIVE_RED),
            ]
        )
    )
    elements.append(tbl)
    elements.append(Spacer(1, 0.5 * cm))
    return elements


def _build_theme_details(styles, themes: List[Dict[str, Any]]):
    elements = []
    elements.append(PageBreak())
    elements.append(Paragraph("Theme Deep-Dives", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_BLUE))

    for t in themes:
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph(t["theme_name"], styles["theme_name"]))
        elements.append(
            Paragraph(
                f"{t['count']} mentions ({t['percentage']}%) — {t['description']}",
                styles["body"],
            )
        )

        quotes = t.get("quotes", [])
        if quotes:
            elements.append(Paragraph("Representative Quotes:", styles["small"]))
            for q in quotes:
                _c = SENTIMENT_COLORS.get(q.get("sentiment", "neutral"), MID_GRAY)
                sentiment_hex = "#{:06x}".format(int(_c.hexval(), 16))
                bullet = f'<font color="{sentiment_hex}" size="9">\u25cf</font>  "{q["text"]}"'

        elements.append(HRFlowable(width="100%", thickness=0.3, color=BORDER_COLOR))

    elements.append(Spacer(1, 0.5 * cm))
    return elements


def _build_recommendations(styles, recommendations: List[Dict[str, Any]]):
    elements = []
    elements.append(PageBreak())
    elements.append(Paragraph("What to Fix First", styles["section_heading"]))
    elements.append(
        Paragraph(
            "Prioritized recommendations based on frequency and negative sentiment.",
            styles["body"],
        )
    )
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    elements.append(Spacer(1, 0.3 * cm))

    for rec in recommendations:
        priority = rec.get("priority", "?")
        title = rec.get("title", "")
        description = rec.get("description", "")

        # Priority badge + title row
        badge_data = [[f"#{priority}", title]]
        badge_tbl = Table(badge_data, colWidths=[1.2 * cm, 14 * cm])
        badge_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), BRAND_BLUE),
                    ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                    ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (0, 0), 9),
                    ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (1, 0), (1, 0), 10),
                    ("TEXTCOLOR", (1, 0), (1, 0), BRAND_DARK),
                    ("ALIGN", (0, 0), (0, 0), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWHEIGHT", (0, 0), (-1, -1), 0.65 * cm),
                    ("LEFTPADDING", (1, 0), (1, 0), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ]
            )
        )
        elements.append(badge_tbl)
        elements.append(Paragraph(description, styles["rec_body"]))
        elements.append(Spacer(1, 0.1 * cm))

    return elements


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------

def generate_pdf_report(
    themes: List[Dict[str, Any]],
    overall_sentiment: Dict[str, int],
    recommendations: List[Dict[str, Any]],
    total_feedback: int,
) -> bytes:
    """
    Build and return a PDF report as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Customer Feedback Analysis Report",
        author="Feedback Theme Extractor",
    )

    styles = _build_styles()
    generated_at = datetime.now().strftime("%B %d, %Y %H:%M")

    story = []
    story += _build_header(styles, total_feedback, len(themes), generated_at)
    story += _build_overall_sentiment(styles, overall_sentiment)
    story += _build_themes_summary(styles, themes)
    story += _build_theme_details(styles, themes)
    story += _build_recommendations(styles, recommendations)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()