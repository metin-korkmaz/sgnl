# SGNL Analytics System

## Overview

Built-in visitor analytics tracking for SGNL. Captures:
- IP addresses
- User agents (device type detection)
- Page views and time spent on pages
- Session tracking via cookies
- Referrer sources
- Visit timestamps

## Architecture

### Backend Components

1. **Database Models** (`analytics_models.py`)
   - `VisitorLog`: Visitor sessions with IP, device, referrer
   - `PageView`: Individual page visits with time-on-page
   - `AnalyticsEvent`: Custom event tracking

2. **Middleware** (`analytics_middleware.py`)
   - Tracks all incoming requests
   - Updates visitor last_activity timestamp
   - Parses User-Agent for device detection

3. **API Routes** (`analytics_routes.py`)
   - `POST /analytics/track` - Track custom events
   - `POST /analytics/heartbeat` - Session heartbeat (30s interval)
   - `POST /analytics/pageview` - Record page view with time spent
   - `GET /analytics/stats` - Get aggregate statistics
   - `GET /analytics/visitors` - Get visitor list
   - `POST /analytics/cleanup` - Delete old data (default: 90 days)

4. **Utilities** (`analytics_utils.py`)
   - Create new visitor records
   - Cleanup old data (90-day retention)

### Frontend Components

1. **Client-side Script** (`static/js/analytics.js`)
   - Session management via cookies
   - Page load tracking
   - Heartbeat pings every 30 seconds
   - Time-on-page calculation
   - Uses `navigator.sendBeacon()` for reliable tracking

## Setup

### 1. Configure Database

Edit `.env` file:
```bash
# Default: SQLite (no setup required)
DATABASE_URL=sqlite:///./analytics.db

# For PostgreSQL:
DATABASE_URL=postgresql://user:password@localhost:5432/sgnl

# For MySQL:
DATABASE_URL=mysql://user:password@localhost:3306/sgnl
```

### 2. Install Dependencies

```bash
pip install -r app/requirements.txt
```

New dependencies:
- `sqlalchemy>=2.0.0`
- `user-agent>=0.1.10`

### 3. Database Initialization

Database tables are created automatically on startup via `init_db()` in `analytics_middleware.py`.

### 4. Start Application

```bash
docker-compose up -d --build
```

The analytics system initializes automatically.

## Usage

### Automatic Tracking

Analytics are collected automatically for all visitors:
- **First visit**: Creates visitor record in database
- **Page loads**: Tracks page views
- **Heartbeats**: Updates session activity every 30s
- **Page exit**: Records time spent on page

### Manual Tracking

Use `SGNLAnalytics` global in your JavaScript:

```javascript
// Track custom event
SGNLAnalytics.trackEvent('button_click', '{"button": "search"}');

// Get session ID
const sessionId = SGNLAnalytics.getSessionId();
```

### View Analytics

**Get Statistics:**
```bash
curl http://localhost:8000/analytics/stats
```

**Get Visitor List:**
```bash
curl "http://localhost:8000/analytics/visitors?limit=50"
```

**Clean Old Data (90+ days):**
```bash
curl -X POST "http://localhost:8000/analytics/cleanup?days=90"
```

## Data Retention

- **Default**: 90 days
- **Cleanup**: Manual via `/analytics/cleanup` endpoint
- **Recommendation**: Set up cron job to run cleanup weekly:

```bash
# Add to crontab (runs weekly at 2 AM)
0 2 * * 0 curl -X POST "http://localhost:8000/analytics/cleanup?days=90"
```

## Privacy Considerations

- IP addresses are stored
- No GDPR compliance (per your requirement)
- User agents captured (includes browser/OS info)
- Referrers captured (source of traffic)
- Cookie-based session tracking (90-day expiry)

## Database Schema

### visitor_logs
```sql
id INTEGER PRIMARY KEY
session_id VARCHAR(100) UNIQUE
ip_address VARCHAR(50)
user_agent TEXT
device_type VARCHAR(20)
country VARCHAR(50)
city VARCHAR(100)
referrer TEXT
landing_page VARCHAR(500)
created_at DATETIME
last_activity DATETIME
is_active BOOLEAN
total_time_seconds FLOAT
```

### page_views
```sql
id INTEGER PRIMARY KEY
session_id VARCHAR(100)
path VARCHAR(500)
query_params TEXT
time_on_page FLOAT
created_at DATETIME
```

### analytics_events
```sql
id INTEGER PRIMARY KEY
session_id VARCHAR(100)
event_type VARCHAR(50)
event_data TEXT
created_at DATETIME
```

## Example Queries

### Unique Visitors by Day
```sql
SELECT 
    DATE(created_at) as date,
    COUNT(DISTINCT ip_address) as unique_visitors
FROM visitor_logs
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Average Time on Site
```sql
SELECT AVG(total_time_seconds) as avg_time
FROM visitor_logs
WHERE created_at >= NOW() - INTERVAL '7 days';
```

### Most Visited Pages
```sql
SELECT 
    path,
    COUNT(*) as visits,
    AVG(time_on_page) as avg_time_on_page
FROM page_views
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY path
ORDER BY visits DESC
LIMIT 10;
```

## Troubleshooting

**Database locked error (SQLite):**
- SQLite supports only one writer at a time
- Switch to PostgreSQL for production

**Missing analytics:**
- Check browser console for JavaScript errors
- Verify `/static/js/analytics.js` is loaded
- Check network tab for beacon requests

**Old data not deleted:**
- Run `/analytics/cleanup` endpoint manually
- Set up cron job for automated cleanup

## Future Enhancements

- [ ] Geolocation (city/country from IP)
- [ ] Heatmap of scroll behavior
- [ ] Funnel analysis
- [ ] Real-time dashboard
- [ ] Export to CSV
- [ ] UTM parameter tracking
