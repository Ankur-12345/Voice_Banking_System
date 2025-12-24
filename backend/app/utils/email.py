import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings

class EmailService:
    @staticmethod
    def send_reset_email(email: str, reset_token: str):
        """
        Send password reset email to user
        In production, configure SMTP settings in .env
        """
        try:
            # Email configuration
            sender_email = "noreply@voicebanking.com"
            subject = "Password Reset Request"
            
            # Create reset link
            reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
            
            # Email body
            body = f"""
            Hello,
            
            You requested to reset your password. Click the link below to reset:
            {reset_link}
            
            If you didn't request this, please ignore this email.
            
            Best regards,
            Voice Banking System
            """
            
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))
            
            # For development, just log the token
            print(f"Password reset token for {email}: {reset_token}")
            print(f"Reset link: {reset_link}")
            
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False
