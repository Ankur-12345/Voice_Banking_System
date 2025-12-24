from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from ..database import Base


class PendingTransaction(Base):
    __tablename__ = "pending_transactions"
    
    id = Column(String, primary_key=True)
    sender_username = Column(String, nullable=False)
    recipient_account = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    transaction_type = Column(String, default="voice_transfer")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    otp_sent = Column(Boolean, default=False)
    status = Column(String, default="pending")  # pending, verified, expired, cancelled
