from core.fastapi.dependency.service_dependency import AbstractService
from apps.payments.models import PhonePePaymentLog
from apps.payments.models import SbiePayPaymentLog
from typing import Literal
from typing_extensions import Annotated
from apps.donation.models import Donation
import io
from datetime import datetime
from num2words import num2words
from zoneinfo import ZoneInfo

# ReportLab imports for structured layout (Platypus)
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os

class InvoiceService(AbstractService):
    def generate_invoice_pdf(self, donation: Donation, payment_provider: Literal["sbiepay", "phonepe"], payment_log: SbiePayPaymentLog | PhonePePaymentLog) -> io.BytesIO:
        buffer = io.BytesIO()
        # Set margins to utilize space better
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=50)
        doc.title = f"Donation_Receipt_{donation.order_id}"
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles for headers and text
        title_style = ParagraphStyle(
            name='TitleStyle',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=18,
            spaceAfter=6
        )
        
        address_style = ParagraphStyle(
            name='AddressStyle',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=10,
            leading=12,
            spaceAfter=4
        )
        
        contact_style = ParagraphStyle(
            name='ContactStyle',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=10,
            textColor=colors.darkslategray,
            spaceAfter=12
        )

        receipt_title_style = ParagraphStyle(
            name='ReceiptTitle',
            parent=styles['Heading2'],
            alignment=TA_CENTER,
            fontSize=14,
            spaceBefore=10,
            spaceAfter=20
        )

        # Sukrutha Keralam Details 
        ngo_name = "Sukrutha Keralam"
        # Using HTML-like tags supported by ReportLab Paragraphs for line breaks if needed, or rely on auto-wrap
        ngo_address = "Janam Souhrudavedi Cultural & Charitable Trust, JTC 52/3429,<br/>Krishna Nagar, Thiruvallom Road, Karumam,<br/>Thiruvananthapuram – 695002, Kerala, India" 
        ngo_phone = "+91 95674 91010" 
        ngo_email = "support@sukruthakeralam.com"
        
        # Header Section
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_dir, "assets", "logo.png")
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=60, height=60)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 10))
            
        elements.append(Paragraph(f"<b>{ngo_name}</b>", title_style))
        elements.append(Paragraph(ngo_address, address_style))
        elements.append(Paragraph(f"Phone: {ngo_phone} &nbsp;|&nbsp; Email: {ngo_email}", contact_style))
        
        elements.append(Spacer(1, 10))
        
        # Receipt Title
        elements.append(Paragraph("<u>DONATION RECEIPT</u>", receipt_title_style))

        # Prepare Transaction Data
        amount = float(getattr(donation, 'amount', 0.0))
        amount_words = num2words(amount, lang='en_IN').title() + " Rupees Only"
        
        donor_name = getattr(donation, 'full_name', getattr(donation, 'name', 'N/A'))
        donor_phone = getattr(donation, 'phone_number', getattr(donation, 'phone', 'N/A'))
        donor_email = getattr(donation, 'email', 'N/A')
        
        created_at = getattr(donation, 'created_at', None)
        ist_tz = ZoneInfo("Asia/Kolkata")
        if created_at:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=ZoneInfo("UTC"))
            date_str = created_at.astimezone(ist_tz).strftime('%Y-%m-%d %H:%M %Z')
        else:
            date_str = datetime.now(ist_tz).strftime('%Y-%m-%d %H:%M %Z')

        # Determine Transaction ID
        if payment_provider == "sbiepay":
            tx_id = getattr(payment_log, "sbiepay_ref_id", "N/A")
        elif payment_provider == "phonepe":
            tx_id = getattr(payment_log, "provider_reference_id", "N/A") # often mapped to this, adjust if needed
        else:
            tx_id = "N/A"

        # Define Table Data (Row by Row)
        data = [
            ["Receipt Number:", str(donation.order_id)],
            ["Date & Time:", date_str],
            ["Donor Name:", donor_name],
            ["Donor Phone:", str(donor_phone)],
            ["Donor Email:", donor_email if donor_email else "N/A"],
            ["Payment Provider:", payment_provider.upper()],
            ["Transaction Ref:", str(tx_id)],
            ["Donation Amount:", f"INR {amount:,.2f}"],
            ["Amount in Words:", Paragraph(amount_words, styles['Normal'])] # Wrap long text in a Paragraph
        ]

        # Create Table Structure
        # Column widths: 150 points for labels, 350 for values
        t = Table(data, colWidths=[150, 350])
        
        # Table Styling
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke), # Light gray background for labels
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'), # Align labels to right
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Align values to left
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), # Bold labels
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),      # Normal values
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey), # Subtle grid lines
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(t)
        
        elements.append(Spacer(1, 40))

        # Footer Section
        footer_style = ParagraphStyle(
            name='FooterStyle',
            parent=styles['Normal'],
            alignment=TA_LEFT,
            fontSize=10,
            textColor=colors.dimgrey,
            fontName='Helvetica-Oblique'
        )
        
        footer_text = "Thank you for your generous contribution to Sukrutha Keralam."
        elements.append(Paragraph(footer_text, footer_style))
        
        elements.append(Spacer(1, 60))
        
        sign_style = ParagraphStyle(
            name='SignStyle',
            parent=styles['Normal'],
            alignment=TA_RIGHT,
            fontSize=11,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("Authorized Signatory", sign_style))

        # Build the PDF
        doc.build(elements)

        buffer.seek(0)
        return buffer

InvoiceServiceDependency = Annotated[InvoiceService, InvoiceService.get_dependency()]