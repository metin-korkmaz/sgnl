# Deployment Checklist

## Pre-Deployment Checklist

### Code Changes
- [x] Removed hardcoded IP addresses from code
- [x] Added proper CORS configuration with environment variables
- [x] Added validation for n8n webhook URLs
- [x] Updated error handling for missing configuration

### Environment Configuration
- [x] Created `.env.example` with domain-based URLs
- [x] Created `.env.dev` for development
- [x] Created `.env.prod` template for production
- [x] Added `ALLOWED_ORIGINS` variable for CORS control

### Docker Configuration
- [x] Updated `docker-compose.yml` for production (nginx-proxy_default network)
- [x] Created `docker-compose.dev.yml` for development
- [x] Changed from `ports:` to `expose:` in production config
- [x] Added `ALLOWED_ORIGINS` environment variable

### Documentation
- [x] Created comprehensive `DEPLOYMENT.md`
- [x] Updated `README.md` with security section
- [x] Added environment variable documentation
- [x] Added troubleshooting guide

### Git Configuration
- [x] Updated `.gitignore` to exclude environment files
- [x] Added `.env.prod` and `.env.dev` to `.gitignore`
- [x] Added deployment config files to `.gitignore`

## Pre-Deployment Actions

### 1. Prepare Production Environment File

```bash
# Copy production template
cp .env.prod .env

# Edit with your actual credentials
nano .env
```

**Required values to set:**
- [ ] `OPENAI_API_KEY` - Your production OpenAI API key
- [ ] `TAVILY_API_KEY` - Your production Tavily API key

**Verify these are set correctly:**
- [ ] `N8N_WEBHOOK_URL` - Should be `http://n8n.metinkorkmaz.quest/webhook/sgnl/scan-topic`
- [ ] `N8N_FAST_SEARCH_URL` - Should be `http://n8n.metinkorkmaz.quest/webhook/fast-search`
- [ ] `ALLOWED_ORIGINS` - Should be `https://sgnl.metinkorkmaz.quest`

### 2. Verify n8n Configuration

```bash
# Test n8n is accessible
curl http://n8n.metinkorkmaz.quest/healthz

# Expected: HTTP 200 response
```

- [ ] n8n responds to health check
- [ ] n8n webhooks are accessible

### 3. Check Docker Network

```bash
# Verify nginx-proxy_default network exists
docker network ls | grep nginx-proxy

# Expected: nginx-proxy_default listed
```

- [ ] `nginx-proxy_default` network exists

### 4. Verify Nginx Proxy Manager

```bash
# Check NPM is running
docker ps | grep nginx-proxy

# Expected: nginx-proxy-app-1 container is running
```

- [ ] Nginx Proxy Manager is running
- [ ] Can access NPM at `http://your-server-ip:81`

## Deployment Steps

### 1. Deploy with Docker Compose

```bash
# Build and start production container
docker-compose up -d

# Check logs
docker-compose logs -f sgnl-api
```

- [ ] Container starts successfully
- [ ] No errors in logs
- [ ] Environment variables loaded correctly

### 2. Verify Container Network

```bash
# Check if container is on nginx-proxy_default network
docker network inspect nginx-proxy_default | grep sgnl-api

# Expected: Container name listed in output
```

- [ ] Container connected to `nginx-proxy_default` network

### 3. Configure Nginx Proxy Manager

1. **Access NPM Web UI**
   - URL: `http://your-server-ip:81`
   - Login with credentials

2. **Add Proxy Host**
   - Go to **Hosts** → **Proxy Hosts** → **Add Proxy Host**
   - Configure:
     ```
     Domain Names: sgnl.metinkorkmaz.quest
     Forward Hostname: sgnl-api
     Forward Port: 8000
     ```
   - **SSL Tab:**
     - Request a new SSL certificate
     - Force SSL: ✅ Enabled
     - HTTP/2 Support: ✅ Enabled
     - Enable HSTS: ✅ Enabled
   - Click **Save**

- [ ] Proxy host created successfully
- [ ] SSL certificate requested
- [ ] Certificate issued (wait 1-5 minutes)

## Post-Deployment Verification

### 1. Health Check

```bash
# Test health endpoint
curl https://sgnl.metinkorkmaz.quest/health

# Expected response:
# {
#   "status": "ok",
#   "version": "2.0.0",
#   "openai_configured": true
# }
```

- [ ] Health endpoint returns 200 OK
- [ ] Response contains `"status": "ok"`
- [ ] `openai_configured` is `true`

### 2. SSL Certificate Verification

```bash
# Check SSL certificate
curl -I https://sgnl.metinkorkmaz.quest

# Expected: 200 OK with SSL/TLS headers
```

- [ ] SSL certificate is valid
- [ ] No browser warnings
- [ ] HTTPS redirects work correctly

### 3. CORS Testing

Open browser console on `https://sgnl.metinkorkmaz.quest`:
- [ ] No CORS errors in console
- [ ] API endpoints accessible from frontend

### 4. n8n Connection Test

```bash
# Test from within the container
docker exec -it sgnl-api bash
curl http://n8n.metinkorkmaz.quest/healthz
exit
```

- [ ] Container can reach n8n
- [ ] No network errors

### 5. API Endpoint Testing

```bash
# Test content extraction
curl -X POST https://sgnl.metinkorkmaz.quest/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Test deep scan
curl -X POST https://sgnl.metinkorkmaz.quest/deep-scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

- [ ] `/extract` endpoint works
- [ ] `/deep-scan` endpoint works
- [ ] n8n webhooks are called successfully

### 6. Rate Limiting Test

```bash
# Make multiple requests (more than 20)
for i in {1..25}; do
  curl https://sgnl.metinkorkmaz.quest/health
done
```

- [ ] After 20 requests, get 429 status code
- [ ] Rate limiting works as expected

### 7. Security Verification

- [ ] No hardcoded IP addresses in error messages
- [ ] Environment variables not exposed in responses
- [ ] CORS restrictions work (test from different origin)
- [ ] No sensitive data in logs

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs sgnl-api

# Common issues:
# - Missing .env file
# - Invalid environment variables
# - Port conflicts
```

### SSL Certificate Not Issuing

1. Check DNS points to correct IP
2. Wait up to 5 minutes
3. Check NPM logs for errors
4. Ensure ports 80 and 443 are not blocked

### n8n Connection Failed

```bash
# Test from container
docker exec -it sgnl-api bash
curl http://n8n.metinkorkmaz.quest/healthz

# Check environment variables
docker exec sgnl-api env | grep N8N
```

### CORS Errors

1. Verify `ALLOWED_ORIGINS` in `.env`
2. Restart container after changing `.env`
3. Check browser console for specific error

## Cleanup

If deployment fails:

```bash
# Stop container
docker-compose down

# Remove container
docker-compose down -v

# Check for orphaned containers
docker ps -a | grep sgnl

# Remove if needed
docker rm sgnl-api
```

## Success Criteria

Deployment is successful when:

- [x] All code changes implemented
- [x] All environment files created
- [x] Docker configurations updated
- [x] Documentation created
- [ ] Container running on nginx-proxy_default network
- [ ] NPM proxy host configured
- [ ] SSL certificate valid
- [ ] Health endpoint responding
- [ ] All API endpoints working
- [ ] n8n webhooks functional
- [ ] CORS restrictions active
- [ ] Rate limiting working
- [ ] No errors in logs

---

## Notes

- Keep `.env` file secure - never commit to git
- Back up `.env` before making changes
- Monitor logs for first 24 hours after deployment
- Document any issues for future reference
