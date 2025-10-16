# Step 8 Setup Instructions - Collaborators, Targeted Versions & Pricing

## Overview
This step adds collaboration features, targeted resume generation, and prepares the foundation for SaaS billing tiers.

## Features Added
- **Collaboration Roles**: Invite viewers, commenters, and editors
- **Targeted Resume Generation**: Auto-tailor resumes for specific job descriptions
- **Advanced Analytics**: Resume-JD matching analysis
- **User Access Control**: Role-based permissions
- **Database Schema**: Support for collaboration and billing tiers

## 1. Database Setup

Run the SQL commands in `SETUP_STEP8_DATABASE.sql` in your Supabase SQL editor:

```bash
# Copy the contents of SETUP_STEP8_DATABASE.sql and run in Supabase
```

This creates:
- `collaborators` table for sharing resumes
- `user_tiers` table for billing tiers (free/pro/recruiter)
- `usage_tracking` table for analytics
- Enhanced RLS policies for collaboration
- Helper functions for access control

## 2. Backend API Setup

The following new API endpoints are available:

### Collaboration Endpoints (`/api/collab/`)
- `POST /invite` - Invite a collaborator
- `POST /accept` - Accept collaboration invite
- `GET /collaborators/{resume_id}` - Get resume collaborators
- `DELETE /collaborators/{collaborator_id}` - Remove collaborator
- `GET /role/{resume_id}` - Get user's role for resume

### Targeted Resume Endpoints (`/api/target/`)
- `POST /target` - Create targeted resume version
- `GET /targeted/{base_resume_id}` - Get targeted versions
- `POST /analyze-match` - Analyze resume-JD match

## 3. Frontend Features

### Dashboard Updates
- Resume management with collaboration buttons
- Quick actions sidebar
- Real-time resume listing

### Editor Enhancements
- **🎯 Tailor for JD** button - Creates targeted resume versions
- **📊 Match Analysis** button - Analyzes resume-JD compatibility
- Enhanced collaboration features

### Collaboration Flow
1. User clicks "Share" on a resume
2. Enters collaborator email and role
3. System sends invite with token
4. Collaborator accepts via `/accept?token=...`
5. Access granted based on role (viewer/commenter/editor)

## 4. Environment Variables

Ensure these are set in your backend `.env`:

```env
OPENAI_API_KEY=your-openai-api-key
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## 5. Testing the Features

### Test Collaboration
1. Create a resume in the editor
2. Click "Share" button
3. Enter an email address and select role
4. Check that invite is created in database
5. Test invite acceptance flow

### Test Targeted Resumes
1. Paste a job description in the editor
2. Click "🎯 Tailor for JD" button
3. Enter a job title
4. Verify new targeted resume is created
5. Check that it's linked to the base resume via `parent_id`

### Test Match Analysis
1. Paste a job description
2. Click "📊 Match Analysis" button
3. Review the detailed analysis results
4. Verify score, strengths, weaknesses, and recommendations

## 6. Role-Based Access Control

### Roles and Permissions
- **Owner**: Full access (create, read, update, delete, share)
- **Editor**: Can edit content and add comments
- **Commenter**: Can only add and view comments
- **Viewer**: Read-only access

### Database Functions
- `can_access_resume(resume_uuid)` - Check if user can access resume
- `get_resume_role(resume_uuid)` - Get user's role for resume

## 7. Usage Tracking

The system now tracks:
- Resume creation and editing
- Collaboration invites
- Targeted resume generation
- Analysis requests

This data can be used for:
- Billing calculations
- Usage analytics
- Feature limits enforcement

## 8. Next Steps for Production

### Email Integration
Replace the simple alert with actual email sending:
```python
# In production, integrate with email service
# SendGrid, AWS SES, or similar
send_invite_email(email, invite_link)
```

### Billing Integration
Implement tier-based limits:
- Free: 3 resumes, 5 collaborations
- Pro: Unlimited resumes, 20 collaborations
- Recruiter: Unlimited everything + team management

### Enhanced UI
- Replace alerts with proper modals
- Add collaboration management interface
- Implement real-time notifications

## 9. API Documentation

Visit `http://localhost:8000/docs` to see the interactive API documentation for all new endpoints.

## 10. Troubleshooting

### Common Issues
1. **Collaboration not working**: Check RLS policies and user authentication
2. **Targeted resume fails**: Verify OpenAI API key and quota
3. **Permission denied**: Ensure user has proper role for the resume
4. **Database errors**: Check that all tables and functions were created correctly

### Debug Steps
1. Check browser console for errors
2. Verify API endpoints are accessible
3. Check Supabase logs for database issues
4. Test with different user accounts

## 11. Security Considerations

- All collaboration actions require authentication
- RLS policies enforce access control at database level
- Invite tokens are UUIDs (not easily guessable)
- User roles are validated on every request

This completes Step 8 - your RoleReady application now supports collaboration and targeted resume generation!
