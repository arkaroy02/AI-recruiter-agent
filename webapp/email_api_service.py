"""Email service using HTTP API (works on cloud platforms that block SMTP)."""

from __future__ import annotations

import os
import requests
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
        "status": "pending",
        "joined_at": None,
        "interview_answers": [],
    }
    
    return token


def validate_meeting_token(token: str) -> Optional[Dict]:
    """Validate a meeting token and return meeting info if valid."""
    meeting = MEETING_STORE.get(token)
    if not meeting:
        return None
    
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


def send_email_via_brevo_api(
    candidate_email: str,
    candidate_name: str,
    meeting_token: str,
    company_name: str = "Talent Scout Studio",
    base_url: str = "http://localhost:8000"
) -> Dict:
    """
    Send email using Brevo HTTP API (works on cloud platforms).
    """
    api_key = os.getenv("BREVO_API_KEY", "")
    
    if not api_key:
        return {
            "success": False,
            "simulated": True,
            "message": "BREVO_API_KEY not configured. Email simulated.",
            "meeting_link": f"{base_url}/interview/{meeting_token}",
            "token": meeting_token
        }
    
    meeting_link = f"{base_url}/interview/{meeting_token}"
    
    html_content = f"""
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
                
                <p>We're excited to inform you that your profile has been shortlisted for an interview opportunity!</p>
                
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
                
                <p><strong>Important:</strong> This link will expire in 48 hours.</p>
                
                <p>Best regards,<br><strong>{company_name} Recruitment Team</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": api_key
            },
            json={
                "sender": {
                    "name": company_name,
                    "email": os.getenv("FROM_EMAIL", "noreply@interview.ikbal.work")
                },
                "to": [
                    {
                        "email": candidate_email,
                        "name": candidate_name
                    }
                ],
                "subject": f"Interview Invitation from {company_name}",
                "htmlContent": html_content
            },
            timeout=30
        )
        
        if response.status_code == 201:
            return {
                "success": True,
                "simulated": False,
                "message": f"Email sent successfully to {candidate_email}",
                "meeting_link": meeting_link,
                "token": meeting_token
            }
        else:
            return {
                "success": False,
                "simulated": False,
                "message": f"Brevo API error: {response.status_code} - {response.text}",
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


def send_meeting_email(
    candidate_email: str,
    candidate_name: str,
    meeting_token: str,
    company_name: str = "Talent Scout Studio",
    base_url: str = "http://localhost:8000"
) -> Dict:
    """
    Send meeting invitation email using HTTP API.
    """
    # Try Brevo API first
    brevo_api_key = os.getenv("BREVO_API_KEY", "")
    if brevo_api_key:
        return send_email_via_brevo_api(
            candidate_email, candidate_name, meeting_token, company_name, base_url
        )
    
    # Fallback to simulation
    meeting_link = f"{base_url}/interview/{meeting_token}"
    return {
        "success": True,
        "simulated": True,
        "message": "Email simulated (no BREVO_API_KEY configured)",
        "meeting_link": meeting_link,
        "token": meeting_token,
        "note": "Set BREVO_API_KEY in environment to send real emails"
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
