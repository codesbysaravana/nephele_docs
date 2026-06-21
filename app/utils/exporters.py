"""Exporters utility for serializing system reports to JSON, CSV, and PDF formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def export_to_json(data: Any) -> str:
    """Format python structures into a pretty JSON string."""
    return json.dumps(data, indent=2, default=str)


def export_to_csv(rows: List[Dict[str, Any]], headers: List[str]) -> str:
    """Serialize tabular dict logs into a CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        # Filter to include only required keys
        filtered_row = {k: row.get(k, "") for k in headers}
        writer.writerow(filtered_row)
    return output.getvalue()


def build_base_pdf(buffer: io.BytesIO, title: str, story: List[Any]) -> bytes:
    """Generate a clean PDF document from story flowables using ReportLab."""
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    # Define document layout event handlers (header/footer)
    def add_page_decorations(canvas: Any, document: Any) -> None:
        canvas.saveState()
        # Top banner line
        canvas.setStrokeColor(colors.HexColor("#3F51B5"))
        canvas.setLineWidth(2)
        canvas.line(40, letter[1] - 45, letter[0] - 40, letter[1] - 45)
        # Header text
        canvas.setFont('Helvetica-Bold', 8)
        canvas.setFillColor(colors.HexColor("#757575"))
        canvas.drawString(40, letter[1] - 35, "NEPHELE INTERVIEW INTELLIGENCE SYSTEM")
        # Footer text
        canvas.setFont('Helvetica', 8)
        canvas.drawString(40, 30, f"Confidential  |  Generated automatically")
        canvas.drawRightString(letter[0] - 40, 30, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
    return buffer.getvalue()


def export_interview_pdf(report: Dict[str, Any]) -> bytes:
    """Create a formatted PDF candidate evaluation report."""
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor("#1A237E"),
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor("#3949AB"),
        spaceBefore=15,
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=8
    )

    story = [
        Spacer(1, 15),
        Paragraph(f"Candidate Interview Report", title_style),
        Spacer(1, 5)
    ]

    # Profile Table
    profile_data = [
        [Paragraph("<b>Candidate ID:</b>", body_style), Paragraph(report.get("candidate_id", ""), body_style)],
        [Paragraph("<b>Candidate Name:</b>", body_style), Paragraph(report.get("candidate_name", ""), body_style)],
        [Paragraph("<b>Activated Domain:</b>", body_style), Paragraph(report.get("domain", ""), body_style)],
    ]
    
    # Append overall scores per domain
    for dom_id, score in report.get("domain_scores", {}).items():
        profile_data.append([
            Paragraph(f"<b>Overall {dom_id} Mastery:</b>", body_style),
            Paragraph(f"<b>{score:.1%}</b>", body_style)
        ])

    t_profile = Table(profile_data, colWidths=[150, 350])
    t_profile.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F5F5F7")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
    ]))
    
    story.append(t_profile)
    story.append(Spacer(1, 15))

    # Summary
    story.append(Paragraph("Executive Summary", section_style))
    story.append(Paragraph(report.get("summary", ""), body_style))
    story.append(Spacer(1, 10))

    # Concept Mastery Table
    story.append(Paragraph("Concept Level Masteries", section_style))
    
    concept_headers = [Paragraph("<b>Concept</b>", body_style), Paragraph("<b>Mastery Level</b>", body_style), Paragraph("<b>Status</b>", body_style)]
    concept_data = [concept_headers]
    
    for concept, score in report.get("concept_scores", {}).items():
        status = "Mastered" if score >= 0.80 else ("Needs Review" if score <= 0.40 else "Developing")
        status_color = "#2E7D32" if score >= 0.80 else ("#C62828" if score <= 0.40 else "#EF6C00")
        
        status_para = Paragraph(f"<font color='{status_color}'><b>{status}</b></font>", body_style)
        concept_data.append([
            Paragraph(concept, body_style),
            Paragraph(f"{score:.1%}", body_style),
            status_para
        ])

    t_concepts = Table(concept_data, colWidths=[220, 140, 140])
    t_concepts.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3F51B5")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
    ]))
    # Set text colors in table headers
    for i in range(3):
        t_concepts.setStyle(TableStyle([('TEXTCOLOR', (i, 0), (i, 0), colors.white)]))

    story.append(t_concepts)
    story.append(Spacer(1, 15))

    # Strong & Weak Areas
    story.append(Paragraph("Detailed Performance Analysis", section_style))
    strong_list = report.get("strong_concepts", [])
    weak_list = report.get("weak_concepts", [])
    rec_list = report.get("recommended_topics", [])
    
    story.append(Paragraph(f"<b>Key Strengths:</b> {', '.join(strong_list) if strong_list else 'No concepts fully mastered yet.'}", body_style))
    story.append(Paragraph(f"<b>Development Areas:</b> {', '.join(weak_list) if weak_list else 'No severe conceptual gaps identified.'}", body_style))
    story.append(Paragraph(f"<b>Next Actionable Learning Paths:</b> {', '.join(rec_list) if rec_list else 'Complete the next recommended modules.'}", body_style))

    return build_base_pdf(buffer, "Interview Report", story)


def export_evolution_pdf(report: Dict[str, Any]) -> bytes:
    """Create a formatted PDF report for graph structural evolution recommendations."""
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor("#006064"),
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor("#00838F"),
        spaceBefore=12,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        spaceAfter=6
    )

    story = [
        Spacer(1, 15),
        Paragraph(f"Knowledge Graph Evolution Recommendations", title_style),
        Spacer(1, 5),
        Paragraph(f"<b>Domain:</b> {report.get('domain', 'machine_learning')}", body_style),
        Paragraph("The following optimizations are mined from candidate traversal paths and rubrics:", body_style),
        Spacer(1, 10)
    ]

    # Concept difficulty rankings
    story.append(Paragraph("Mined Concept Difficulties & Rankings", section_style))
    diff_headers = [Paragraph("<b>Concept ID</b>", body_style), Paragraph("<b>Score</b>", body_style), Paragraph("<b>Inferred Level</b>", body_style)]
    diff_table_data = [diff_headers]
    for row in report.get("concept_difficulty_rankings", []):
        diff_table_data.append([
            Paragraph(row.get("concept", ""), body_style),
            Paragraph(f"{row.get('difficulty_score', 0.0):.3f}", body_style),
            Paragraph(row.get("classification", "").upper(), body_style)
        ])
    t_diff = Table(diff_table_data, colWidths=[240, 130, 130])
    t_diff.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00838F")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#B2DFDB")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0F2F1")),
    ]))
    story.append(t_diff)
    story.append(Spacer(1, 15))

    # Edge strength updates
    story.append(Paragraph("Active Edge Relationship Strengths", section_style))
    edge_headers = [Paragraph("<b>Source</b>", body_style), Paragraph("<b>Target</b>", body_style), Paragraph("<b>Action Recommendation</b>", body_style)]
    edge_table_data = [edge_headers]
    for row in report.get("existing_edge_recommendations", []):
        edge_table_data.append([
            Paragraph(row.get("source", ""), body_style),
            Paragraph(row.get("target", ""), body_style),
            Paragraph(row.get("recommendation", ""), body_style)
        ])
    t_edges = Table(edge_table_data, colWidths=[170, 170, 160])
    t_edges.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0097A7")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#B2DFDB")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0F2F1")),
    ]))
    story.append(t_edges)

    return build_base_pdf(buffer, "Evolution Report", story)


def export_analytics_pdf(metrics: Dict[str, Any]) -> bytes:
    """Create a formatted PDF report of aggregated system performance and latency metrics."""
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor("#2E7D32"),
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor("#388E3C"),
        spaceBefore=12,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        spaceAfter=6
    )

    story = [
        Spacer(1, 15),
        Paragraph(f"System Analytics & Latency Report", title_style),
        Spacer(1, 10)
    ]

    # Latencies
    story.append(Paragraph("System Latency Monitoring", section_style))
    latency_headers = [Paragraph("<b>Pipeline Stage</b>", body_style), Paragraph("<b>Average Latency (s)</b>", body_style), Paragraph("<b>Sample Size</b>", body_style)]
    latencies_data = [latency_headers]
    for stage, stats in metrics.get("latencies", {}).items():
        latencies_data.append([
            Paragraph(stage.replace("_", " ").title(), body_style),
            Paragraph(f"{stats.get('average_seconds', 0.0):.3f} s", body_style),
            Paragraph(str(stats.get("invocation_count", 0)), body_style)
        ])
    t_lat = Table(latencies_data, colWidths=[220, 140, 140])
    t_lat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#388E3C")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#C8E6C9")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E8F5E9")),
    ]))
    story.append(t_lat)
    story.append(Spacer(1, 15))

    # Token expenditures and costs
    story.append(Paragraph("API Cost and Token Tracking", section_style))
    token_headers = [Paragraph("<b>AI Provider</b>", body_style), Paragraph("<b>Total Tokens</b>", body_style), Paragraph("<b>Accumulated Cost ($)</b>", body_style)]
    token_data = [token_headers]
    for provider, stats in metrics.get("provider_costs", {}).items():
        token_data.append([
            Paragraph(provider.title(), body_style),
            Paragraph(f"{stats.get('total', 0):,}", body_style),
            Paragraph(f"${stats.get('cost', 0.0):.5f}", body_style)
        ])
    t_tok = Table(token_data, colWidths=[180, 160, 160])
    t_tok.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#C8E6C9")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E8F5E9")),
    ]))
    story.append(t_tok)

    return build_base_pdf(buffer, "Analytics Report", story)
