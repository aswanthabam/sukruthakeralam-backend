from core.fastapi.dependency.service_dependency import AbstractService
from curses import textpad
from distutils import fancy_getopt
from core import payment
from apps.payments.models import PhonePePaymentLog
from apps.payments.models import SbiePayPaymentLog
from typing import Literal
from typing_extensions import Annotated
from apps.donation.models import Donation
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from num2words import num2words

class InvoiceService(AbstractService):
    def generate_invoice_pdf(self, donation: Donation, payment_provider: Literal["sbiepay", "phonepe"], payment_log: SbiePayPaymentLog | PhonePePaymentLog) -> io.BytesIO:
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle(f"Donation_Receipt_{donation.order_id}")

        # Sukrutha Keralam Details 
        # Update these with actuals or leave None to exclude from the PDF
        ngo_name = "Sukrutha Keralam"
        ngo_address = "Janam Souhrudavedi Cultural & Charitable Trust, JTC 52/3429, Krishna Nagar, Thiruvallom Road, Karumam, Thiruvananthapuram – 695002, Kerala, India" 
        ngo_phone = "+91 95674 91010" 
        ngo_email = "support@sukruthakeralam.com"
        
        # Optional Registration details
        ngo_pan = None
        ngo_80g = None
        ngo_fcra = None

        # Draw Header
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(300, 750, ngo_name)
        
        pdf.setFont("Helvetica", 10)
        y_offset = 735
        
        if ngo_address:
            pdf.drawCentredString(300, y_offset, ngo_address)
            y_offset -= 15
            
        contact_info = []
        if ngo_phone: contact_info.append(f"Phone: {ngo_phone}")
        if ngo_email: contact_info.append(f"Email: {ngo_email}")
        if contact_info:
            pdf.drawCentredString(300, y_offset, " | ".join(contact_info))
            y_offset -= 15
            
        reg_info = []
        if ngo_pan: reg_info.append(f"PAN: {ngo_pan}")
        if ngo_80g: reg_info.append(f"80G URN: {ngo_80g}")
        if ngo_fcra: reg_info.append(f"FCRA: {ngo_fcra}")
        if reg_info:
            pdf.drawCentredString(300, y_offset, " | ".join(reg_info))
            y_offset -= 15

        pdf.line(50, y_offset, 550, y_offset)
        y_offset -= 25

        # Receipt Title
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(300, y_offset, "DONATION RECEIPT")
        y_offset -= 40

        # Donor & Transaction Info Setup
        pdf.setFont("Helvetica", 12)
        
        # Format Amount to Words (Indian English format)
        # Assumes donation.amount is a numeric type
        amount = float(getattr(donation, 'amount', 0.0))
        amount_words = num2words(amount, lang='en_IN').title() + " Rupees Only"

        # Fallbacks for dynamic fields in case your ORM names differ
        donor_name = getattr(donation, 'full_name', getattr(donation, 'name', 'N/A'))
        donor_phone = getattr(donation, 'phone_number', getattr(donation, 'phone', 'N/A'))
        donor_email = getattr(donation, 'email', None)
        
        # Safely extract created date
        created_at = getattr(donation, 'created_at', None)
        date_str = created_at.strftime('%Y-%m-%d') if created_at else datetime.now().strftime('%Y-%m-%d')

        details = [
            f"Receipt Number: {donation.order_id}",
            f"Date: {date_str}",
            f"Donor Name: {donor_name}",
            f"Donor Phone: {donor_phone}",
        ]

        if donor_email:
            details.append(f"Donor Email: {donor_email}")

        details.extend([
            f"Donation Amount: INR {amount:,.2f}",
            f"Amount in Words: {amount_words}",
        ])

        # Transaction ID if available
        if payment_provider == "sbiepay":
            tx_id = getattr(payment_log, "sbiepay_ref_id")
        elif payment_provider == "phonepe":
            tx_id = getattr(payment_log, "phonepe_order_id")
        else:
            tx_id = None
        if tx_id:
            details.append(f"Transaction Ref: {tx_id}")

        # Draw details on PDF dynamically
        for detail in details:
            pdf.drawString(50, y_offset, detail)
            y_offset -= 25

        # Footer / Declaration
        y_offset -= 40
        pdf.setFont("Helvetica-Oblique", 10)
        
        if ngo_80g:
            pdf.drawString(50, y_offset, "This receipt is issued for tax exemption purposes under Section 80G of the Income Tax Act, 1961.")
        else:
            pdf.drawString(50, y_offset, "Thank you for your generous contribution to Sukrutha Keralam.")
        
        y_offset -= 60
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(400, y_offset, "Authorized Signatory")

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return buffer


InvoiceServiceDependency = Annotated[InvoiceService, InvoiceService.get_dependency()]