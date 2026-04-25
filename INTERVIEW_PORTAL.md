# Interview Portal & Meeting Links (Experimental Feature)

This is an **experimental feature** that allows recruiters to send meeting links to shortlisted candidates. Candidates can then access a self-paced interview portal.

## Features

- 📧 **Email Meeting Links** - Send branded interview invitation emails to shortlisted candidates
- 🔗 **Unique Meeting Tokens** - Each candidate gets a unique, secure link (expires in 48 hours)
- 📝 **Self-Paced Interview Portal** - Candidates answer questions at their convenience
- 📊 **Status Tracking** - Track pending, joined, and completed interviews
- 🎨 **Beautiful UI** - Modern, responsive interview portal

## How It Works

### 1. Run the Pipeline
1. Paste a job description
2. Run the pipeline (Demo or Real mode)
3. View the shortlisted candidates

### 2. Send Meeting Link
1. Click on a candidate card to view their details
2. Scroll to the "📧 Interview Portal (Experimental)" section
3. Enter the candidate's email address
4. Click "Send Meeting Link"

### 3. Candidate Experience
1. Candidate receives an email with a meeting link
2. They click the link to access the interview portal
3. They answer the interview questions
4. Their responses are saved and marked as completed

### 4. Review Responses
- The recruiter can view the candidate's status (pending/joined/completed)
- Click "View Interview Portal" to see the candidate's responses

## Configuration

### Email Settings (Optional)

To send real emails, configure SMTP settings in `.env`:

```env
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Base URL for meeting links
BASE_URL=http://localhost:8000
```

#### Gmail Setup
1. Enable 2-factor authentication on your Google account
2. Go to Google Account → Security → App passwords
3. Generate a new app password for "Mail"
4. Use that password as `SMTP_PASSWORD`

#### Other Providers
- **Outlook**: `SMTP_HOST=smtp-mail.outlook.com`
- **SendGrid**: `SMTP_HOST=smtp.sendgrid.net`
- **Amazon SES**: `SMTP_HOST=email-smtp.region.amazonaws.com`

### Without SMTP Configuration
If SMTP is not configured, the system will:
- Simulate email sending
- Display the meeting link in the UI
- Show a warning that email was simulated

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/shortlist/send-email` | POST | Send meeting link to candidate |
| `/interview/{token}` | GET | Render interview portal |
| `/api/interview/validate/{token}` | GET | Validate meeting token |
| `/api/interview/join/{token}` | POST | Mark candidate as joined |
| `/api/interview/submit/{token}` | POST | Submit interview answers |
| `/api/meetings/{run_id}` | GET | Get all meetings for a run |
| `/api/meeting/{token}` | GET | Get meeting status |

## Request/Response Examples

### Send Email
```json
POST /api/shortlist/send-email
{
  "run_id": "abc123",
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "company_name": "Acme Corp"
}

Response:
{
  "success": true,
  "simulated": false,
  "message": "Email sent successfully to john@example.com",
  "meeting_link": "http://localhost:8000/interview/xyz789",
  "token": "xyz789",
  "candidate_name": "John Doe"
}
```

### Validate Token
```json
GET /api/interview/validate/xyz789

Response:
{
  "valid": true,
  "meeting": {
    "token": "xyz789",
    "candidate_name": "John Doe",
    "status": "pending",
    "expires_at": "2026-04-27T12:00:00"
  },
  "candidate": { ... },
  "questions": [
    "Tell us about yourself...",
    "What interests you most about this role...",
    ...
  ]
}
```

## Security Features

- **Token Expiry**: Meeting links expire after 48 hours
- **Unique Tokens**: Each candidate gets a unique UUID token
- **Status Tracking**: Track if link was used
- **No Authentication Required**: Candidates access via secure token only

## Future Enhancements (Ideas)

- [ ] Video interview recording
- [ ] Scheduled interview times
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Automated reminder emails
- [ ] Interview analytics dashboard
- [ ] Custom question templates
- [ ] Multi-round interviews
- [ ] Team collaboration features

## Troubleshooting

### Email Not Sending
1. Check SMTP credentials in `.env`
2. Verify `SMTP_PASSWORD` is an app password (not regular password for Gmail)
3. Check firewall allows outbound SMTP connections
4. Review server logs for error messages

### Link Shows as Expired
- Links expire after 48 hours
- Generate a new link by sending another email

### Candidate Can't Access Portal
1. Verify the token is correct in the URL
2. Check if link has expired
3. Ensure the server is running and accessible

## Files Modified

- `webapp/email_service.py` - Email sending and meeting token management
- `webapp/main.py` - API endpoints for interview portal
- `webapp/templates/interview_portal.html` - Candidate-facing interview UI
- `webapp/static/app.js` - Frontend integration
- `.env` - Configuration for SMTP and base URL
