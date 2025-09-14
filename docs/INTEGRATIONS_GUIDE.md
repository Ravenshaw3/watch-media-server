# 🔗 Watch Media Server - Integrations Guide

This comprehensive guide covers all the integrations available in your Watch Media Server, from external services to smart home automation.

## 📋 Table of Contents

1. [External Services Integration](#external-services-integration)
2. [Smart Home Integration](#smart-home-integration)
3. [Automation & Scheduling](#automation--scheduling)
4. [Webhooks & Notifications](#webhooks--notifications)
5. [Cloud Storage Integration](#cloud-storage-integration)
6. [Social Media Integration](#social-media-integration)
7. [Setup Instructions](#setup-instructions)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)

---

## 🌐 External Services Integration

### Trakt.tv Integration

**Purpose**: Sync your watchlist and viewing history with Trakt.tv

**Features**:
- Automatic sync of watchlist
- Viewing history synchronization
- Two-way data sync
- OAuth authentication

**Setup**:
1. Create a Trakt.tv application at https://trakt.tv/oauth/applications
2. Add your credentials to `.env`:
   ```bash
   TRAKT_CLIENT_ID=your_client_id
   TRAKT_CLIENT_SECRET=your_client_secret
   ```
3. Connect your account via the web interface

**API Endpoints**:
- `GET /api/integrations/external-services/auth-url/trakt` - Get OAuth URL
- `POST /api/integrations/external-services/sync/trakt` - Sync data

### Letterboxd Integration

**Purpose**: Import movie reviews and ratings from Letterboxd

**Features**:
- Import movie ratings
- Sync watchlist
- Review synchronization

**Setup**:
1. Get Letterboxd API credentials
2. Add to `.env`:
   ```bash
   LETTERBOXD_API_KEY=your_api_key
   LETTERBOXD_API_SECRET=your_api_secret
   ```

### IMDb Integration

**Purpose**: Enhanced metadata from IMDb

**Features**:
- Detailed movie information
- Cast and crew data
- Ratings and reviews
- Plot summaries

**Setup**:
1. Get IMDb API key from https://imdb-api.com/
2. Add to `.env`:
   ```bash
   IMDB_API_KEY=your_api_key
   ```

---

## 🏠 Smart Home Integration

### Amazon Alexa

**Purpose**: Voice control for your media server

**Supported Commands**:
- "Play [movie name]"
- "Pause the movie"
- "Resume playback"
- "Search for [movie name]"
- "Add [movie] to my watchlist"
- "What should I watch?"

**Setup**:
1. Create Alexa skill at https://developer.amazon.com/alexa/console/ask
2. Add credentials to `.env`:
   ```bash
   ALEXA_CLIENT_ID=your_client_id
   ALEXA_CLIENT_SECRET=your_client_secret
   ALEXA_SKILL_ID=your_skill_id
   ```
3. Enable the skill in your Alexa app

**API Endpoints**:
- `POST /api/integrations/smart-home/voice-command` - Handle voice commands

### Google Home/Assistant

**Purpose**: Google Assistant integration

**Features**:
- Voice control via Google Assistant
- Smart home device control
- Routine integration

**Setup**:
1. Create Google Cloud project
2. Enable Home Graph API
3. Add credentials to `.env`:
   ```bash
   GOOGLE_HOME_API_KEY=your_api_key
   GOOGLE_HOME_PROJECT_ID=your_project_id
   ```

### Home Assistant

**Purpose**: Integration with Home Assistant automation platform

**Features**:
- Control Home Assistant entities
- Trigger automations
- Device state monitoring
- Scene control

**Setup**:
1. Get Home Assistant API token
2. Add to `.env`:
   ```bash
   HOME_ASSISTANT_URL=http://your-ha-ip:8123
   HOME_ASSISTANT_TOKEN=your_long_lived_token
   ```

**API Endpoints**:
- `POST /api/integrations/smart-home/home-assistant/control` - Control entities

### Philips Hue

**Purpose**: Smart lighting integration

**Features**:
- Scene control based on media type
- Ambient lighting during playback
- Mood lighting for different genres

**Setup**:
1. Find your Hue bridge IP
2. Create username via API
3. Add to `.env`:
   ```bash
   PHILIPS_HUE_BRIDGE_URL=http://your-bridge-ip/api
   PHILIPS_HUE_USERNAME=your_username
   ```

**API Endpoints**:
- `POST /api/integrations/smart-home/philips-hue/scene` - Set scene

### Sonos

**Purpose**: Audio system integration

**Features**:
- Volume control
- Audio group management
- Playback control

**Setup**:
1. Get Sonos API credentials
2. Add to `.env`:
   ```bash
   SONOS_BASE_URL=http://your-sonos-ip:1400
   SONOS_API_KEY=your_api_key
   ```

---

## ⚙️ Automation & Scheduling

### Automated Tasks

**Purpose**: Schedule recurring tasks for maintenance and organization

**Available Task Types**:
- **Library Scan**: Automatically scan for new media
- **Database Cleanup**: Remove old logs and temporary data
- **File Organization**: Organize files by date, genre, etc.
- **Backup**: Create database backups
- **Transcode Cleanup**: Remove old transcoded files
- **Metadata Update**: Update media metadata from external sources
- **Custom Scripts**: Run custom automation scripts

**Schedule Formats**:
- `daily at 02:00` - Every day at 2 AM
- `weekly on monday` - Every Monday
- `every 30 minutes` - Every 30 minutes
- `every 2 hours` - Every 2 hours

**API Endpoints**:
- `GET /api/integrations/automation/tasks` - List tasks
- `POST /api/integrations/automation/tasks` - Create task
- `PUT /api/integrations/automation/tasks/{id}/toggle` - Toggle task
- `DELETE /api/integrations/automation/tasks/{id}` - Delete task

**Example Task Creation**:
```json
{
  "task_name": "Daily Library Scan",
  "task_type": "library_scan",
  "schedule_expression": "daily at 02:00",
  "task_config": {
    "scan_path": "/media/movies",
    "recursive": true
  }
}
```

### File Organization Rules

**Purpose**: Automatically organize media files

**Features**:
- Pattern-based file organization
- Date-based sorting
- Genre-based organization
- Custom naming conventions

**Example Rules**:
- Move movies to `/media/movies/{year}/{title}`
- Organize TV shows by `/media/tv/{show}/{season}`
- Sort by genre: `/media/{genre}/{title}`

---

## 🔔 Webhooks & Notifications

### Webhook Subscriptions

**Purpose**: Get notified of events in real-time

**Supported Events**:
- `media_added` - New media added to library
- `media_played` - Media playback started
- `media_completed` - Media playback completed
- `user_registered` - New user registered
- `library_scan_completed` - Library scan finished
- `transcode_completed` - Transcoding finished

**Setup**:
1. Create webhook endpoint in your application
2. Subscribe to events via API:
   ```json
   {
     "webhook_url": "https://your-app.com/webhook",
     "event_types": ["media_added", "media_played"],
     "secret_key": "your_secret_key"
   }
   ```

**API Endpoints**:
- `POST /api/integrations/external-services/webhooks` - Create subscription

### Notification Services

**Email Notifications**:
- Configure SMTP settings in `.env`
- Send notifications for important events
- Customizable email templates

**Telegram Notifications**:
- Send notifications via Telegram bot
- Rich media messages
- Interactive buttons

**Push Notifications**:
- Firebase Cloud Messaging (FCM)
- Web push notifications
- Mobile app notifications

---

## ☁️ Cloud Storage Integration

### Dropbox Integration

**Purpose**: Sync media files with Dropbox

**Features**:
- Automatic file sync
- Cloud backup
- Remote access

**Setup**:
1. Create Dropbox app at https://www.dropbox.com/developers/apps
2. Add credentials to `.env`:
   ```bash
   DROPBOX_CLIENT_ID=your_client_id
   DROPBOX_CLIENT_SECRET=your_client_secret
   ```

### Google Drive Integration

**Purpose**: Sync with Google Drive

**Features**:
- File synchronization
- Cloud storage
- Team sharing

**Setup**:
1. Create Google Cloud project
2. Enable Drive API
3. Add credentials to `.env`:
   ```bash
   GOOGLE_DRIVE_CLIENT_ID=your_client_id
   GOOGLE_DRIVE_CLIENT_SECRET=your_client_secret
   ```

---

## 📱 Social Media Integration

### Twitter Integration

**Purpose**: Share media recommendations on Twitter

**Features**:
- Share what you're watching
- Post reviews and ratings
- Automated sharing

**Setup**:
1. Create Twitter app at https://developer.twitter.com/
2. Add credentials to `.env`:
   ```bash
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_BEARER_TOKEN=your_bearer_token
   ```

**API Endpoints**:
- `POST /api/integrations/external-services/share/twitter` - Share to Twitter

### Facebook Integration

**Purpose**: Share media on Facebook

**Features**:
- Post to Facebook pages
- Share reviews
- Social engagement

**Setup**:
1. Create Facebook app at https://developers.facebook.com/
2. Add credentials to `.env`:
   ```bash
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   ```

---

## 🛠️ Setup Instructions

### 1. Environment Configuration

Copy the integration environment file:
```bash
cp env.integrations .env
```

Edit `.env` with your API keys and credentials.

### 2. Install Dependencies

The integration dependencies are already included in `requirements.txt`:
- `requests-oauthlib` - OAuth authentication
- `schedule` - Task scheduling
- `dropbox` - Dropbox integration
- `google-api-python-client` - Google services
- `tweepy` - Twitter integration
- `python-telegram-bot` - Telegram integration

### 3. Database Migration

The integration services will automatically create their database tables on first run.

### 4. Service Configuration

Each integration service can be configured through the web interface or API endpoints.

### 5. Testing Integrations

Use the web interface to test each integration:
1. Go to Settings → Integrations
2. Configure each service
3. Test connections
4. Verify functionality

---

## 📚 API Reference

### External Services API

**Base URL**: `/api/integrations/external-services`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth-url/{service}` | GET | Get OAuth authorization URL |
| `/callback/{service}` | GET | Handle OAuth callback |
| `/connections` | GET | Get service connections |
| `/sync/{service}` | POST | Sync with external service |
| `/share/{service}` | POST | Share media to service |
| `/webhooks` | POST | Create webhook subscription |
| `/logs` | GET | Get integration logs |

### Smart Home API

**Base URL**: `/api/integrations/smart-home`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/devices` | GET/POST | Manage smart home devices |
| `/voice-command` | POST | Handle voice commands |
| `/home-assistant/control` | POST | Control Home Assistant |
| `/philips-hue/scene` | POST | Set Philips Hue scene |
| `/voice-history` | GET | Get voice command history |

### Automation API

**Base URL**: `/api/integrations/automation`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tasks` | GET/POST | Manage automation tasks |
| `/tasks/{id}/toggle` | PUT | Toggle task status |
| `/tasks/{id}` | DELETE | Delete task |
| `/tasks/{id}/logs` | GET | Get task logs |

---

## 🔧 Troubleshooting

### Common Issues

**1. OAuth Authentication Fails**
- Check API credentials
- Verify redirect URLs
- Ensure proper scopes are requested

**2. Smart Home Commands Not Working**
- Verify device registration
- Check network connectivity
- Ensure proper authentication

**3. Automation Tasks Not Running**
- Check task status (active/inactive)
- Verify schedule expression format
- Review task logs for errors

**4. Webhook Notifications Not Received**
- Verify webhook URL is accessible
- Check secret key configuration
- Review webhook logs

### Debug Mode

Enable debug logging:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

### Log Files

Integration logs are stored in:
- Application logs: `./logs/watch.log`
- Integration logs: Database table `integration_logs`
- Automation logs: Database table `automation_logs`

### Support

For additional help:
1. Check the logs for error messages
2. Review the API documentation
3. Test integrations individually
4. Verify environment configuration

---

## 🚀 Advanced Features

### Custom Integrations

You can create custom integrations by:
1. Extending the base integration classes
2. Adding new API endpoints
3. Implementing custom authentication
4. Creating specialized automation tasks

### Integration Marketplace

Future plans include:
- Plugin system for custom integrations
- Community-contributed integrations
- Integration templates
- Automated setup wizards

### Enterprise Features

For enterprise deployments:
- SSO integration
- LDAP/Active Directory
- Advanced security features
- Multi-tenant support
- Custom branding

---

## 📈 Performance & Scaling

### Optimization Tips

1. **Caching**: Enable Redis caching for better performance
2. **Rate Limiting**: Configure appropriate rate limits
3. **Batch Operations**: Use bulk operations when possible
4. **Async Processing**: Use background tasks for heavy operations

### Monitoring

Monitor integration health:
- Use the health check endpoint
- Set up alerts for failed integrations
- Monitor API usage and limits
- Track performance metrics

---

This integrations guide provides everything you need to connect your Watch Media Server with external services and create a fully automated, connected media experience! 🎬✨
