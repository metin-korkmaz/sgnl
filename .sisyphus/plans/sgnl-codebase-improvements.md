# SGNL Codebase Improvement Work Plan

## TL;DR

> **Objective**: Fix critical security vulnerabilities, improve code quality, and enhance developer experience across 37 identified issues.
>
> **Deliverables**: 
> - Security hardening (CSP, XSS prevention, rate limiting)
> - Code quality improvements (refactoring, type safety)
> - Developer tooling setup (linting, formatting, CI/CD)
> - Accessibility and SEO enhancements
>
> **Estimated Effort**: ~50 hours across all phases
> **Parallel Execution**: YES - 4 waves with 5-8 tasks each
> **Critical Path**: Security fixes → Code organization → Tooling setup → Final verification

---

## Context

This work plan addresses findings from the comprehensive codebase audit. The SGNL application is a production-ready FastAPI service for content signal extraction with a brutalist frontend. While the architecture is solid, there are security vulnerabilities, code organization issues, and missing developer tooling that need attention.

### Key Findings from Audit

1. **1 Critical Security Issue**: XSS vulnerability in JavaScript
2. **12 High Priority Issues**: Security headers, code organization, rate limiting
3. **17 Medium Priority Issues**: Type safety, maintainability, accessibility
4. **7 Low Priority Issues**: SEO, performance optimizations

---

## Work Objectives

### Core Objective
Transform SGNL from a B+ grade codebase to an A-grade production system by addressing all critical and high-priority issues while establishing proper developer tooling and workflows.

### Concrete Deliverables

#### Phase 1: Security Hardening (CRITICAL)
- [ ] Fix XSS vulnerability in main.js
- [ ] Implement security headers middleware
- [ ] Extend rate limiting to all protected endpoints
- [ ] Fix CSS file reference bug

#### Phase 2: Code Organization (HIGH)
- [ ] Refactor main.py into modular structure
- [ ] Extract middleware to separate files
- [ ] Move hardcoded values to configuration
- [ ] Fix type safety issues

#### Phase 3: Developer Tooling (HIGH)
- [ ] Set up Ruff (Python linter/formatter)
- [ ] Configure mypy for type checking
- [ ] Add pre-commit hooks
- [ ] Create GitHub Actions CI/CD

#### Phase 4: Quality & Polish (MEDIUM)
- [ ] Add accessibility improvements
- [ ] Create SEO files (robots.txt, sitemap.xml)
- [ ] Add test coverage reporting
- [ ] Docker security hardening

### Definition of Done
- All security vulnerabilities patched and verified
- Code passes linting and type checking
- All tests pass with coverage reporting
- CI/CD pipeline runs successfully
- Accessibility audit passes

### Must Have
- XSS vulnerability fixed
- Security headers implemented
- Rate limiting comprehensive
- Developer tooling configured
- CI/CD pipeline operational

### Must NOT Have (Guardrails from Metis review)
- No breaking API changes
- No removal of existing functionality
- No degradation in performance
- No new untested code
- No changes without corresponding tests

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest with async support)
- **Automated tests**: YES (TDD for fixes, tests-after for refactoring)
- **Framework**: pytest + pytest-asyncio

### QA Policy
Every task includes agent-executed QA scenarios:
- **Security**: Use curl to verify headers, test XSS payloads
- **Code Quality**: Run linting/type checking commands
- **API**: Test endpoints with curl/httpx
- **Frontend**: Use Playwright for browser verification

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — Security & Critical Fixes):
├── Task 1: Fix XSS vulnerability in main.js [quick]
├── Task 2: Fix CSS file reference in index.html [quick]
├── Task 3: Create SecurityHeadersMiddleware [quick]
├── Task 4: Extend rate limiting to all endpoints [quick]
├── Task 5: Add robots.txt and sitemap.xml [quick]
└── Task 6: Add skip navigation link for a11y [quick]

Wave 2 (After Wave 1 — Code Organization, MAX PARALLEL):
├── Task 7: Extract RateLimitMiddleware to separate file [unspecified-high]
├── Task 8: Refactor main.py routes into routes/ directory [unspecified-high]
├── Task 9: Move hardcoded config to config.py and env vars [quick]
├── Task 10: Fix type safety issues in analytics models [quick]
├── Task 11: Add proper type hints to main functions [quick]
└── Task 12: Create config/ directory with structured settings [deep]

Wave 3 (After Wave 2 — Developer Tooling):
├── Task 13: Set up Ruff configuration [quick]
├── Task 14: Configure mypy for type checking [quick]
├── Task 15: Add pre-commit hooks [quick]
├── Task 16: Create GitHub Actions CI/CD workflow [unspecified-high]
├── Task 17: Add test coverage reporting [quick]
└── Task 18: Create .editorconfig [quick]

Wave 4 (After Wave 3 — Polish & Verification):
├── Task 19: Add comprehensive input labels and ARIA attributes [visual-engineering]
├── Task 20: Implement JSON-LD structured data [quick]
├── Task 21: Add OG image alt text [quick]
├── Task 22: Docker security hardening (non-root user) [unspecified-high]
└── Task 23: Create comprehensive test for security headers [deep]

Wave FINAL (After ALL tasks — independent review, 4 parallel):
├── Task F1: Security audit verification (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Full test suite execution (unspecified-high)
└── Task F4: Accessibility audit (deep)

Critical Path: Task 1 → Task 2 → Task 3 → Task 4 → Task 7 → Task 13 → Task 19 → F1-F4
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 6 (Waves 1 & 2)
```

### Dependency Matrix

- **1-6**: — → 7-12, 1
- **7**: — → 13-18, 2
- **8**: 7 → 13-18, 2
- **13-18**: 7-12 → 19-23, 3
- **19-23**: 13-18 → F1-F4, 4

### Agent Dispatch Summary

- **Wave 1**: **6** tasks → All `quick`
- **Wave 2**: **6** tasks → T7-T8 `unspecified-high`, T9-T11 `quick`, T12 `deep`
- **Wave 3**: **6** tasks → T13-T15,T17-T18 `quick`, T16 `unspecified-high`
- **Wave 4**: **5** tasks → T19 `visual-engineering`, T20-T21,T23 `quick`, T22 `unspecified-high`
- **Final**: **4** tasks → F1 `oracle`, F2-F3 `unspecified-high`, F4 `deep`

---

## TODOs

### Wave 1: Security & Critical Fixes

- [ ] **1. Fix XSS Vulnerability in main.js**

  **What to do**:
  - Replace `innerHTML` usage with `textContent` where user-provided URLs are displayed
  - Sanitize URL inputs before DOM insertion
  - Add URL validation in `extractDomain()` function
  
  **Must NOT do**:
  - Do not use DOMPurify (adds dependency) unless necessary
  - Do not change API contracts
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `frontend-ui-ux` (for JavaScript DOM manipulation)
  
  **References**:
  - `app/static/js/main.js:400-500` - DOM insertion points
  - OWASP XSS Prevention Cheat Sheet
  
  **Acceptance Criteria**:
  - [ ] No `innerHTML` usage with user content
  - [ ] All URL display uses `textContent`
  - [ ] `extractDomain()` validates URL format
  
  **QA Scenarios**:
  ```
  Scenario: Malicious URL in search results
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:8000
      2. Enter search term "javascript:alert('xss')"
      3. Submit search
      4. Inspect results for script execution
    Expected: Script does NOT execute, URL displayed as text
    Evidence: .sisyphus/evidence/task-1-xss-test.png
  
  Scenario: HTML injection in URL
    Tool: Playwright
    Steps:
      1. Search with "<img src=x onerror=alert(1)>"
      2. Check results display
    Expected: HTML tags displayed as literal text, not parsed
    Evidence: .sisyphus/evidence/task-1-html-injection.png
  ```
  
  **Commit**: YES
  - Message: `fix(security): prevent XSS via URL sanitization`
  - Files: `app/static/js/main.js`

- [ ] **2. Fix CSS File Reference Bug**

  **What to do**:
  - Change `main-searchfix.css?v=6.6` to `main.css` in index.html
  - Verify cache busting still works (use file hash or keep query param)
  
  **Must NOT do**:
  - Do not delete main-searchfix.css if it exists and is different
  
  **References**:
  - `app/templates/index.html:41`
  - `app/static/css/main.css` (2518 lines)
  
  **Acceptance Criteria**:
  - [ ] HTML references correct CSS file
  - [ ] Page renders with proper styling
  
  **QA Scenarios**:
  ```
  Scenario: CSS loads correctly
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:8000
      2. Check Network tab for CSS request
      3. Verify 200 status and correct content-type
    Expected: CSS loads, styles applied (check brutalist design visible)
    Evidence: .sisyphus/evidence/task-2-css-load.png
  ```
  
  **Commit**: YES
  - Message: `fix(ui): correct CSS file reference in template`
  - Files: `app/templates/index.html`

- [ ] **3. Implement SecurityHeadersMiddleware**

  **What to do**:
  - Create middleware to add security headers:
    - `Content-Security-Policy`
    - `X-Frame-Options: DENY`
    - `X-Content-Type-Options: nosniff`
    - `Strict-Transport-Security` (HSTS)
    - `Referrer-Policy: strict-origin-when-cross-origin`
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  
  **References**:
  - OWASP Secure Headers Project
  - FastAPI middleware documentation
  - `app/main.py:166-191` - existing middleware
  
  **Acceptance Criteria**:
  - [ ] Middleware created in `app/middleware/security.py`
  - [ ] All 5 security headers present in responses
  - [ ] Middleware registered in main.py
  
  **QA Scenarios**:
  ```
  Scenario: Security headers present
    Tool: Bash (curl)
    Steps:
      1. Run: curl -I http://localhost:8000/
      2. Check for all security headers
    Expected: All 5 headers present with correct values
    Evidence: .sisyphus/evidence/task-3-headers.txt
  
  Scenario: CSP prevents inline scripts
    Tool: Bash (curl)
    Steps:
      1. Check Content-Security-Policy header
    Expected: CSP restricts script sources appropriately
    Evidence: .sisyphus/evidence/task-3-csp.txt
  ```
  
  **Commit**: YES
  - Message: `feat(security): add comprehensive security headers middleware`
  - Files: `app/middleware/security.py`, `app/main.py`

- [ ] **4. Extend Rate Limiting to All Protected Endpoints**

  **What to do**:
  - Add `/analyze-results`, `/check-density`, `/extract` to `PROTECTED_PATHS`
  - Consider different rate limits for different endpoints (stricter for expensive operations)
  
  **References**:
  - `app/main.py:78-158` - RateLimitMiddleware
  - `app/main.py:81` - PROTECTED_PATHS
  
  **Acceptance Criteria**:
  - [ ] All write/expensive endpoints protected
  - [ ] Rate limits configurable per endpoint
  
  **QA Scenarios**:
  ```
  Scenario: Rate limit on analyze-results
    Tool: Bash (curl)
    Steps:
      1. Run: for i in {1..5}; do curl -X POST http://localhost:8000/analyze-results -H "Content-Type: application/json" -d '{"results":[],"query":"test"}'; done
    Expected: After 3 requests, receive 429 status
    Evidence: .sisyphus/evidence/task-4-rate-limit.txt
  ```
  
  **Commit**: YES
  - Message: `feat(security): extend rate limiting to all API endpoints`
  - Files: `app/main.py`

- [ ] **5. Add robots.txt and sitemap.xml**

  **What to do**:
  - Create `app/static/robots.txt` with appropriate crawl rules
  - Create `app/static/sitemap.xml` with main endpoints
  - Add routes in main.py to serve these files
  
  **Acceptance Criteria**:
  - [ ] robots.txt accessible at `/robots.txt`
  - [ ] sitemap.xml accessible at `/sitemap.xml`
  
  **QA Scenarios**:
  ```
  Scenario: SEO files accessible
    Tool: Bash (curl)
    Steps:
      1. curl http://localhost:8000/robots.txt
      2. curl http://localhost:8000/sitemap.xml
    Expected: Both return 200 with correct content-type
    Evidence: .sisyphus/evidence/task-5-seo-files.txt
  ```
  
  **Commit**: YES
  - Message: `feat(seo): add robots.txt and sitemap.xml`
  - Files: `app/static/robots.txt`, `app/static/sitemap.xml`, `app/main.py`

- [ ] **6. Add Skip Navigation Link for Accessibility**

  **What to do**:
  - Add hidden "Skip to main content" link at top of body
  - Add `id="main-content"` to main element
  - Style to be visible on focus
  
  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: []
  
  **Acceptance Criteria**:
  - [ ] Skip link present and functional
  - [ ] Visible when focused via keyboard
  
  **QA Scenarios**:
  ```
  Scenario: Skip link works
    Tool: Playwright
    Steps:
      1. Navigate to page
      2. Press Tab key
      3. Check skip link appears
      4. Press Enter
      5. Check focus moves to main content
    Expected: Keyboard navigation enhanced
    Evidence: .sisyphus/evidence/task-6-skip-link.png
  ```
  
  **Commit**: YES
  - Message: `feat(a11y): add skip navigation link`
  - Files: `app/templates/index.html`, `app/static/css/main.css`

### Wave 2: Code Organization

- [ ] **7. Extract RateLimitMiddleware to Separate File**

  **What to do**:
  - Move `RateLimitMiddleware` class to `app/middleware/rate_limit.py`
  - Update imports in main.py
  - Keep functionality identical
  
  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  
  **Acceptance Criteria**:
  - [ ] Middleware in separate file
  - [ ] All tests pass
  - [ ] No functionality change
  
  **QA Scenarios**:
  ```
  Scenario: Rate limiting still works
    Tool: Bash (curl)
    Steps:
      1. Rapid requests to /fast-search
    Expected: 429 returned after limit
    Evidence: .sisyphus/evidence/task-7-rate-limit.txt
  ```
  
  **Commit**: YES
  - Message: `refactor(middleware): extract RateLimitMiddleware to separate module`
  - Files: `app/middleware/rate_limit.py`, `app/main.py`

- [ ] **8. Refactor main.py Routes into Routes Directory**

  **What to do**:
  - Create `app/routes/` directory
  - Extract route handlers into modules:
    - `routes/health.py` - Health check
    - `routes/extract.py` - Content extraction
    - `routes/scan.py` - Scan endpoints (deep-scan, scan-topic, fast-search)
    - `routes/analyze.py` - Analyze results, check-density
  - Update main.py to use `app.include_router()`
  
  **Must NOT do**:
  - Do not change API contracts or response formats
  
  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  
  **Acceptance Criteria**:
  - [ ] Routes organized in modules
  - [ ] main.py < 300 lines
  - [ ] All endpoints still functional
  
  **QA Scenarios**:
  ```
  Scenario: All endpoints work after refactor
    Tool: Bash (curl)
    Steps:
      1. Test /health
      2. Test /extract with sample URL
      3. Test /fast-search (mock)
      4. Test /deep-scan (mock)
    Expected: All return expected responses
    Evidence: .sisyphus/evidence/task-8-endpoints.txt
  ```
  
  **Commit**: YES (grouped with Task 7)
  - Message: `refactor(routes): modularize route handlers`
  - Files: `app/routes/*.py`, `app/main.py`

- [ ] **9. Move Hardcoded Config to config.py and Env Vars**

  **What to do**:
  - Create `app/config.py` with Pydantic Settings
  - Move hardcoded values:
    - `CLEANUP_INTERVAL = 300`
    - `HIGH_TRUST_DOMAINS` dict
    - `SPAM_PATTERNS` list
    - System prompt text
  - Update .env.example with new variables
  
  **References**:
  - `app/main.py:82` - CLEANUP_INTERVAL
  - `app/extractor.py:222-258` - Domains and patterns
  - `app/main.py:210-217` - System prompt
  
  **Acceptance Criteria**:
  - [ ] Config centralized in config.py
  - [ ] All previously hardcoded values configurable
  - [ ] .env.example updated
  
  **QA Scenarios**:
  ```
  Scenario: Config loads from environment
    Tool: Bash
    Steps:
      1. Set custom env vars
      2. Start application
      3. Verify config values loaded
    Expected: Custom values take effect
    Evidence: .sisyphus/evidence/task-9-config.txt
  ```
  
  **Commit**: YES
  - Message: `refactor(config): extract hardcoded values to configuration`
  - Files: `app/config.py`, `app/main.py`, `app/extractor.py`, `app/services/analyzer.py`, `.env.example`

- [ ] **10. Fix Type Safety Issues in Analytics Models**

  **What to do**:
  - Fix SQLAlchemy model type annotations (see LSP errors)
  - Use proper SQLAlchemy 2.0 Mapped types
  - Fix `Column[str]` comparison issues
  
  **LSP Errors to Fix**:
  - analytics_middleware.py:90,93 - Cannot assign to Column attributes
  - analytics_routes.py:59,148 - Same issues
  
  **Acceptance Criteria**:
  - [ ] No LSP errors in analytics files
  - [ ] All type annotations correct
  
  **QA Scenarios**:
  ```
  Scenario: Analytics endpoints work
    Tool: Bash (curl)
    Steps:
      1. Visit homepage (creates session)
      2. Check analytics endpoints
    Expected: No errors, proper data
    Evidence: .sisyphus/evidence/task-10-analytics.txt
  ```
  
  **Commit**: YES
  - Message: `fix(types): correct SQLAlchemy model type annotations`
  - Files: `app/analytics_models.py`, `app/analytics_middleware.py`, `app/analytics_routes.py`

- [ ] **11. Add Proper Type Hints to Main Functions**

  **What to do**:
  - Add return types to functions missing them:
    - `get_openai_client()` → `Optional[OpenAI]`
    - `calculate_density()` → `float`
    - `calculate_combined_density()` → `float`
  - Fix other type issues from LSP
  
  **Acceptance Criteria**:
  - [ ] All public functions have type hints
  - [ ] No LSP type errors
  
  **QA Scenarios**:
  ```
  Scenario: Type checking passes
    Tool: Bash (mypy)
    Steps:
      1. Run: mypy app/
    Expected: No errors
    Evidence: .sisyphus/evidence/task-11-mypy.txt
  ```
  
  **Commit**: YES
  - Message: `refactor(types): add comprehensive type hints`
  - Files: `app/main.py`, `app/extractor.py`, `app/models.py`

- [ ] **12. Create Config Directory with Structured Settings**

  **What to do**:
  - Create `app/config/` directory
  - Organize settings by domain:
    - `config/database.py` - DB settings
    - `config/security.py` - Security settings
    - `config/api.py` - API settings
    - `config/__init__.py` - Unified config export
  - Use Pydantic Settings with env var support
  
  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  
  **Acceptance Criteria**:
  - [ ] Structured config module
  - [ ] Validation via Pydantic
  - [ ] Backward compatible
  
  **Commit**: YES (grouped with Task 9)
  - Message: `feat(config): create structured configuration system`
  - Files: `app/config/*.py`

### Wave 3: Developer Tooling

- [ ] **13. Set Up Ruff Configuration**

  **What to do**:
  - Install ruff: `pip install ruff`
  - Create `pyproject.toml` with ruff config:
    - Line length: 100
    - Enable all rules, ignore specific if needed
    - Python version: 3.11
  - Run initial format and lint
  - Fix any auto-fixable issues
  
  **Acceptance Criteria**:
  - [ ] `pyproject.toml` with ruff config
  - [ ] All code formatted with ruff
  - [ ] No linting errors (or explicitly ignored with reason)
  
  **QA Scenarios**:
  ```
  Scenario: Ruff passes
    Tool: Bash
    Steps:
      1. Run: ruff check app/
      2. Run: ruff format --check app/
    Expected: No errors
    Evidence: .sisyphus/evidence/task-13-ruff.txt
  ```
  
  **Commit**: YES
  - Message: `chore(tooling): add and apply ruff configuration`
  - Files: `pyproject.toml`, `requirements.txt`, all Python files

- [ ] **14. Configure mypy for Type Checking**

  **What to do**:
  - Install mypy: `pip install mypy`
  - Add mypy config to `pyproject.toml`:
    - Python version: 3.11
    - Strict mode with reasonable exceptions
    - Ignore missing imports for third-party libs if needed
  - Run mypy and fix issues
  
  **Acceptance Criteria**:
  - [ ] mypy configuration in pyproject.toml
  - [ ] All type errors resolved
  - [ ] CI will catch type errors
  
  **QA Scenarios**:
  ```
  Scenario: mypy passes
    Tool: Bash
    Steps:
      1. Run: mypy app/
    Expected: Success: no issues found
    Evidence: .sisyphus/evidence/task-14-mypy.txt
  ```
  
  **Commit**: YES
  - Message: `chore(tooling): configure mypy type checking`
  - Files: `pyproject.toml`, `requirements.txt`

- [ ] **15. Add Pre-commit Hooks**

  **What to do**:
  - Install pre-commit: `pip install pre-commit`
  - Create `.pre-commit-config.yaml`:
    - ruff (lint + format)
    - mypy
    - Check for large files
    - Check YAML/JSON syntax
    - Check for merge conflicts
  - Install hooks: `pre-commit install`
  - Run on all files
  
  **Acceptance Criteria**:
  - [ ] `.pre-commit-config.yaml` created
  - [ ] Hooks installed
  - [ ] All files pass pre-commit
  
  **QA Scenarios**:
  ```
  Scenario: Pre-commit works
    Tool: Bash
    Steps:
      1. Make a test change
      2. Stage: git add .
      3. Commit: git commit -m "test"
    Expected: Hooks run, pass or block appropriately
    Evidence: .sisyphus/evidence/task-15-precommit.txt
  ```
  
  **Commit**: YES
  - Message: `chore(tooling): add pre-commit hooks`
  - Files: `.pre-commit-config.yaml`, `requirements.txt`

- [ ] **16. Create GitHub Actions CI/CD Workflow**

  **What to do**:
  - Create `.github/workflows/ci.yml`:
    - Run on Python 3.11
    - Install dependencies
    - Run ruff (lint + format check)
    - Run mypy
    - Run pytest with coverage
    - Build Docker image (optional)
  
  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  
  **Acceptance Criteria**:
  - [ ] CI workflow runs on PR and push
  - [ ] All checks must pass
  - [ ] Coverage report generated
  
  **QA Scenarios**:
  ```
  Scenario: CI pipeline works
    Tool: GitHub web interface
    Steps:
      1. Push to branch
      2. Create PR
      3. Check Actions tab
    Expected: All checks green
    Evidence: Screenshot of passing checks
  ```
  
  **Commit**: YES
  - Message: `ci(github): add CI/CD workflow with lint, type-check, and test`
  - Files: `.github/workflows/ci.yml`

- [ ] **17. Add Test Coverage Reporting**

  **What to do**:
  - Install pytest-cov: `pip install pytest-cov`
  - Configure coverage in `pyproject.toml`:
    - Minimum coverage threshold: 80%
    - Exclude test files
    - Generate HTML and XML reports
  - Run tests with coverage
  
  **Acceptance Criteria**:
  - [ ] Coverage configuration in pyproject.toml
  - [ ] HTML report generated in htmlcov/
  - [ ] CI uploads coverage reports
  
  **QA Scenarios**:
  ```
  Scenario: Coverage report generated
    Tool: Bash
    Steps:
      1. Run: pytest --cov=app --cov-report=html
      2. Check htmlcov/index.html
    Expected: Coverage report shows >80%
    Evidence: .sisyphus/evidence/task-17-coverage.html
  ```
  
  **Commit**: YES
  - Message: `chore(tooling): add test coverage reporting`
  - Files: `pyproject.toml`, `requirements.txt`

- [ ] **18. Create .editorconfig**

  **What to do**:
  - Create `.editorconfig` with:
    - UTF-8 encoding
    - LF line endings
    - 4 spaces for Python
    - 2 spaces for JS/CSS/HTML
    - Trim trailing whitespace
    - Final newline
  
  **Acceptance Criteria**:
  - [ ] `.editorconfig` present
  - [ ] IDE respects settings
  
  **Commit**: YES
  - Message: `chore(tooling): add .editorconfig for consistent formatting`
  - Files: `.editorconfig`

### Wave 4: Polish & Verification

- [ ] **19. Add Comprehensive Input Labels and ARIA Attributes**

  **What to do**:
  - Add `<label>` for search input (visually hidden)
  - Add ARIA labels to icon-only buttons
  - Add `role="navigation"` to nav
  - Add proper heading hierarchy
  
  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: []
  
  **Acceptance Criteria**:
  - [ ] All inputs have labels
  - [ ] ARIA landmarks present
  - [ ] Heading hierarchy logical (h1 → h2 → h3)
  
  **QA Scenarios**:
  ```
  Scenario: Accessibility audit passes
    Tool: Playwright + axe-core or manual check
    Steps:
      1. Run automated a11y check
      2. Manual keyboard navigation test
    Expected: No critical or serious issues
    Evidence: .sisyphus/evidence/task-19-a11y.txt
  ```
  
  **Commit**: YES
  - Message: `feat(a11y): improve accessibility with labels and ARIA`
  - Files: `app/templates/index.html`, `app/static/css/main.css`

- [ ] **20. Implement JSON-LD Structured Data**

  **What to do**:
  - Add JSON-LD script tag to index.html
  - Define schema for WebApplication
  - Include name, description, URL, author
  
  **Acceptance Criteria**:
  - [ ] JSON-LD present in <head>
  - [ ] Valid schema.org markup
  
  **QA Scenarios**:
  ```
  Scenario: Structured data valid
    Tool: Google Rich Results Test (manual)
    Steps:
      1. View page source
      2. Find JSON-LD script
    Expected: Valid structured data present
    Evidence: .sisyphus/evidence/task-20-jsonld.txt
  ```
  
  **Commit**: YES
  - Message: `feat(seo): add JSON-LD structured data`
  - Files: `app/templates/index.html`

- [ ] **21. Add OG Image Alt Text**

  **What to do**:
  - Add `og:image:alt` meta tag to index.html
  - Describe the OG image content
  
  **Acceptance Criteria**:
  - [ ] `og:image:alt` present
  
  **Commit**: YES (grouped with Task 20)
  - Message: `feat(seo): add OG image alt text`
  - Files: `app/templates/index.html`

- [ ] **22. Docker Security Hardening**

  **What to do**:
  - Create non-root user in Dockerfile
  - Run container as non-root
  - Use specific Python version tag (not slim-latest)
  - Add HEALTHCHECK instruction
  
  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  
  **Acceptance Criteria**:
  - [ ] Non-root user created and used
  - [ ] HEALTHCHECK configured
  - [ ] Image still builds and runs
  
  **QA Scenarios**:
  ```
  Scenario: Container runs as non-root
    Tool: Bash (docker exec)
    Steps:
      1. Build: docker build -t sgnl-test .
      2. Run: docker run -d --name sgnl-test sgnl-test
      3. Check user: docker exec sgnl-test whoami
    Expected: User is not root
    Evidence: .sisyphus/evidence/task-22-docker.txt
  
  Scenario: Healthcheck works
    Tool: Bash (docker inspect)
    Steps:
      1. Inspect health: docker inspect --format='{{.State.Health.Status}}' sgnl-test
    Expected: Status is "healthy"
    Evidence: .sisyphus/evidence/task-22-health.txt
  ```
  
  **Commit**: YES
  - Message: `security(docker): run container as non-root with healthcheck`
  - Files: `Dockerfile`

- [ ] **23. Create Comprehensive Test for Security Headers**

  **What to do**:
  - Add test in `test_main.py` to verify all security headers
  - Test each header: CSP, X-Frame-Options, HSTS, etc.
  
  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  
  **Acceptance Criteria**:
  - [ ] Test file with security header assertions
  - [ ] All tests pass
  
  **QA Scenarios**:
  ```
  Scenario: Security headers tested
    Tool: Bash (pytest)
    Steps:
      1. Run: pytest tests/test_security.py -v
    Expected: All security header tests pass
    Evidence: .sisyphus/evidence/task-23-security-tests.txt
  ```
  
  **Commit**: YES
  - Message: `test(security): add comprehensive security header tests`
  - Files: `app/tests/test_security.py`

### Wave FINAL: Verification

- [ ] **F1. Plan Compliance Audit** — `oracle`
  
  **What to do**:
  - Read entire plan end-to-end
  - Verify each "Must Have" requirement is implemented
  - Check "Must NOT Have" guardrails were respected
  - Verify all evidence files exist
  
  **Output Format**:
  ```
  Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT
  ```

- [ ] **F2. Code Quality Review** — `unspecified-high`
  
  **What to do**:
  - Run `ruff check app/` - must pass
  - Run `mypy app/` - must pass
  - Run `pytest` - all tests must pass
  - Check for: `as any`, `@ts-ignore`, empty catches, `console.log`
  
  **Output Format**:
  ```
  Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT
  ```

- [ ] **F3. Full Test Suite Execution** — `unspecified-high`
  
  **What to do**:
  - Run full pytest suite with coverage
  - Verify coverage >= 80%
  - Run integration tests
  - Document any failures
  
  **Output Format**:
  ```
  Unit [N/N] | Integration [N/N] | Coverage [N%] | VERDICT
  ```

- [ ] **F4. Accessibility Audit** — `deep`
  
  **What to do**:
  - Run automated a11y tests (axe-core)
  - Manual keyboard navigation test
  - Screen reader check (if available)
  - Check color contrast
  
  **Output Format**:
  ```
  Critical [N] | Serious [N] | Moderate [N] | Minor [N] | VERDICT
  ```

---

## Final Verification Wave

### Verification Commands

```bash
# Security headers
curl -I http://localhost:8000/ | grep -E "(Content-Security-Policy|X-Frame-Options|Strict-Transport-Security)"

# Code quality
ruff check app/
mypy app/

# Tests
pytest --cov=app --cov-report=term-missing

# Docker security
docker exec sgnl-api whoami  # Should not be root

# Accessibility (manual)
# - Keyboard navigation works
# - Skip link visible on focus
# - All inputs labeled
```

### Final Checklist

- [ ] All Critical and High issues resolved
- [ ] Security headers present on all responses
- [ ] No XSS vulnerabilities
- [ ] Rate limiting comprehensive
- [ ] Code passes linting and type checking
- [ ] All tests pass with >80% coverage
- [ ] CI/CD pipeline operational
- [ ] Pre-commit hooks installed
- [ ] Documentation updated
- [ ] Docker security hardening complete

---

## Commit Strategy

### Grouped Commits by Wave

**Wave 1** (Security fixes):
```
fix(security): prevent XSS via URL sanitization
fix(ui): correct CSS file reference in template
feat(security): add comprehensive security headers middleware
feat(security): extend rate limiting to all API endpoints
feat(seo): add robots.txt and sitemap.xml
feat(a11y): add skip navigation link
```

**Wave 2** (Code organization):
```
refactor(middleware): extract RateLimitMiddleware to separate module
refactor(routes): modularize route handlers
refactor(config): extract hardcoded values to configuration
feat(config): create structured configuration system
fix(types): correct SQLAlchemy model type annotations
refactor(types): add comprehensive type hints
```

**Wave 3** (Tooling):
```
chore(tooling): add and apply ruff configuration
chore(tooling): configure mypy type checking
chore(tooling): add pre-commit hooks
chore(tooling): add test coverage reporting
chore(tooling): add .editorconfig for consistent formatting
ci(github): add CI/CD workflow with lint, type-check, and test
```

**Wave 4** (Polish):
```
feat(a11y): improve accessibility with labels and ARIA
feat(seo): add JSON-LD structured data and OG image alt
security(docker): run container as non-root with healthcheck
test(security): add comprehensive security header tests
```

---

## Success Criteria

### Objective Metrics

| Metric | Before | Target | How to Verify |
|--------|--------|--------|---------------|
| Security Headers | 0/5 | 5/5 | `curl -I` check |
| XSS Vulnerabilities | 1 | 0 | Security audit |
| Code Linting | Fail | Pass | `ruff check` |
| Type Checking | Fail | Pass | `mypy` |
| Test Coverage | Unknown | ≥80% | `pytest --cov` |
| Lines in main.py | 719 | <300 | Line count |
| Accessibility Issues | 6 | ≤2 | axe-core audit |
| CI/CD | None | Operational | GitHub Actions |

### Subjective Criteria

- [ ] Code is more maintainable and modular
- [ ] Developer experience improved with tooling
- [ ] Security posture significantly enhanced
- [ ] No regressions in functionality
- [ ] Documentation remains accurate

---

## Risk Assessment

### Low Risk
- Adding SEO files (robots.txt, sitemap.xml)
- Creating .editorconfig
- Adding type hints

### Medium Risk
- Refactoring main.py (potential import issues)
- Moving config to external files (env var changes)
- Docker changes (user permissions)

### High Risk
- Fixing XSS (must not break legitimate functionality)
- Adding security headers (CSP may break inline scripts)
- CI/CD changes (may block merges initially)

### Mitigation Strategies
1. **Comprehensive testing** - Every change has tests
2. **Staged rollout** - Security headers can be report-only first
3. **Backward compatibility** - Config changes support old env vars
4. **Rollback plan** - Each wave can be reverted independently

---

## Notes

### From Audit

The LSP errors detected additional type issues:
- SQLAlchemy model assignments (Column types)
- Optional type comparisons in main.py
- Import resolution for textstat

These are addressed in Tasks 10 and 11.

### Design Decisions

1. **Ruff over Black+Flake8**: Ruff is faster and combines both tools
2. **Pydantic Settings**: Modern approach for configuration with validation
3. **Keep Vanilla JS**: No bundler added (not needed for current complexity)
4. **Modular Routes**: Follow FastAPI best practices for large apps

---

*Plan created: 2026-03-04*  
*Total Tasks: 23 implementation + 4 verification*  
*Estimated Effort: 50 hours*
