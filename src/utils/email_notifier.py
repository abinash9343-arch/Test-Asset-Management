
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_FILE = Path("config/config.yaml")

class EmailNotifier:
    def __init__(self):
        self.config = self._load_config()
        self.email_config = self.config.get('email', {})
        self.enabled = self.email_config.get('enabled', False)
        
    def _load_config(self):
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def send_assignment_email(self, to_email, asset_details):
        """
        Sends an email notification for asset assignment.
        """
        if not to_email:
            logger.warning("No email address provided for notification.")
            return False

        subject = f"IT Asset Assigned: {asset_details.get('name', 'Unknown Asset')}"
        
        body = f"""
        Dear User,

        The following IT asset has been assigned to you:

        Asset Name: {asset_details.get('name', 'N/A')}
        Type: {asset_details.get('asset_type', 'N/A')}
        Serial Number: {asset_details.get('serial_number', 'N/A')}
        
        Please contact IT support if you have any questions.

        Best regards,
        IT Support Team
        """

        if not self.enabled:
            logger.info(f"--- [MOCK EMAIL] ---")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {body}")
            logger.info(f"--------------------")
            return True

        try:
            smtp_server = self.email_config.get('smtp_server')
            smtp_port = self.email_config.get('smtp_port')
            sender_email = self.email_config.get('sender_email')
            password = self.email_config.get('password')
            
            if not all([smtp_server, smtp_port, sender_email, password]):
                logger.error("Missing SMTP configuration.")
                return False

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_password_reset(self, to_email, new_password):
        """
        Sends an email with the new password.
        """
        if not to_email:
            logger.warning("No email address provided for password reset.")
            return False

        subject = "IT Agent - Password Reset"
        
        body = f"""
        Dear User,

        Your password for the IT Agent Dashboard has been reset.

        New Password: {new_password}

        Please login and change your password if needed.

        Best regards,
        IT Support Team
        """

        if not self.enabled:
            logger.info(f"--- [MOCK EMAIL: PASSWORD RESET] ---")
            logger.info(f"To: {to_email}")
            logger.info(f"New Password: {new_password}")
            logger.info(f"------------------------------------")
            return True

        try:
            smtp_server = self.email_config.get('smtp_server')
            smtp_port = self.email_config.get('smtp_port')
            sender_email = self.email_config.get('sender_email')
            password = self.email_config.get('password')
            
            if not all([smtp_server, smtp_port, sender_email, password]):
                logger.error("Missing SMTP configuration.")
                # Fallback logging for safety when email is enabled but config is missing
                logger.info(f"FALLBACK LOG: New Password for {to_email} is {new_password}")
                return False

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Password reset email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
             # Fallback logging so user isn't locked out if email fails
            logger.info(f"FALLBACK LOG: New Password for {to_email} is {new_password}")
            return False
