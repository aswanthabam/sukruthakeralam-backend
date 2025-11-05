import os
from typing import Optional, Dict, Any, List
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from jinja2 import Environment, FileSystemLoader, Template
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    AWS SES Email Service with template support
    """

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        sender_email: str,
        templates_dir: Optional[str] = None,
    ):
        """
        Initialize Email Service

        Args:
            aws_access_key_id: AWS Access Key ID
            aws_secret_access_key: AWS Secret Access Key
            aws_region: AWS Region (e.g., 'us-east-1')
            sender_email: Verified sender email address in SES
            templates_dir: Directory containing email templates
        """
        self.sender_email = sender_email
        self.ses_client = boto3.client(
            "ses",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )

        # Setup Jinja2 template environment
        if templates_dir:
            self.templates_dir = Path(templates_dir)
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=True,
            )
        else:
            self.templates_dir = None
            self.jinja_env = None

    def render_template(
        self, template_name: str, context: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Render email template with context

        Args:
            template_name: Name of the template file (e.g., 'donation_thank_you.html')
            context: Dictionary with template variables

        Returns:
            Tuple of (html_content, text_content)
        """
        if not self.jinja_env:
            raise ValueError("Templates directory not configured")

        try:
            # Render HTML template
            html_template = self.jinja_env.get_template(template_name)
            html_content = html_template.render(**context)

            # Try to render text version
            text_template_name = template_name.replace(".html", ".txt")
            try:
                text_template = self.jinja_env.get_template(text_template_name)
                text_content = text_template.render(**context)
            except Exception:
                # Fallback: strip HTML tags for text version
                import re

                text_content = re.sub(r"<[^>]+>", "", html_content)

            return html_content, text_content

        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}")
            raise

    def send_email(
        self,
        recipient_email: str,
        subject: str,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        reply_to_emails: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send email using AWS SES

        Args:
            recipient_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
            reply_to_emails: List of reply-to email addresses

        Returns:
            Dictionary with response data including MessageId and status
        """
        if not html_body and not text_body:
            raise ValueError("Either html_body or text_body must be provided")

        try:
            # Prepare email destination
            destination = {"ToAddresses": [recipient_email]}

            if cc_emails:
                destination["CcAddresses"] = cc_emails
            if bcc_emails:
                destination["BccAddresses"] = bcc_emails

            # Prepare message body
            body = {}
            if html_body:
                body["Html"] = {"Charset": "UTF-8", "Data": html_body}
            if text_body:
                body["Text"] = {"Charset": "UTF-8", "Data": text_body}

            # Prepare message
            message = {
                "Subject": {"Charset": "UTF-8", "Data": subject},
                "Body": body,
            }

            # Send email
            send_kwargs = {
                "Source": self.sender_email,
                "Destination": destination,
                "Message": message,
            }

            if reply_to_emails:
                send_kwargs["ReplyToAddresses"] = reply_to_emails

            response = self.ses_client.send_email(**send_kwargs)

            logger.info(
                f"Email sent successfully to {recipient_email}. MessageId: {response['MessageId']}"
            )

            return {
                "success": True,
                "message_id": response["MessageId"],
                "status": "sent",
                "recipient": recipient_email,
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(
                f"Failed to send email to {recipient_email}. Error: {error_code} - {error_message}"
            )

            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
                "status": "failed",
                "recipient": recipient_email,
            }

        except Exception as e:
            logger.error(
                f"Unexpected error sending email to {recipient_email}: {str(e)}"
            )
            return {
                "success": False,
                "error_message": str(e),
                "status": "failed",
                "recipient": recipient_email,
            }

    def send_template_email(
        self,
        recipient_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        reply_to_emails: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send email using a template

        Args:
            recipient_email: Recipient email address
            subject: Email subject
            template_name: Name of the template file
            context: Dictionary with template variables
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
            reply_to_emails: List of reply-to email addresses

        Returns:
            Dictionary with response data including MessageId and status
        """
        try:
            # Render template
            html_body, text_body = self.render_template(template_name, context)

            # Send email
            return self.send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                reply_to_emails=reply_to_emails,
            )

        except Exception as e:
            logger.error(f"Error sending template email to {recipient_email}: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "status": "failed",
                "recipient": recipient_email,
            }
