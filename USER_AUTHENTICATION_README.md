# User Authentication System for GenAI Mediaplan

This document explains how to set up and use the new user authentication system that allows users to save presentations to their own Google Drive.

## Overview

The system now supports:
- **OAuth 2.0 Authentication**: Users can authenticate with their Google accounts
- **User-specific Presentations**: Each user can create and save presentations to their own Google Drive
- **Secure Credential Management**: User credentials are managed securely in memory
- **Simple Frontend Interface**: Easy-to-use web interface for authentication and mediaplan generation

## Prerequisites

1. **Google Cloud Project**: You need a Google Cloud project with the Google Drive API enabled
2. **OAuth 2.0 Credentials**: Download the OAuth client credentials file
3. **Python Dependencies**: Install required packages

## Setup Instructions

### 1. Google Cloud Project Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Drive API
   - Google Slides API
   - Google Sheets API

### 2. OAuth 2.0 Credentials Setup

1. In the Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application" as the application type
4. Add authorized redirect URIs:
   - `http://localhost:3000/callback` (for development)
   - `http://localhost:8000/auth/callback` (for API server)
5. Download the client credentials JSON file
6. Rename it to `client_secret_drive.json` and place it in the project root

### 3. Environment Variables

Create or update your `.env` file with the following variables:

```env
SOURCE_FILE_ID=your_source_presentation_id
SOURCE_SHEET_ID=your_source_sheet_id
SHARED_FOLDER_ID=your_shared_folder_id
```

### 4. Install Dependencies

```bash
# Install additional dependencies for OAuth
pip install google-auth-oauthlib google-auth-httplib2
```

## Running the Application

### 1. Start the API Server

```bash
cd src/genai_mediaplan
python api.py
```

The API server will start on `http://localhost:8000`

### 2. Start the Frontend Server

```bash
cd frontend
python server.py
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Authentication Endpoints

#### Start OAuth Flow
```http
POST /auth/start
Content-Type: application/json

{
    "user_id": "unique_user_id",
    "redirect_uri": "http://localhost:3000/callback"
}
```

#### Handle OAuth Callback
```http
POST /auth/callback
Content-Type: application/json

{
    "user_id": "unique_user_id",
    "authorization_code": "oauth_authorization_code"
}
```

#### Set User Credentials
```http
POST /auth/set-credentials
Content-Type: application/json

{
    "user_id": "unique_user_id",
    "credentials_data": {
        "access_token": "...",
        "refresh_token": "...",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "...",
        "client_secret": "...",
        "scopes": ["https://www.googleapis.com/auth/drive"]
    }
}
```

#### Check Authentication Status
```http
GET /auth/status/{user_id}
```

#### Logout User
```http
DELETE /auth/logout/{user_id}
```

### User-specific Mediaplan Endpoints

#### Generate Mediaplan for User
```http
POST /user/generate-mediaplan
Content-Type: application/json

{
    "user_id": "unique_user_id",
    "cohort_name": "Shopping",
    "audience_data": {...},  // Optional
    "forecast_data": {...}   // Optional
}
```

#### Update User's Presentation
```http
POST /user/update-presentation
Content-Type: application/json

{
    "user_id": "unique_user_id",
    "cohort_name": "Shopping",
    "presentation_id": "google_slides_presentation_id",
    "audience_data": {...},  // Optional
    "forecast_data": {...}   // Optional
}
```

## Using the Frontend

### 1. Open the Frontend

Navigate to `http://localhost:3000` in your browser.

### 2. Set User ID

1. Enter a unique user ID (e.g., "john_doe_123")
2. Click "Set User ID"

### 3. Authenticate with Google

1. Click "Start Google Authentication"
2. A new window will open with Google's OAuth consent screen
3. Sign in with your Google account
4. Grant the necessary permissions (Google Drive access)
5. The window will close automatically
6. Click "Check Authentication Status" to verify

### 4. Generate Mediaplan

1. Select a cohort from the dropdown
2. Click "Generate Mediaplan"
3. The system will:
   - Run the CrewAI agents to generate insights
   - Create a new presentation in your Google Drive
   - Return a link to the presentation

### 5. Update Existing Presentation

1. Select a cohort from the dropdown
2. Enter the Google Slides presentation ID
3. Click "Update Presentation"
4. The system will update the existing presentation with new content

## Security Considerations

### Credential Storage
- User credentials are stored in memory only (not persisted to disk)
- Credentials are automatically refreshed when expired
- Users can logout to remove their credentials

### OAuth Flow
- Uses standard OAuth 2.0 authorization code flow
- Authorization codes are exchanged for access tokens
- Refresh tokens are used to maintain long-term access

### API Security
- CORS is enabled for frontend communication
- User authentication is verified before any Google Drive operations
- Each user's credentials are isolated

## Troubleshooting

### Common Issues

1. **"User not authenticated" Error**
   - Make sure you've completed the OAuth flow
   - Check that the user ID matches between auth and generation requests
   - Try logging out and re-authenticating

2. **"Failed to create auth URL" Error**
   - Verify that `client_secret_drive.json` is in the correct location
   - Check that the Google Cloud project has the necessary APIs enabled
   - Ensure the redirect URI is properly configured

3. **"Permission denied" Error**
   - Make sure the Google account has access to Google Drive
   - Check that the OAuth consent screen includes the necessary scopes
   - Verify that the application is properly configured in Google Cloud Console

4. **CORS Errors**
   - Ensure the frontend server is running on the correct port
   - Check that the API server has CORS middleware enabled
   - Verify that the frontend is making requests to the correct API URL

### Debug Mode

To enable debug logging, add the following to your environment:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
export LOG_LEVEL=DEBUG
```

## File Structure

```
genai_mediaplan/
├── src/genai_mediaplan/
│   ├── api.py                          # Main API server
│   ├── utils/
│   │   ├── auth_manager.py             # OAuth authentication manager
│   │   ├── user_slides_manager.py      # User-specific slides operations
│   │   └── update_google_slides_content.py  # Original slides manager
├── frontend/
│   ├── index.html                      # Frontend interface
│   └── server.py                       # Frontend server
├── client_secret_drive.json            # OAuth credentials
└── .env                                # Environment variables
```

## Production Deployment

For production deployment, consider:

1. **HTTPS**: Use HTTPS for all OAuth redirects
2. **Database**: Store user credentials securely in a database
3. **Session Management**: Implement proper session management
4. **Rate Limiting**: Add rate limiting to prevent abuse
5. **Monitoring**: Add logging and monitoring for OAuth flows
6. **Security Headers**: Implement proper security headers
7. **Environment Variables**: Use environment variables for all sensitive data

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the Google Cloud Console for API quotas and errors
3. Check the application logs for detailed error messages
4. Ensure all dependencies are properly installed 