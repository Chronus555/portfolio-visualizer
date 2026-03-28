"""
PDF Report Generation Service using ReportLab.
Generates branded, professional portfolio analysis reports.
"""
import io
import logging
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

logger = logging.getLogger(__name__)

# Brand colors
BLUE      = colors.HexColor("#3b82f6")
DARK      = colors.HexColor("#0f172a")
GRAY      = colors.HexColor("#64748b")
LIGHT_BG  = colors.HexColor("#f8fafc")
BORDER    = colors.HexColor("#e2e8f0")
GREEN     = colors.HexColor("#10b981")
RED       = colors.HexColor("#ef4444")
WHITE     = colors.white


def build_styles():
    styles = getSampleStyleSheet()
    base = styles["Normal"]

    return {
        "title": ParagraphStyle(
            "title", parent=base,
            fontSize=22, fontName="Helvetica-Bold",
            textColor=DARK, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base,
            fontSize=11, fontName="Helvetica",
            textColor=GRAY, spaceAfter=16,
        ),
        "section_heading": ParagraphStyle(
            "section_heading", parent=base,
            fontSize=13, fontName="Helvetica-Bold",
            textColor=DARK, spaceBefore=16, spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body", parent=base,
            fontSize=9, fontName="Helvetica",
            textColor=GRAY, leading=14,
        ),
        "metric_label": ParagraphStyle(
            "metric_label", parent=base,
            fontSize=8, fontName="Helvetica",
            textColor=GRAY, spaceAfter=2,
        ),
        "metric_value": ParagraphStyle(
            "metric_value", parent=base,
            fontSize=16, fontName="Helvetica-Bold",
            textColor=DARK,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer", parent=base,
            fontSize=7, fontName="Helvetica",
            textColor=GRAY, leading=10,
        ),
        "table_header": ParagraphStyle(
            "table_header", parent=base,
            fontSize=8, fontName="Helvetica-Bold",
            textColor=WHITE,
        ),
        "table_cell": ParagraphStyle(
            "table_cell", parent=base,
            fontSize=8, fontName="Helvetica",
            textColor=DARK,
        ),
    }


TABLE_STYLE_BASE = TableStyle([
    ("BACKGROUND",    (0, 0), (-1, 0),  BLUE),
    ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
    ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
    ("FONTSIZE",      (0, 0), (-1, 0),  8),
    ("BOTTOMPADDING", (0, 0), (-1, 0),  6),
    ("TOPPADDING",    (0, 0), (-1, 0),  6),
    ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE",      (0, 1), (-1, -1), 8),
    ("TOPPADDING",    (0, 1), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_BG]),
    ("GRID",          (0, 0), (-1, -1), 0.5, BORDER),
    ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
])


def generate_backtest_report(data: Dict) -> bytes:
    """Generate a PDF report from backtest results."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Portfolio Backtest Report",
    )
    styles = build_styles()
    story = []

    # ── Header ─────────────────────────────────────────────────────────────────
    _add_header(story, styles,
                title="Portfolio Backtest Report",
                subtitle=f"Generated {datetime.now().strftime('%B %d, %Y')}")

    # ── Summary metrics ────────────────────────────────────────────────────────
    metrics = data.get("metrics", [])
    if metrics:
        story.append(Paragraph("Performance Summary", styles["section_heading"]))
        _add_metrics_table(story, metrics, styles)

    # ── Annual returns ─────────────────────────────────────────────────────────
    annual = data.get("annual_returns", [])
    if annual:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Annual Returns", styles["section_heading"]))
        _add_annual_returns_table(story, annual, metrics, styles)

    # ── Disclaimer ─────────────────────────────────────────────────────────────
    _add_disclaimer(story, styles)

    doc.build(story)
    return buffer.getvalue()


def generate_portfolio_report(report_type: str, title: str, data: Dict) -> bytes:
    """Generic report builder."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=title,
    )
    styles = build_styles()
    story = []

    _add_header(story, styles,
                title=title,
                subtitle=f"Generated {datetime.now().strftime('%B %d, %Y')}")

    # Render sections based on data keys
    for section_title, section_data in data.items():
        if isinstance(section_data, list) and section_data:
            story.append(Paragraph(section_title, styles["section_heading"]))
            if isinstance(section_data[0], dict):
                _add_generic_table(story, section_data, styles)

    _add_disclaimer(story, styles)
    doc.build(story)
    return buffer.getvalue()


# ── Helper builders ────────────────────────────────────────────────────────────

def _add_header(story, styles, title: str, subtitle: str):
    # Blue top bar
    story.append(HRFlowable(width="100%", thickness=3, color=BLUE, spaceAfter=12))

    story.append(Paragraph(title, styles["title"]))
    story.append(Paragraph(subtitle, styles["subtitle"]))
    story.append(Paragraph(
        "Portfolio Visualizer · Open-Source Portfolio Analysis",
        styles["body"]
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=8, spaceAfter=8))


def _add_metrics_table(story, metrics: List[Dict], styles):
    ROWS = [
        ("CAGR",          "cagr",               True,  False),
        ("Std Dev",        "stdev",              True,  False),
        ("Best Year",      "best_year",          True,  False),
        ("Worst Year",     "worst_year",         True,  False),
        ("Max Drawdown",   "max_drawdown",       True,  False),
        ("Sharpe Ratio",   "sharpe_ratio",       False, False),
        ("Sortino Ratio",  "sortino_ratio",      False, False),
        ("Final Balance",  "final_balance",      False, True),
    ]

    headers = ["Metric"] + [m["portfolio_name"] for m in metrics]
    table_data = [headers]

    for label, key, is_pct, is_dollar in ROWS:
        row = [label]
        for m in metrics:
            val = m.get(key)
            if val is None:
                row.append("—")
            elif is_dollar:
                row.append(f"${float(val):,.0f}")
            elif is_pct:
                v = float(val) * 100
                row.append(f"{v:+.2f}%")
            else:
                row.append(f"{float(val):.3f}")
        table_data.append(row)

    col_widths = [2 * inch] + [1.5 * inch] * len(metrics)
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TABLE_STYLE_BASE)
    story.append(t)


def _add_annual_returns_table(story, annual: List[Dict], metrics: List[Dict], styles):
    names = [m["portfolio_name"] for m in metrics]
    headers = ["Year"] + names
    table_data = [headers]

    for row in sorted(annual, key=lambda x: x["year"], reverse=True)[:15]:
        r = [str(row["year"])]
        for name in names:
            v = (row.get("returns") or {}).get(name)
            if v is None:
                r.append("—")
            else:
                r.append(f"{float(v):+.2f}%")
        table_data.append(r)

    col_widths = [1 * inch] + [1.5 * inch] * len(names)
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TABLE_STYLE_BASE)
    story.append(t)


def _add_generic_table(story, data: List[Dict], styles):
    if not data:
        return
    headers = list(data[0].keys())
    table_data = [headers]
    for row in data:
        table_data.append([str(row.get(k, "—")) for k in headers])

    available_width = 7 * inch
    col_w = available_width / len(headers)
    t = Table(table_data, colWidths=[col_w] * len(headers), repeatRows=1)
    t.setStyle(TABLE_STYLE_BASE)
    story.append(t)


def _add_disclaimer(story, styles):
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6))
    story.append(Paragraph(
        "DISCLAIMER: This report is generated by Portfolio Visualizer, an open-source tool for "
        "educational and informational purposes only. Past performance is not indicative of future results. "
        "This report does not constitute investment advice, tax advice, or a solicitation to buy or sell any security. "
        "All data sourced from Yahoo Finance. Please consult a licensed financial advisor before making investment decisions.",
        styles["disclaimer"]
    ))
