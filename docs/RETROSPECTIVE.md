# SGNL Project Sprint Retrospective — April 2026

**Date:** 2026-04-22
**Project:** SGNL Signal Extraction Engine
**Deployment:** https://sgnl.metinkorkmaz.quest
**Repository:** https://github.com/metin-korkmaz/sgnl

---

## Sprint Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **Goal** | ✅ Achieved | Deploy functional signal extraction engine |
| **Commits** | 38 | Solo development over ~3 months |
| **Features** | 13 feat commits | Core functionality complete |
| **Tests** | 4 test commits | TDD approach for rate limiter |
| **Deployment** | ✅ Operational | Health check passing, OpenAI configured |

### Commit Distribution by Type

| Type | Count | Description |
|------|-------|-------------|
| `feat` | 13 | New features (rate limiter, caching, security, UI) |
| `fix` | 7 | Bug fixes (XSS, mobile layout, Starlette API) |
| `test` | 4 | Test additions (TDD rate limiter) |
| `docs` | 8 | Documentation improvements |
| `perf` | 1 | Performance optimizations |
| `refactor` | 1 | Code refactoring |
| `infra` | 1 | Infrastructure (Redis Docker) |
| `chore` | 1 | Maintenance tasks |

### Timeline Activity

| Date | Commits | Phase |
|------|---------|-------|
| Dec 29, 2025 | 10 | Initial development burst |
| Jan 1-3, 2026 | 12 | Security & performance polish |
| Mar 4, 2026 | 4 | Security headers, UI fixes |
| Mar 9, 2026 | 2 | CI/CD, caching layer |
| Mar 25, 2026 | 10 | Redis rate limiter (TDD) |

---

## 4Ls Retrospective

### 🟢 LIKED — What Went Well

#### 1. TDD Discipline for Rate Limiter
```
Mar 25, 2026 → 10 commits in one day
Pattern: test → fail → implement → pass → refactor
```
- **Evidence:** Commits `014b6e2` → `914f0ea` → `8718559` → `8bcfd06`
- **Outcome:** RedisRateLimiter with sliding window algorithm, fail-open fallback
- **Why it worked:** Tests drove the design; storage abstraction emerged naturally

#### 2. Security-First Mindset
- **SSRF Validator:** 43 tests passed, comprehensive protection
  - Private IP blocking (IPv4/IPv6 CIDR ranges)
  - DNS rebinding prevention
  - Metadata endpoint protection (AWS, GCP, Alibaba)
  - Dangerous scheme blocking (file://, ftp://, gopher://)
- **SecurityHeadersMiddleware:** CSP, XSS protection, clickjacking prevention
- **Rate Limiting:** Extended to all expensive endpoints
- **Docker:** Runs as non-root user (appuser)

#### 3. Accessibility Verification Passed
- **WCAG 2.1 AA compliant**
- Keyboard navigation (Tab, Cmd+K, Escape)
- Touch targets 48px+ minimum
- Color contrast 4.5:1+ ratios
- Semantic HTML structure

#### 4. Clean Commit Hygiene
- Conventional commits format (feat, fix, test, refactor, perf)
- Descriptive commit messages with scope prefixes
- Atomic commits (one feature per commit)

#### 5. CI/CD Pipeline Quality
- Matrix testing (Python 3.11, 3.12)
- Ruff linting + formatting check
- MyPy type checking
- pytest with coverage
- Codecov integration
- Docker build verification

---

### 🟡 LEARNED — New Knowledge Gained

#### 1. Redis Async Integration is Tricky
```
Issue: RuntimeWarning: coroutine 'RedisCache.ping' was never awaited
Root cause: Event loop already running when RedisCache.ping() called
Status: Fallback to InMemoryRateLimiter working
```
- **Lesson:** Async initialization in FastAPI startup events requires careful handling
- **Current workaround:** Hybrid cache (memory fallback when Redis unavailable)
- **Production impact:** Redis shows `available: false` but rate limiting still works

#### 2. Starlette 1.0.0 API Changes
```
Commit: 5a36e14 — fix: update TemplateResponse for Starlette 1.0.0 API
```
- **Lesson:** Dependency upgrades require API compatibility checks
- **Pattern:** FastAPI/Starlette breaking changes surface in TemplateResponse

#### 3. Swiss Brutalism Design System
- **Philosophy:** Zero tolerance for friction, no smooth scrolling, no "delight"
- **Colors:** Ink Black (#000000), Off White (#F4F1EA), Safety Orange (#FF4500), Signal Green (#00FF00)
- **Typography:** Industrial Sans headers, Monospace data
- **Lesson:** Minimalist design reduces maintenance and improves performance

#### 4. SSRF is Deceptively Complex
- **Discovery:** DNS rebinding attacks require IP resolution BEFORE validation
- **Pattern:** `ipaddress` module + CIDR matching is robust
- **Lesson:** Security validators must block metadata endpoints (169.254.169.254)

---

### 🔴 LACKED — What Was Missing

#### 1. Redis Production Integration
| Issue | Impact | Severity |
|-------|--------|----------|
| Redis async bug | Memory fallback only | Medium |
| No Redis in production | Can't share rate limit state across instances | High (for scaling) |
| Health check shows `redis_available: false` | Monitoring blind spot | Medium |

**Root cause:** Async event loop conflict in `app/cache/__init__.py`

#### 2. No Linting Tool Configured
- **AGENTS.md note:** "No linter configured (no .flake8, pylint, ruff found)"
- **CI uses Ruff** but project lacks `.ruff.toml` or `pyproject.toml` config
- **Impact:** Inconsistent linting between CI and local dev

#### 3. Temporary Files Left Behind
```
main-searchfix.css — 2490 lines (patch file)
=5.0.0 — Unknown artifact
20, 50, 100 — Unknown marker files
```
- **Lesson:** Cleanup commit should follow patch merges
- **Recommendation:** Remove after verification period

#### 4. No Pre-commit Hooks Enforced
- `.pre-commit-config.yaml` exists but hooks not run locally
- **Impact:** Developers can commit without linting/type checking
- **Lesson:** CI catches issues but local feedback is faster

---

### 🔵 LONGED FOR — What We Wish We Had

#### 1. Proper Redis Integration Working
```
Goal: Redis available: true in health check
Need: Fix async initialization bug
Benefit: Distributed rate limiting, cache persistence across restarts
```

#### 2. Team Collaboration
- **Current state:** Solo development (38 commits, single contributor)
- **Wish:** Code review, pair programming, knowledge sharing
- **Gap areas:** Security review, performance profiling, UX testing

#### 3. Monitoring & Observability
- No error tracking (no Sentry integration)
- No performance monitoring (no APM)
- No uptime alerts
- Analytics middleware exists but not fully utilized

#### 4. Automated Security Scanning
- **Current:** Manual SSRF validator tests
- **Wish:** Automated dependency scanning (Dependabot)
- **Wish:** Container vulnerability scanning
- **Wish:** CSP violation reporting endpoint

---

## Action Items

| Priority | Action Item | Owner | Deadline | Success Metric |
|----------|-------------|-------|----------|----------------|
| **1** | Fix Redis async initialization bug | Metin | 2026-04-30 | `redis_available: true` in health check |
| **2** | Configure Ruff in pyproject.toml | Metin | 2026-04-25 | `ruff check app/` passes locally |
| **3** | Clean up temporary files | Metin | 2026-04-25 | No stray files in repo root |

### Action Details

#### Action 1: Redis Async Bug Fix
- **File:** `app/cache/__init__.py`
- **Issue:** Event loop conflict during startup
- **Approach:** Move Redis initialization to proper async context
- **Verification:** Health endpoint shows Redis available

#### Action 2: Ruff Configuration
- **Add to `pyproject.toml`:**
```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
```
- **Benefit:** Consistent linting in CI and local dev

#### Action 3: File Cleanup
- Remove: `main-searchfix.css`, `=5.0.0`, `20`, `50`, `100`
- Verify: No visual regressions after CSS cleanup

---

## Carry-over from Previous Work

| Previous Action | Status | Notes |
|-----------------|--------|-------|
| SSRF Validator Integration | ✅ Done | Integrated into extractor.py |
| AsyncOpenAI Migration | ✅ Done | All LLM calls now async |
| Security Headers | ✅ Done | CSP, XSS, clickjacking protection |
| Accessibility Verification | ✅ Done | WCAG AA compliant |
| CI/CD Pipeline | ✅ Done | GitHub Actions with matrix |
| Redis Rate Limiter | ⚠️ Partial | Implemented but not working in prod |

---

## Summary

### Strengths
- **TDD approach** produced robust rate limiter implementation
- **Security-first mindset** delivered comprehensive SSRF protection
- **Clean commit hygiene** maintains readable git history
- **Accessibility compliance** achieved WCAG AA standards

### Improvement Areas
- **Redis integration** needs async bug fix for production reliability
- **Linting configuration** should be explicit in project config
- **File cleanup** removes technical debt from temporary patches

### Velocity Assessment
- **Efficient:** 38 commits in 3 months → core functionality complete
- **Quality:** Test commits, security focus, accessibility verification
- **Deployable:** Production health check passing, API functional

---

## Recommendations for Next Sprint

1. **Redis async fix** — Priority 1, enables distributed deployment
2. **Add observability** — Sentry for error tracking, Prometheus for metrics
3. **Security automation** — Dependabot, container scanning
4. **Performance profiling** — Identify bottleneck endpoints

---

**Retrospective facilitated by:** Sisyphus AI Agent
**Format:** 4Ls (Liked / Learned / Lacked / Longed For)
**Tone:** Constructive — focus on improvement, not blame