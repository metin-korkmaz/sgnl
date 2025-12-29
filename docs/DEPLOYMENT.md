# SGNL Deployment Guide

This guide covers deploying the SGNL API with Nginx Proxy Manager for SSL termination and domain routing.

## Prerequisites

- Nginx Proxy Manager running and accessible at `http://your-server:81`
- Docker and Docker Compose installed
- Domains pointing to your server:
  - `sgnl.metinkorkmaz.quest` ← Your API
  - `n8n.metinkorkmaz.quest` ← Your n8n (already configured)

## Production Deployment

### Step 1: Prepare Environment File

```bash
# Copy production template
cp .env.prod .env

# Edit with your actual API keys
nano .env
```

**Required variables to configure:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `TAVILY_API_KEY` - Your Tavily API key

**Optional variables:**
- `ALLOWED_ORIGINS` - Default: `https://sgnl.metinkorkmaz.quest`
- `RATE_LIMIT` - Default: 20 requests/minute
- `LOG_LEVEL` - Default: INFO

### Step 2: Deploy with Docker Compose

```bash
# Build and start production container
docker-compose up -d

# Check logs
docker-compose logs -f sgnl-api

# Check container status
docker ps | grep sgnl-api
```

### Step 3: Configure Nginx Proxy Manager

1. **Access NPM Web UI**
   - URL: `http://your-server-ip:81`
   - Login with your NPM credentials

2. **Create Proxy Host for SGNL**
   - Go to **Hosts** → **Proxy Hosts**
   - Click **Add Proxy Host**
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

3. **Wait for SSL Certificate**
   - Let's Encrypt may take 1-5 minutes to issue the certificate
   - Check NPM logs for any errors

### Step 4: Verify Deployment

```bash
# Check container health
docker ps | grep sgnl-api

# Test health endpoint (HTTP)
curl http://sgnl.metinkorkmaz.quest/health

# Test health endpoint (HTTPS)
curl https://sgnl.metinkorkmaz.quest/health

# Expected response:
# {
#   "status": "ok",
#   "version": "2.0.0",
#   "openai_configured": true
# }
```

### Step 5: Test API Endpoints

```bash
# Test content extraction
curl -X POST https://sgnl.metinkorkmaz.quest/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Test deep scan (requires configured n8n)
curl -X POST https://sgnl.metinkorkmaz.quest/deep-scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Development Setup

### Local Development

```bash
# Use development environment
cp .env.dev .env

# Edit with your dev API keys
nano .env

# Start with port mapping (access at http://localhost:8000)
docker-compose -f docker-compose.dev.yml up --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Running Directly with Python

```bash
# Install dependencies
cd app
pip install -r requirements.txt

# Load environment variables
export $(cat ../.env | xargs)

# Run the server
python main.py
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for GPT-4o analysis |
| `TAVILY_API_KEY` | Yes | - | Tavily API key for web search |
| `N8N_WEBHOOK_URL` | Yes | - | n8n webhook URL for deep scan |
| `N8N_FAST_SEARCH_URL` | Yes | - | n8n webhook URL for fast search |
| `ALLOWED_ORIGINS` | No | `https://sgnl.metinkorkmaz.quest` | CORS allowed origins (comma-separated) |
| `RATE_LIMIT` | No | 20 | Max requests per IP per minute |
| `RATE_WINDOW_SECONDS` | No | 60 | Time window for rate limiting |
| `HOST` | No | 0.0.0.0 | API server host |
| `PORT` | No | 8000 | Internal container port |
| `LOG_LEVEL` | No | INFO | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `DENSITY_THRESHOLD` | No | 0.45 | Content density threshold (0.0-1.0) |
| `LLM_MAX_CHARS` | No | 12000 | Max content length to send to LLM |

## Docker Networks

The production setup uses the `nginx-proxy_default` network to communicate with Nginx Proxy Manager:

```bash
# Verify network connection
docker network inspect nginx-proxy_default | grep sgnl-api

# Expected output should show sgnl-api connected
```

## Security

### Production Security Features

- ✅ **No hardcoded credentials** - All secrets in environment variables
- ✅ **Domain-based n8n URLs** - No IP addresses exposed
- ✅ **Restricted CORS** - Only configured domains allowed
- ✅ **SSL/TLS encryption** - Automatic Let's Encrypt certificates
- ✅ **Rate limiting** - Prevents abuse (20 req/min default)
- ✅ **Network isolation** - Container on isolated Docker network

### n8n Communication

The API communicates with n8n via internal Docker networking:

```
sgnl-api → nginx-proxy_default → n8n.metinkorkmaz.quest → n8n container
```

No IP addresses are hardcoded - all communication uses domain names.

## Troubleshooting

### Container Not Connecting to NPM

**Problem:** Container can't connect to nginx-proxy_default network

```bash
# Check network connection
docker network inspect nginx-proxy_default | grep sgnl-api

# If not connected, recreate container
docker-compose down
docker-compose up -d

# Verify connection
docker network inspect nginx-proxy_default | grep sgnl-api
```

### SSL Certificate Issues

**Problem:** SSL certificate not issued or renewal fails

**Solutions:**

1. **Check DNS configuration**
   ```bash
   # Verify domain points to your server
   dig sgnl.metinkorkmaz.quest
   ```

2. **Check ports are not blocked**
   ```bash
   # Ensure ports 80 and 443 are accessible
   sudo ufw status
   # If needed, allow ports
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. **Wait for Let's Encrypt**
   - Certificate issuance may take 1-5 minutes
   - Check NPM logs for errors

4. **Force certificate renewal**
   - In NPM UI, go to Proxy Host → SSL → Renew

### n8n Connection Issues

**Problem:** API can't connect to n8n

**Debug steps:**

1. **Test n8n from container**
   ```bash
   # Enter container
   docker exec -it sgnl-api bash

   # Test n8n connection
   curl http://n8n.metinkorkmaz.quest/healthz

   # Exit container
   exit
   ```

2. **Check n8n is running**
   ```bash
   docker ps | grep n8n
   ```

3. **Check environment variables**
   ```bash
   docker exec sgnl-api env | grep N8N
   ```

4. **Check logs for errors**
   ```bash
   docker-compose logs sgnl-api | grep -i n8n
   ```

### CORS Errors

**Problem:** Browser shows CORS errors

**Solutions:**

1. **Check ALLOWED_ORIGINS environment variable**
   ```bash
   docker exec sgnl-api env | grep ALLOWED_ORIGINS
   ```

2. **Verify your domain is in the list**
   ```bash
   # Expected: https://sgnl.metinkorkmaz.quest
   ```

3. **Restart container after changing .env**
   ```bash
   docker-compose up -d
   ```

### Health Check Failures

**Problem:** `/health` endpoint returns errors

**Debug:**

```bash
# Check logs
docker-compose logs sgnl-api

# Test OpenAI configuration
curl https://sgnl.metinkorkmaz.quest/health

# Expected response with openai_configured: true or false
```

### Rate Limiting Too Strict

**Problem:** Legitimate requests being rate-limited

**Solutions:**

1. **Increase rate limit in .env**
   ```bash
   RATE_LIMIT=50
   ```

2. **Restart container**
   ```bash
   docker-compose up -d
   ```

## Updating the Application

### Pull Latest Changes

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# View logs
docker-compose logs -f
```

### Rolling Updates (Zero Downtime)

```bash
# Pull latest code
git pull origin main

# Build new image
docker-compose build

# Start new container
docker-compose up -d

# Stop old container (automatic)
docker-compose down
```

## Monitoring

### View Logs

```bash
# All logs
docker-compose logs sgnl-api

# Follow logs (tail)
docker-compose logs -f sgnl-api

# Last 100 lines
docker-compose logs --tail=100 sgnl-api

# Filter for errors
docker-compose logs sgnl-api | grep -i error
```

### Container Metrics

```bash
# Container status
docker ps | grep sgnl-api

# Container stats (CPU, memory, etc.)
docker stats sgnl-api

# Container details
docker inspect sgnl-api
```

## Backup and Restore

### Backup Environment Configuration

```bash
# Backup .env file
cp .env .env.backup.$(date +%Y%m%d)

# List backups
ls -la .env.backup.*
```

### Restore from Backup

```bash
# Restore from specific backup
cp .env.backup.20251226 .env

# Restart container
docker-compose up -d
```

## Development vs Production

### Development Configuration

- **Network:** `sgnl-net` (isolated bridge network)
- **Ports:** Exposed on `8000` for local access
- **CORS:** Allows `http://localhost:3000` and `http://127.0.0.1:3000`
- **Rate Limiting:** 100 requests/minute (more lenient)
- **Logging:** DEBUG level (verbose)

### Production Configuration

- **Network:** `nginx-proxy_default` (shared with NPM)
- **Ports:** Internal only (8000), exposed via NPM
- **CORS:** Restricted to `https://sgnl.metinkorkmaz.quest`
- **Rate Limiting:** 20 requests/minute (strict)
- **Logging:** INFO level (minimal)

## Performance Tuning

### Adjust Rate Limiting

For high-traffic deployments, adjust in `.env`:

```bash
RATE_LIMIT=50
RATE_WINDOW_SECONDS=60
```

### Adjust LLM Settings

For faster responses (less accuracy):

```bash
LLM_MAX_CHARS=8000
DENSITY_THRESHOLD=0.50
```

For more accurate analysis (slower):

```bash
LLM_MAX_CHARS=16000
DENSITY_THRESHOLD=0.40
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs sgnl-api`
2. Check NPM logs in the web UI
3. Review this troubleshooting section
4. Verify environment variables are correctly set
