"""Backend-only branded quotation PDF service.

Do not expose a browser PDF generator. Call this only after verifying the user's
company membership and the quotation's approved/issued state server-side.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas


@dataclass(frozen=True)
class QuotationLine:
    description: str
    quantity: int
    unit_price_minor: int


@dataclass(frozen=True)
class ApprovedQuotation:
    reference: str
    company_name: str
    client_name: str
    issued_on: str
    valid_until: str
    currency: str
    lines: tuple[QuotationLine, ...]
    tax_minor: int
    status: str


def render_approved_quotation_pdf(
    quotation: ApprovedQuotation, *, approved_logo_path: Path, document_kind: str = "QUOTATION",
) -> bytes:
    """Render an A4 PDF with the *actual* brand image; fail closed otherwise.

    This pure backend service deliberately accepts no raw HTML, JS or user
    supplied arbitrary filesystem path over HTTP.
    """
    if document_kind not in {"QUOTATION", "INVOICE"}:\n        raise ValueError("Unsupported document type")\n    logo = Path(approved_logo_path)
    if not logo.is_file() or logo.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise ValueError("An approved CapitalBridge logo is required")
    if quotation.status not in {"approved", "sent", "accepted"}:
        raise ValueError("Only approved quotations may be rendered officially")
    if quotation.currency != "LSL":
        raise ValueError("Only validated LSL quotations are currently supported")
    if not quotation.lines or quotation.tax_minor < 0:
        raise ValueError("Quotation amounts are invalid")
    if any(line.quantity <= 0 or line.unit_price_minor < 0 for line in quotation.lines):
        raise ValueError("Invalid quotation item")
    for value in (quotation.reference, quotation.company_name, quotation.client_name):
        if not value.strip() or len(value) > 250:
            raise ValueError("Missing or excessive document identity")

    out = BytesIO()
    pdf = canvas.Canvas(out, pagesize=A4, pageCompression=1)
    pdf.setTitle(f"{document_kind.title()} {quotation.reference}")
    width, height = A4
    navy = colors.HexColor("#142b46")
    ink = colors.HexColor("#202d40")
    light = colors.HexColor("#eff4f8")
    left, right, bottom = 52, width - 52, 56

    def money(minor: int) -> str:
        return f"M {Decimal(minor) / Decimal(100):,.2f}"

    style = ParagraphStyle("line", fontName="Helvetica", fontSize=9, leading=13, textColor=ink)

    def wrapped(text: str, x: float, top: float, max_width: float) -> float:
        p = Paragraph(escape(text), style)
        _, h = p.wrap(max_width, 500)
        p.drawOn(pdf, x, top - h)
        return h

    def new_page(page: int) -> float:
        pdf.setFillColor(navy)
        pdf.rect(0, height - 13, width, 13, fill=1, stroke=0)
        pdf.drawImage(ImageReader(str(logo)), left, height - 93, width=105,
                      height=62, preserveAspectRatio=True, anchor="c", mask="auto")
        pdf.setFillColor(navy)
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawRightString(right, height - 60, document_kind)
        pdf.setFont("Helvetica", 9)
        pdf.drawRightString(right, height - 79, quotation.reference)
        pdf.setStrokeColor(colors.HexColor("#dce5ef"))
        pdf.line(left, height - 103, right, height - 103)
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.HexColor("#66778a"))
        pdf.drawString(left, 37, quotation.company_name[:85])
        pdf.drawRightString(right, 37, f"Page {page}")
        return height - 128

    page = 1
    y = new_page(page)
    pdf.setFillColor(ink)
    y -= wrapped("Prepared for: " + quotation.client_name, left, y, 430) + 12
    for field, value in (("Issue date", quotation.issued_on), ("Due on" if document_kind == "INVOICE" else "Valid until", quotation.valid_until)):
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(left, y, field)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(left + 100, y, value)
        y -= 20
    y -= 17

    def table_heading(y: float) -> float:
        pdf.setFillColor(light)
        pdf.roundRect(left, y - 27, right - left, 30, 4, stroke=0, fill=1)
        pdf.setFillColor(navy)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(left + 10, y - 16, "Service / description")
        pdf.drawRightString(right - 169, y - 16, "Qty")
        pdf.drawRightString(right - 83, y - 16, "Unit")
        pdf.drawRightString(right - 9, y - 16, "Amount")
        return y - 39

    y = table_heading(y)
    subtotal = 0
    for line in quotation.lines:
        line_total = line.quantity * line.unit_price_minor
        subtotal += line_total
        p = Paragraph(escape(line.description), style)
        _, h = p.wrap(210, 1000)
        row_height = max(h + 15, 35)
        if y - row_height < bottom + 90:
            pdf.showPage()
            page += 1
            y = table_heading(new_page(page))
        p.drawOn(pdf, left + 10, y - h - 5)
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica", 9)
        pdf.drawRightString(right - 169, y - 15, str(line.quantity))
        pdf.drawRightString(right - 83, y - 15, money(line.unit_price_minor))
        pdf.drawRightString(right - 9, y - 15, money(line_total))
        pdf.setStrokeColor(colors.HexColor("#e2e9f0"))
        pdf.line(left, y - row_height + 1, right, y - row_height + 1)
        y -= row_height
    if y < bottom + 105:
        pdf.showPage()
        page += 1
        y = new_page(page)
    y -= 15
    for label, amount, bold in (
        ("Subtotal", subtotal, False),
        ("Tax", quotation.tax_minor, False),
        ("TOTAL (LSL)", subtotal + quotation.tax_minor, True),
    ):
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 11 if bold else 9)
        pdf.setFillColor(navy if bold else ink)
        pdf.drawRightString(right - 110, y, label)
        pdf.drawRightString(right, y, money(amount))
        y -= 22
    pdf.save()
    return out.getvalue()
