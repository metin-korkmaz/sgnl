# SGNL Analytics Implementation - Summary

## What Was Built

A complete, production-ready analytics system that captures visitor data **for free** using your existing infrastructure.

### Features Implemented

✅ **IP Address Tracking** - Capture visitor IPs
✅ **Device Detection** - Desktop/mobile/tablet via User-Agent parsing
✅ **Session Management** - Cookie-based visitor sessions
✅ **Page View Tracking** - Track every page visit
✅ **Time on Page** - Measure how long users spend on each page
✅ **Heartbeat System** - Active session tracking every 30 seconds
✅ **Referrer Tracking** - Know where visitors come from
✅ **90-Day Retention** - Automatic data cleanup
✅ **API Dashboard** - Query analytics via REST API
✅ **Zero Cost** - Uses SQLite (PostgreSQL option available)

## Files Created

| File | Purpose |
|------|---------|
| `app/analytics_models.py` | Database models (VisitorLog, PageView, AnalyticsEvent) |
| `app/analytics_middleware.py` | Request tracking middleware |
| `app/analytics_routes.py` | Analytics API endpoints |
| `app/analytics_utils.py` | Utility functions (create visitor, cleanup) |
| `app/static/js/analytics.js` | Client-side tracking script |
| `init_analytics.py` | Database initialization script |
| `docs/ANALYTICS.md` | Complete documentation |

## Files Modified

| File | Changes |
|------|---------|
| `app/main.py` | Added analytics imports, middleware, routes |
| `app/requirements.txt` | Added SQLAlchemy, user-agent dependencies |
| `app/templates/index.html` | Added analytics.js script tag |
| `docker-compose.yml` | Added database volume mount |
| `.env.example` | Added DATABASE_URL configuration |
| `.gitignore` | Added database files to ignore list |

## How It Works

```
User visits website → 
    ↓
Cookie checked (sgnl_session) →
    ↓
New visitor record created →
    ↓
JavaScript beacon sends pageview →
    ↓
Heartbeat every 30s keeps session alive →
    ↓
On page exit: time-on-page recorded →
    ↓
All data stored in database
```

## Quick Start

### 1. Set Database URL

Edit `.env` file:
```bash
# Default: SQLite (recommended for <100 users/month)
DATABASE_URL=sqlite:///./app/analytics.db

# Or PostgreSQL (if you already have it):
DATABASE_URL=postgresql://user:password@localhost:5432/sgnl
```

### 2. Rebuild Container

```bash
docker-compose down
docker-compose up -d --build
```

### 3. Verify Analytics Working

Visit your site. Check browser DevTools → Network tab:
- Look for requests to `/analytics/pageview`
- Look for heartbeats to `/analytics/heartbeat`

### 4. View Analytics Data

```bash
# Get statistics
curl http://localhost:8000/analytics/stats

# Get recent visitors
curl "http://localhost:8000/analytics/visitors?limit=20"

# Access interactive API docs
open http://localhost:8000/docs
```

## Data Captured

Per visitor:
- **IP address** (e.g., 192.168.1.1)
- **User Agent** (e.g., Mozilla/5.0...)
- **Device type** (mobile/desktop/tablet)
- **Referrer** (source of visit)
- **Landing page** (first page visited)
- **Session ID** (unique cookie identifier)
- **Timestamps** (created_at, last_activity)
- **Total time** (cumulative time on site)

Per page view:
- **Path** (URL path)
- **Time on page** (seconds)
- **Timestamp** (when page was viewed)

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/analytics/track` | POST | Track custom events |
| `/analytics/heartbeat` | POST | Keep session alive |
| `/analytics/pageview` | POST | Record page view |
| `/analytics/stats` | GET | Get statistics |
| `/analytics/visitors` | GET | Get visitor list |
| `/analytics/cleanup` | POST | Delete old data |

## Data Management

### Automatic Cleanup

Run weekly to maintain 90-day retention:

```bash
# Add to crontab
0 2 * * 0 curl -X POST "http://localhost:8000/analytics/cleanup?days=90"
```

### Manual Cleanup

```bash
# Delete data older than 90 days
curl -X POST "http://localhost:8000/analytics/cleanup?days=90"

# Delete data older than 30 days
curl -X POST "http://localhost:8000/analytics/cleanup?days=30"
```

## Database Location

### SQLite (Default)
- File: `./app/analytics.db` (inside container)
- Volume: `./analytics_data` (on host)
- Backup: Copy `analytics_data` directory

### PostgreSQL (Optional)
- Uses your existing PostgreSQL instance
- No volume needed (database handles persistence)
- Configure via `DATABASE_URL` in `.env`

## Example: View Analytics in Terminal

```bash
# Quick stats
curl -s http://localhost:8000/analytics/stats | python3 -m json.tool

# Get top 10 visitors
curl -s "http://localhost:8000/analytics/visitors?limit=10" | python3 -m json.tool
```

## Privacy & Compliance

- **IP addresses stored**: ✓ (per your requirement)
- **No GDPR compliance**: ✓ (per your requirement)
- **90-day retention**: ✓ (configurable)
- **Cookie-based tracking**: ✓ (sgnl_session cookie)
- **No 3rd party trackers**: ✓ (self-hosted)

## Comparison: vs Cloudflare Analytics

| Feature | Cloudflare | SGNL Analytics |
|---------|-----------|-----------------|
| IP tracking | Yes | ✓ |
| Device detection | Limited | ✓ |
| Time on page | ❌ | ✓ |
| Page views | Yes | ✓ |
| Referrers | Yes | ✓ |
| Custom events | ❌ | ✓ |
| Data ownership | Cloudflare's | Yours (100%) |
| Cost | Business/Enterprise | FREE |
| Retention | Limited | Configurable (90d+) |
| Privacy | GDPR compliant | No GDPR |

## Troubleshooting

### Analytics Not Tracking

1. Check browser console for JavaScript errors
2. Verify `/static/js/analytics.js` loads (Network tab)
3. Check middleware logs: `docker logs -f sgnl-api`

### Database Errors

**SQLite locked:**
- SQLite supports single writer
- Switch to PostgreSQL for high traffic

**Permission denied:**
```bash
chmod 755 ./analytics_data
```

### Missing Data

**No visitors showing:**
- Check `app/main.py` line ~158: `await create_visitor()` runs on each visit
- Verify cookie is being set: `document.cookie` in browser console

**No pageviews:**
- Check `analytics.js` is loaded in HTML
- Look for network requests to `/analytics/pageview`

## Next Steps

**Week 1:**
- [ ] Test tracking with multiple devices
- [ ] Verify data appears in database
- [ ] Test cleanup endpoint

**Week 2:**
- [ ] Set up automated weekly cleanup
- [ ] Create simple dashboard (optional)
- [ ] Review initial analytics data

**Future Enhancements:**
- [ ] Build admin dashboard UI
- [ ] Add geographic location (city/country)
- [ ] Export data to CSV
- [ ] Real-time visitor counter
- [ ] Heatmap tracking

## Support

- Documentation: `docs/ANALYTICS.md`
- API Docs: http://your-domain.com/docs
- Health Check: http://your-domain.com/health

## Cost Breakdown

| Component | Cost |
|-----------|-------|
| SQLite database | $0 (included) |
| Python dependencies | $0 (open source) |
| Docker containers | $0 (free tier) |
| Storage | $0 (few MB) |
| **Total** | **$0/month** |

---

**Implementation complete. Start tracking users immediately!**
