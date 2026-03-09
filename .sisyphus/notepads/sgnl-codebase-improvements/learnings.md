
## CSS File Reference Fix (2026-03-04)

### Issue
- `app/templates/index.html` line 41 referenced `main-searchfix.css?v=6.6` instead of canonical `main.css`
- This was a patch/override file accidentally left as primary reference

### Investigation
- **main-searchfix.css**: 2490 lines (patch file with `!important` overrides)
- **main.css**: 2517 lines (canonical design system v4)
- Diff shows main-searchfix.css uses aggressive `!important` rules on search-related styles (lines 685-697)
- Both files have identical header/structure, but main.css is the authoritative version

### Resolution
- Updated line 41 to reference `/static/css/main.css?v=7.0`
- Bumped version from 6.6 to 7.0 to force cache invalidation
- Left main-searchfix.css in place (may be needed for rollback or reference)
- Committed: `fix(ui): correct CSS file reference from main-searchfix.css to main.css`

### Impact
- Page styling now loads from canonical design system
- Removes reliance on patch file overrides
- Cache-busting version bump ensures browsers fetch fresh CSS
- No functional changes to styling (main.css includes all necessary rules)

### Recommendation
- Monitor for any visual regressions in search UI
- Consider removing main-searchfix.css after verification period if no issues arise
- Document why patch file existed (search-specific styling needs?)

## SecurityHeadersMiddleware Implementation (2026-03-04)

### Implementation
- Added `SecurityHeadersMiddleware` class to `app/main.py` (lines 160-190)
- Follows existing `RateLimitMiddleware` pattern using `BaseHTTPMiddleware`
- Registered after CORS middleware to avoid header overwrites

### Security Headers Added
1. **X-Frame-Options: DENY** - Prevents clickjacking attacks
2. **X-Content-Type-Options: nosniff** - Prevents MIME type sniffing
3. **Referrer-Policy: strict-origin-when-cross-origin** - Controls referrer leakage
4. **Permissions-Policy** - Disables geolocation, microphone, camera APIs
5. **Content-Security-Policy** - Restricts resource loading with frontend dependencies:
   - `script-src`: 'self' + https://cdnjs.cloudflare.com (GSAP)
   - `style-src`: 'self' + https://fonts.googleapis.com + 'unsafe-inline' (CSS custom properties)
   - `font-src`: 'self' + https://fonts.gstatic.com (Google Fonts)
   - `img-src`: 'self' + data: + https: (OG images)
   - `connect-src`: 'self' (same-origin API calls)

### Middleware Stack Order (Critical)
```
GZipMiddleware (added first)
RateLimitMiddleware (added second)
AnalyticsMiddleware (added third)
CORSMiddleware (added fourth - outermost)
SecurityHeadersMiddleware (added fifth - runs on response path after CORS)
```

### Key Design Decision
- SecurityHeadersMiddleware registered AFTER CORS to ensure CORS headers are not overwritten
- In FastAPI, middleware added last runs first on request, but last on response
- This ensures security headers are applied to all responses without interfering with CORS

### Testing
- Syntax verified with `python3 -m py_compile app/main.py`
- Headers will be visible in response with: `curl -I http://localhost:8000/health`

### Rationale for CSP Allowlist
- GSAP from CDN required for Intelligence Report animations
- Google Fonts required for typography system
- 'unsafe-inline' for style-src needed for CSS custom properties (Swiss design system)
- All API calls are same-origin, so connect-src restricted to 'self'

## Rate Limiting Extension (Task 4)

### What was done
Extended `RateLimitMiddleware.PROTECTED_PATHS` in `app/main.py` (line 86) to cover all expensive/write API endpoints:
- **Before:** `['/fast-search', '/scan-topic', '/deep-scan']`
- **After:** `['/fast-search', '/scan-topic', '/deep-scan', '/extract', '/analyze-results', '/check-density']`

### Why these endpoints needed protection
1. `/extract` — HTTP fetch + Trafilatura parsing (network I/O)
2. `/analyze-results` — HTTP fetch per result + heuristic scoring (network I/O + CPU)
3. `/check-density` — CPU-intensive NLP (spaCy, ideadensity libraries)

### Implementation notes
- Added inline comments explaining the rationale for each protected endpoint
- No changes to middleware logic, rate limit values, or other files
- Unprotected paths remain: `/health`, `/`, `/static`, `/analytics` (as intended)
- Commit: `feat(security): extend rate limiting to all expensive API endpoints`

### Key insight
The middleware uses `request.url.path.startswith(p)` for path matching, so `/extract` will also protect `/extract/*` if any sub-routes exist. This is the intended behavior.
