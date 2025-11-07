from typing import Annotated, Dict, Any, Optional
from fastapi.params import Depends

from core.database.sqlalchamey.core import SessionDep
from core.fastapi.dependency.service_dependency import AbstractService
from core.notifications.email import EmailService
from apps.notifications.models import EmailLog
from apps.settings import settings


class NotificationService(AbstractService):
    DEPENDENCIES = {"session": SessionDep}

    def __init__(self, session: SessionDep, **kwargs):
        super().__init__(**kwargs)
        self.session = session
        self.email_service = EmailService(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_region=settings.AWS_REGION,
            sender_email=settings.SES_SENDER_EMAIL,
            templates_dir=settings.EMAIL_TEMPLATES_DIR,
        )

    async def send_email(
        self,
        recipient_email: str,
        subject: str,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        mail_type: str = "general",
        donation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EmailLog:
        """
        Send email and log the result

        Args:
            recipient_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            mail_type: Type of email (for categorization)
            donation_id: Associated donation ID (if applicable)
            metadata: Additional metadata to store

        Returns:
            EmailLog: Email log record
        """
        # Create email log entry
        email_log = EmailLog(
            donation_id=donation_id,
            recipient_email=recipient_email,
            mail_type=mail_type,
            subject=subject,
            mail_content=html_body or text_body,
            status="pending",
            additional_data=metadata,
        )
        self.session.add(email_log)
        await self.session.commit()
        await self.session.refresh(email_log)

        try:
            # Send email
            result = self.email_service.send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

            # Update email log with result
            if result["success"]:
                email_log.status = "sent"
                email_log.message_id = result.get("message_id")
            else:
                email_log.status = "failed"
                email_log.error_message = result.get("error_message")

        except Exception as e:
            email_log.status = "failed"
            email_log.error_message = str(e)

        await self.session.commit()
        await self.session.refresh(email_log)
        return email_log

    async def send_template_email(
        self,
        recipient_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        mail_type: str = "general",
        donation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EmailLog:
        """
        Send email using a template and log the result

        Args:
            recipient_email: Recipient email address
            subject: Email subject
            template_name: Name of the template file
            context: Dictionary with template variables
            mail_type: Type of email (for categorization)
            donation_id: Associated donation ID (if applicable)
            metadata: Additional metadata to store

        Returns:
            EmailLog: Email log record
        """
        # Create email log entry
        email_log = EmailLog(
            donation_id=donation_id,
            recipient_email=recipient_email,
            mail_type=mail_type,
            subject=subject,
            status="pending",
            additional_data=metadata or {},
        )
        self.session.add(email_log)
        await self.session.commit()
        await self.session.refresh(email_log)

        try:
            # Render and send template
            result = self.email_service.send_template_email(
                recipient_email=recipient_email,
                subject=subject,
                template_name=template_name,
                context=context,
            )

            # Store rendered content if successful
            if result["success"]:
                try:
                    html_content, _ = self.email_service.render_template(
                        template_name, context
                    )
                    email_log.mail_content = html_content
                except Exception:
                    pass  # If rendering fails, we still log the email

                email_log.status = "sent"
                email_log.message_id = result.get("message_id")
            else:
                email_log.status = "failed"
                email_log.error_message = result.get("error_message")

        except Exception as e:
            email_log.status = "failed"
            email_log.error_message = str(e)

        await self.session.commit()
        await self.session.refresh(email_log)
        return email_log

    async def send_donation_thank_you_email(
        self, donation_id: str, recipient_email: str, context: Dict[str, Any]
    ) -> EmailLog:
        """
        Send donation thank you email

        Args:
            donation_id: Donation ID
            recipient_email: Recipient email address
            context: Email context with donation details

        Returns:
            EmailLog: Email log record
        """
        return await self.send_template_email(
            recipient_email=recipient_email,
            subject=f"Thank You for Your Donation - Order {context.get('order_id')}",
            template_name="donation_thank_you.html",
            context=context,
            mail_type="donation_thank_you",
            donation_id=donation_id,
            metadata={"order_id": context.get("order_id")},
        )


NotificationServiceDependency = Annotated[
    NotificationService, NotificationService.get_dependency()
]
