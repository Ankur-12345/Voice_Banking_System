import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings


class OTPService:
    """
    OTP Service for secure transaction verification
    """
    
    def __init__(self):
        # Store OTPs in memory (in production, use Redis or database)
        self.otp_store: Dict[str, Dict] = {}
        self.otp_length = 6
        self.otp_expiry_minutes = 5
    
    def generate_otp(self) -> str:
        """Generate a random 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=self.otp_length))
    
    def create_otp(self, user_email: str, transaction_id: str) -> str:
        """
        Create and store OTP for a transaction
        
        Args:
            user_email: User's email address
            transaction_id: Unique transaction identifier
            
        Returns:
            Generated OTP code
        """
        otp = self.generate_otp()
        expiry_time = datetime.now() + timedelta(minutes=self.otp_expiry_minutes)
        
        # Store OTP with metadata
        self.otp_store[transaction_id] = {
            'otp': otp,
            'email': user_email,
            'expiry': expiry_time,
            'attempts': 0,
            'max_attempts': 3
        }
        
        print(f"🔐 OTP Created: {otp} for {user_email} (expires in {self.otp_expiry_minutes} mins)")
        return otp
    
    def verify_otp(self, transaction_id: str, provided_otp: str) -> tuple[bool, str]:
        """
        Verify OTP for a transaction
        
        Args:
            transaction_id: Transaction identifier
            provided_otp: OTP provided by user
            
        Returns:
            Tuple of (is_valid, message)
        """
        if transaction_id not in self.otp_store:
            return False, "No OTP found for this transaction. Please request a new one."
        
        otp_data = self.otp_store[transaction_id]
        
        # Check if expired
        if datetime.now() > otp_data['expiry']:
            del self.otp_store[transaction_id]
            return False, "OTP has expired. Please request a new one."
        
        # Check attempts
        if otp_data['attempts'] >= otp_data['max_attempts']:
            del self.otp_store[transaction_id]
            return False, "Maximum verification attempts exceeded. Please request a new OTP."
        
        # Verify OTP
        otp_data['attempts'] += 1
        
        if otp_data['otp'] == provided_otp:
            # OTP is valid, remove it (one-time use)
            del self.otp_store[transaction_id]
            return True, "OTP verified successfully"
        else:
            remaining = otp_data['max_attempts'] - otp_data['attempts']
            return False, f"Invalid OTP. {remaining} attempts remaining."
    
    def send_otp_email(self, email: str, otp: str, amount: float, recipient: str) -> bool:
        """
        Send OTP via email
        
        Args:
            email: Recipient email address
            otp: OTP code
            amount: Transfer amount
            recipient: Recipient account/username
            
        Returns:
            Success status
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'🔐 Voice Banking - Transaction Verification OTP'
            msg['From'] = settings.SMTP_USER
            msg['To'] = email
            
            # HTML email body
            html = f"""
            <html>
              <head>
                <style>
                  body {{ font-family: Arial, sans-serif; }}
                  .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                  .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                  .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                  .otp-box {{ background: white; padding: 20px; margin: 20px 0; 
                             border-radius: 10px; text-align: center; border: 2px solid #667eea; }}
                  .otp-code {{ font-size: 32px; font-weight: bold; color: #667eea; 
                              letter-spacing: 5px; font-family: monospace; }}
                  .transaction-details {{ background: white; padding: 15px; margin: 15px 0; 
                                        border-radius: 8px; border-left: 4px solid #ffc107; }}
                  .warning {{ color: #c62828; font-size: 14px; margin-top: 15px; }}
                  .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
                </style>
              </head>
              <body>
                <div class="container">
                  <div class="header">
                    <h1>🏦 Voice Banking System</h1>
                    <p>Transaction Verification Required</p>
                  </div>
                  <div class="content">
                    <h2>Voice Transfer Verification</h2>
                    <p>You have initiated a voice transfer. Please verify this transaction with the OTP below:</p>
                    
                    <div class="otp-box">
                      <p style="margin: 0; color: #666;">Your OTP Code:</p>
                      <div class="otp-code">{otp}</div>
                      <p style="margin: 10px 0 0 0; color: #888; font-size: 14px;">
                        Valid for {self.otp_expiry_minutes} minutes
                      </p>
                    </div>
                    
                    <div class="transaction-details">
                      <h3 style="margin-top: 0;">📋 Transaction Details:</h3>
                      <p><strong>Amount:</strong> ${amount:.2f}</p>
                      <p><strong>Recipient:</strong> {recipient}</p>
                      <p><strong>Method:</strong> Voice Command</p>
                    </div>
                    
                    <div class="warning">
                      <strong>⚠️ Security Notice:</strong><br>
                      • Do NOT share this OTP with anyone<br>
                      • This OTP expires in {self.otp_expiry_minutes} minutes<br>
                      • If you didn't initiate this transfer, please secure your account immediately
                    </div>
                    
                    <div class="footer">
                      <p>This is an automated message from Voice Banking System</p>
                      <p>© 2025 Voice Banking. All rights reserved.</p>
                    </div>
                  </div>
                </div>
              </body>
            </html>
            """
            
            # Attach HTML content
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                
                print(f"📧 OTP email sent to {email}")
                return True
            else:
                print(f"⚠️ SMTP not configured. OTP: {otp} (for testing)")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send OTP email: {e}")
            return False
    
    def cleanup_expired_otps(self):
        """Remove expired OTPs from store"""
        current_time = datetime.now()
        expired_keys = [
            tid for tid, data in self.otp_store.items()
            if current_time > data['expiry']
        ]
        for key in expired_keys:
            del self.otp_store[key]
        
        if expired_keys:
            print(f"🧹 Cleaned up {len(expired_keys)} expired OTPs")
