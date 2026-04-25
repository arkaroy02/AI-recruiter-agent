"""Experimental email service for sending meeting links to shortlisted candidates."""

from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import json
from pathlib import Path


# Store meeting tokens in memory (in production, use a database)
MEETING_STORE: Dict[str, Dict] = {}


def generate_meeting_token(run_id: str, candidate_name: str, expiry_hours: int = 48) -> str:
    """Generate a unique meeting token for a candidate."""
    token = str(uuid4())
    expiry = datetime.now() + timedelta(hours=expiry_hours)
    
    MEETING_STORE[token] = {
        "token": token,
        "run_id": run_id,
        "candidate_name": candidate_name,
        "created_at": datetime.now().isoformat(),
        "expires_at": expiry.isoformat(),
        "status": "pending",  # pending, joined, completed, expired
        "joined_at": None,
        "interview_answers": [],
    }
    
    return token


def validate_meeting_token(token: str) -> Optional[Dict]:
    """Validate a meeting token and return meeting info if valid."""
    meeting = MEETING_STORE.get(token)
    if not meeting:
        return None
    
    # Check expiry
    expires_at = datetime.fromisoformat(meeting["expires_at"])
    if datetime.now() > expires_at:
        meeting["status"] = "expired"
        return None
    
    return meeting


def get_meeting_by_token(token: str) -> Optional[Dict]:
    """Get meeting details by token."""
    return MEETING_STORE.get(token)


def update_meeting_status(token: str, status: str, joined_at: Optional[str] = None) -> None:
    """Update meeting status."""
    if token in MEETING_STORE:
        MEETING_STORE[token]["status"] = status
        if joined_at:
            MEETING_STORE[token]["joined_at"] = joined_at


def add_interview_answer(token: str, question: str, answer: str) -> None:
    """Add an interview answer to the meeting record."""
    if token in MEETING_STORE:
        MEETING_STORE[token]["interview_answers"].append({
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })


def send_meeting_email(
    candidate_email: str,
    candidate_name: str,
    meeting_token: str,
    company_name: str = "Talent Scout Studio",
    base_url: str = "http://localhost:8000"
) -> Dict:
    """
    Send meeting invitation email to candidate.
    
    Returns dict with success status and message.
    """
    # Get email settings from environment
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("FROM_EMAIL", smtp_user)
    
    # Generate meeting link
    meeting_link = f"{base_url}/interview/{meeting_token}"
    
    # Email subject and body
    subject = f"Interview Invitation from {company_name}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 30px; font-weight: bold; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            .meeting-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Congratulations, {candidate_name}!</h1>
                <p>You've been shortlisted for an interview</p>
            </div>
            <div class="content">
                <p>Dear {candidate_name},</p>
                
                <p>We're excited to inform you that your profile has been shortlisted for an interview opportunity! 
                After reviewing your qualifications, we believe you could be a great fit for our team.</p>
                
                <div class="meeting-details">
                    <h3>📅 Interview Details</h3>
                    <p><strong>Company:</strong> {company_name}</p>
                    <p><strong>Status:</strong> Shortlisted</p>
                    <p><strong>Meeting Link:</strong> Valid for 48 hours</p>
                </div>
                
                <p style="text-align: center;">
                    <a href="{meeting_link}" class="button">Join Interview Portal</a>
                </p>
                
                <p><strong>How it works:</strong></p>
                <ol>
                    <li>Click the button above to access your personalized interview portal</li>
                    <li>Complete the interview questions at your convenience</li>
                    <li>Our team will review your responses and get back to you</li>
                </ol>
                
                <p><strong>Important:</strong> This link will expire in 48 hours for security purposes.</p>
                
                <p>If you have any questions, please don't hesitate to reach out.</p>
                
                <p>Best regards,<br>
                <strong>{company_name} Recruitment Team</strong></p>
            </div>
            <div class="footer">
                <p>This is an automated message from {company_name} Talent Platform</p>
                <p>Meeting Token: {meeting_token[:8]}...</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Congratulations {candidate_name}!
    
    You've been shortlisted for an interview with {company_name}.
    
    Click the following link to join your interview portal:
    {meeting_link}
    
    This link will expire in 48 hours.
    
    Best regards,
    {company_name} Recruitment Team
    """
    
    # If no SMTP credentials, simulate email sending
    if not smtp_user or not smtp_password:
        return {
            "success": True,
            "simulated": True,
            "message": "Email simulated (no SMTP credentials configured)",
            "meeting_link": meeting_link,
            "token": meeting_token,
            "candidate_email": candidate_email,
            "note": "Set SMTP_USER and SMTP_PASSWORD in .env to send real emails"
        }
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = from_email
        msg["To"] = candidate_email
        msg["Subject"] = subject
        
        # Attach both plain text and HTML versions
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, candidate_email, msg.as_string())
        
        return {
            "success": True,
            "simulated": False,
            "message": f"Email sent successfully to {candidate_email}",
            "meeting_link": meeting_link,
            "token": meeting_token
        }
        
    except Exception as e:
        return {
            "success": False,
            "simulated": False,
            "message": f"Failed to send email: {str(e)}",
            "meeting_link": meeting_link,
            "token": meeting_token
        }


def save_meeting_store_to_file(filepath: str = "data/meetings.json") -> None:
    """Persist meeting store to file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(MEETING_STORE, f, indent=2, default=str)


def load_meeting_store_from_file(filepath: str = "data/meetings.json") -> None:
    """Load meeting store from file."""
    global MEETING_STORE
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            MEETING_STORE = json.load(f)
