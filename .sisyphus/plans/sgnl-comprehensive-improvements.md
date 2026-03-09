# SGNL Comprehensive Improvements Work Plan

## TL;DR

> **Objective**: Fix critical analytics bug, harden security, improve code quality, and establish developer tooling with TDD approach.
>
> **Deliverables**:
> - Fix analytics heartbeat 422 error (CRITICAL - 100% data loss)
> - Security hardening (Docker non-root, HSTS, CSP improvements)
> - Code quality fixes (SQLAlchemy types, modularize main.py)
> - Developer tooling (Ruff, mypy, pre-commit, CI/CD)
>
> **Estimated Effort**: Medium (~8-12 hours)
> **Parallel Execution**: YES - 4 waves with 4-6 tasks each
> **Critical Path**: Analytics Fix → Security → Code Quality → Tooling

---

## Context

### Original Request
User requested a comprehensive improvement audit and plan for the SGNL backend application, prioritizing a critical analytics bug fix with TDD approach.

### Interview Summary
**Key Discussions**:
- Analytics heartbeat returning 422 (CRITICAL): `navigator.sendBeacon()` sends `text/plain`, backend expects `application/json`
- Deployment: Single-instance, user has deploy access
- Test Strategy: TDD (write failing tests first)
- Scope: Comprehensive (security, quality, tooling)

**Scope Exclusions** (User Confirmed):
- No database schema migrations
- No API versioning
- No logging/monitoring overhaul
- No performance optimization beyond stated issues

**Frontend Analysis**:
- Uses external scripts only (no inline scripts)
- CSP can be strict without 'unsafe-inline' for scripts

### Metis Review
**Identified Gaps** (addressed):
- Scope boundaries: Now explicitly defined
- Deployment strategy: Single-instance confirmed
- CSP coordination: No inline scripts found, can be strict
- Analytics data: Not critical, no migration needed

---

## Work Objectives

### Core Objective
Transform SGNL from a functional but vulnerable state to a production-hardened application with proper security, maintainable code, and developer tooling.

### Concrete Deliverables
- Analytics heartbeat accepting both `application/json` and `text/plain`
- Docker running as non-root user with health check
- Security headers: HSTS, improved CSP
- SQLAlchemy type errors fixed
- main.py modularized (<300 lines)
- Ruff, mypy, pre-commit hooks configured
- Basic CI/CD pipeline

### Definition of Done
- [ ] All tests pass (existing + new)
- [ ] No type errors (mypy clean)
- [ ] No linting errors (ruff clean)
- [ ] Docker health check passes
- [ ] Analytics heartbeat returns 200 for both content types

### Must Have
1. Analytics heartbeat fix (CRITICAL)
2. Docker non-root user
3. HSTS security header
4. SQLAlchemy type fixes
5. Test coverage for analytics

### Must NOT Have (Guardrails)
- No database schema changes
- No API versioning
- No logging/monitoring overhaul
- No "while I'm here" refactoring outside scope
- No changes without corresponding tests
- No breaking API changes

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest with async support)
- **Automated tests**: YES (TDD for all changes)
- **Framework**: pytest + pytest-asyncio
- **Coverage Target**: 80% for modified files

### QA Policy
Every task includes agent-executed QA scenarios:
- **API Tests**: Use curl for endpoint verification
- **Docker Tests**: Use docker exec for container verification
- **Security Tests**: Use curl -I for header verification
- **Code Quality**: Use ruff/mypy for static analysis

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (CRITICAL - Start Immediately - Analytics Fix):
├── Task 1: Write failing test for analytics heartbeat [quick]
├── Task 2: Fix analytics heartbeat endpoint [quick]
├── Task 3: Add integration tests for beacon behavior [quick]
└── Task 4: Add error handling tests [quick]

Wave 2 (After Wave 1 - Security Hardening):
├── Task 5: Add Docker non-root user [quick]
├── Task 6: Add Docker health check [quick]
├── Task 7: Add HSTS security header [quick]
├── Task 8: Improve CSP header (remove unsafe-inline for scripts) [quick]
└── Task 9: Add security header tests [quick]

Wave 3 (After Wave 2 - Code Quality):
├── Task 10: Fix SQLAlchemy type errors [quick]
├── Task 11: Add type hints to analytics functions [quick]
├── Task 12: Extract routes from main.py (Phase 1) [unspecified-high]
└── Task 13: Extract services from main.py (Phase 2) [deep]

Wave 4 (After Wave 3 - Developer Tooling):
├── Task 14: Configure Ruff linter/formatter [quick]
├── Task 15: Configure mypy type checking [quick]
├── Task 16: Add pre-commit hooks [quick]
└── Task 17: Create GitHub Actions CI workflow [unspecified-high]

Wave FINAL (After ALL tasks - Verification):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Full test suite execution (unspecified-high)
└── Task F4: Security verification (deep)

Critical Path: T1 → T2 → T5 → T10 → T12 → T14 → F1-F4
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 4 (Waves 1 & 2)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|------------|--------|
| 1-4 | - | 5-9 |
| 5-9 | 1-4 | 10-13 |
| 10-13 | 5-9 | 14-17 |
| 14-17 | 10-13 | F1-F4 |
| F1-F4 | 14-17 | - |

### Agent Dispatch Summary

- **Wave 1**: **4** tasks → All `quick`
- **Wave 2**: **5** tasks → All `quick`
- **Wave 3**: **4** tasks → T10-T11 `quick`, T12 `unspecified-high`, T13 `deep`
- **Wave 4**: **4** tasks → T14-T16 `quick`, T17 `unspecified-high`
- **Final**: **4** tasks → F1 `oracle`, F2-F3 `unspecified-high`, F4 `deep`

---

## TODOs

### Wave 1: CRITICAL - Analytics Fix (TDD)

- [ ] **1. Write Failing Test for Analytics Heartbeat**

  **What to do**:
  - Create test file `tests/test_analytics_heartbeat.py`
  - Write test that sends POST to `/analytics/heartbeat` with `Content-Type: text/plain;charset=UTF-8`
  - Test should FAIL with 422 (current behavior)
  - This reproduces the `navigator.sendBeacon()` behavior

  **Must NOT do**:
  - Do not modify any implementation code
  - Do not skip the failing test - it MUST fail first

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: Single test file creation, straightforward

  **Parallelization**:
  - **Can Run In Parallel**: NO - first task, establishes test pattern
  - **Blocks**: Task 2 (implementation)
  - **Blocked By**: None

  **References**:
  - `app/analytics_routes.py:51-65` - Current heartbeat endpoint
  - `app/static/js/analytics.js:40-46` - Frontend beacon call
  - `tests/test_main.py` - Existing test patterns

  **Acceptance Criteria**:
  - [ ] Test file created at `tests/test_analytics_heartbeat.py`
  - [ ] Test `test_heartbeat_text_plain_content_type` exists
  - [ ] Running `pytest tests/test_analytics_heartbeat.py -v` shows FAIL (422 error)

  **QA Scenarios**:
  ```
  Scenario: Failing test reproduces 422 error
    Tool: Bash (pytest)
    Steps:
      1. Run: pytest tests/test_analytics_heartbeat.py::test_heartbeat_text_plain_content_type -v
    Expected: Test FAILS with assertion about 422 status code
    Failure Indicators: Test passes (means bug is already fixed) or test errors (syntax issue)
    Evidence: .sisyphus/evidence/task-1-failing-test.txt
  ```

  **Commit**: YES
  - Message: `test(analytics): add failing test for text/plain heartbeat`
  - Files: `app/tests/test_analytics_heartbeat.py`

- [ ] **2. Fix Analytics Heartbeat Endpoint**

  **What to do**:
  - Modify `analytics_routes.py` heartbeat endpoint to accept both:
    - `Content-Type: application/json` (backward compatible)
    - `Content-Type: text/plain;charset=UTF-8` (sendBeacon)
  - Parse request body manually for text/plain content type
  - Validate session_id and path fields

  **Must NOT do**:
  - Do not break existing JSON clients
  - Do not change the response format
  - Do not add new dependencies

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: Single endpoint modification, clear fix

  **Parallelization**:
  - **Can Run In Parallel**: NO - depends on Task 1
  - **Blocks**: Tasks 3-4
  - **Blocked By**: Task 1 (failing test must exist)

  **References**:
  - `app/analytics_routes.py:51-65` - Endpoint to modify
  - FastAPI Request body reading: `request.body()` or `request.json()`
  - Test from Task 1 - must pass after fix

  **Acceptance Criteria**:
  - [ ] Endpoint accepts `text/plain;charset=UTF-8` content type
  - [ ] Endpoint still accepts `application/json` (backward compatible)
  - [ ] All tests pass including Task 1's test
  - [ ] No 422 errors in logs when frontend sends heartbeat

  **QA Scenarios**:
  ```
  Scenario: Heartbeat accepts text/plain content type
    Tool: Bash (curl)
    Steps:
      1. Run: curl -X POST http://localhost:8000/analytics/heartbeat \
           -H "Content-Type: text/plain;charset=UTF-8" \
           -d '{"session_id":"test-123","path":"/test"}' \
           -w "\nHTTP_CODE:%{http_code}"
    Expected: HTTP 200, body contains {"status":"ok"}
    Failure Indicators: HTTP 422 (validation error) or HTTP 500
    Evidence: .sisyphus/evidence/task-2-text-plain-fix.txt

  Scenario: Heartbeat still accepts application/json (backward compat)
    Tool: Bash (curl)
    Steps:
      1. Run: curl -X POST http://localhost:8000/analytics/heartbeat \
           -H "Content-Type: application/json" \
           -d '{"session_id":"test-456","path":"/test"}' \
           -w "\nHTTP_CODE:%{http_code}"
    Expected: HTTP 200, body contains {"status":"ok"}
    Failure Indicators: HTTP 422 or HTTP 500
    Evidence: .sisyphus/evidence/task-2-json-compat.txt

  Scenario: All tests pass after fix
    Tool: Bash (pytest)
    Steps:
      1. Run: pytest tests/test_analytics_heartbeat.py -v
    Expected: All tests PASS
    Failure Indicators: Any test failure
    Evidence: .sisyphus/evidence/task-2-all-tests-pass.txt
  ```

  **Commit**: YES
  - Message: `fix(analytics): accept text/plain content-type in heartbeat endpoint`
  - Files: `app/analytics_routes.py`

- [ ] **3. Add Integration Tests for Beacon Behavior**

  **What to do**:
  - Add test that simulates `navigator.sendBeacon()` with actual HTTP request
  - Test edge cases: empty payload, missing fields, large payload
  - Test session not found scenario

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Task 4
  - **Blocks**: None
  - **Blocked By**: Task 2 (fix must be in place)

  **References**:
  - `tests/test_analytics_heartbeat.py` - Add tests here
  - `app/analytics_routes.py:51-65` - Endpoint behavior

  **Acceptance Criteria**:
  - [ ] Integration test for sendBeacon simulation exists
  - [ ] Test passes
  - [ ] Edge cases covered

  **QA Scenarios**:
  ```
  Scenario: Integration test simulates sendBeacon
    Tool: Bash (pytest)
    Steps:
      1. Run: pytest tests/test_analytics_heartbeat.py -v
    Expected: All tests PASS, coverage includes text/plain handling
    Evidence: .sisyphus/evidence/task-3-integration-tests.txt
  ```

  **Commit**: YES
  - Message: `test(analytics): add integration tests for sendBeacon behavior`
  - Files: `app/tests/test_analytics_heartbeat.py`

- [ ] **4. Add Error Handling Tests**

  **What to do**:
  - Test malformed JSON in payload (should return 400, not 500)
  - Test empty payload
  - Test missing session_id field
  - Test invalid JSON structure

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Task 3
  - **Blocks**: None
  - **Blocked By**: Task 2

  **Acceptance Criteria**:
  - [ ] Error handling tests exist
  - [ ] All tests pass
  - [ ] No 500 errors for invalid input

  **QA Scenarios**:
  ```
  Scenario: Malformed JSON returns 400 not 500
    Tool: Bash (curl)
    Steps:
      1. Run: curl -X POST http://localhost:8000/analytics/heartbeat \
           -H "Content-Type: text/plain;charset=UTF-8" \
           -d 'not valid json' \
           -w "\nHTTP_CODE:%{http_code}"
    Expected: HTTP 400 (bad request), not 500
    Evidence: .sisyphus/evidence/task-4-error-handling.txt

  Scenario: Error tests pass
    Tool: Bash (pytest)
    Steps:
      1. Run: pytest tests/test_analytics_heartbeat.py -v
    Expected: All error handling tests PASS
    Evidence: .sisyphus/evidence/task-4-error-tests.txt
  ```

  **Commit**: YES
  - Message: `test(analytics): add error handling tests for heartbeat`
  - Files: `app/tests/test_analytics_heartbeat.py`

### Wave 2: Security Hardening

- [ ] **5. Add Docker Non-Root User**

  **What to do**:
  - Modify `Dockerfile` to create non-root user
  - Add `RUN useradd -m -r appuser` 
  - Add `USER appuser` before CMD
  - Ensure permissions are correct for /app directory

  **Must NOT do**:
  - Do not break the application
  - Do not change the application code

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 6-9
  - **Blocks**: None
  - **Blocked By**: Tasks 1-4 (analytics stable)

  **References**:
  - `Dockerfile` - File to modify
  - Docker security best practices

  **Acceptance Criteria**:
  - [ ] Dockerfile creates `appuser` user
  - [ ] Container runs as `appuser`
  - [ ] Application still works

  **QA Scenarios**:
  ```
  Scenario: Container runs as non-root
    Tool: Bash (docker)
    Steps:
      1. Rebuild: docker compose build
      2. Start: docker compose up -d
      3. Check user: docker exec sgnl-api whoami
    Expected: Output is "appuser" (not "root")
    Failure Indicators: Output is "root" or container fails to start
    Evidence: .sisyphus/evidence/task-5-non-root.txt
  ```

  **Commit**: YES
  - Message: `security(docker): run container as non-root user`
  - Files: `Dockerfile`

- [ ] **6. Add Docker Health Check**

  **What to do**:
  - Add HEALTHCHECK instruction to Dockerfile
  - Use curl to check /health endpoint
  - Set appropriate intervals and retries

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 5, 7-9
  - **Blocked By**: Tasks 1-4

  **References**:
  - `Dockerfile` - Add HEALTHCHECK
  - `app/main.py:627-638` - Health endpoint

  **Acceptance Criteria**:
  - [ ] HEALTHCHECK in Dockerfile
  - [ ] `docker inspect` shows health status

  **QA Scenarios**:
  ```
  Scenario: Docker health check works
    Tool: Bash (docker)
    Steps:
      1. Rebuild and start container
      2. Run: docker inspect --format='{{.State.Health.Status}}' sgnl-api
    Expected: Status is "healthy"
    Failure Indicators: Status is "unhealthy" or "starting" (stuck)
    Evidence: .sisyphus/evidence/task-6-healthcheck.txt
  ```

  **Commit**: YES
  - Message: `feat(docker): add healthcheck instruction`
  - Files: `Dockerfile`

- [ ] **7. Add HSTS Security Header**

  **What to do**:
  - Add `Strict-Transport-Security` header to `SecurityHeadersMiddleware`
  - Use `max-age=31536000; includeSubDomains`
  - Make it environment-aware (skip in development)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 5-6, 8-9
  - **Blocked By**: Tasks 1-4

  **References**:
  - `app/main.py:167-196` - SecurityHeadersMiddleware
  - OWASP HSTS guidelines

  **Acceptance Criteria**:
  - [ ] HSTS header added
  - [ ] Header visible in responses

  **QA Scenarios**:
  ```
  Scenario: HSTS header present
    Tool: Bash (curl)
    Steps:
      1. Run: curl -I http://localhost:8000/health | grep -i "strict-transport-security"
    Expected: Header present with max-age >= 31536000
    Failure Indicators: Header not found
    Evidence: .sisyphus/evidence/task-7-hsts.txt
  ```

  **Commit**: YES
  - Message: `feat(security): add HSTS header to security middleware`
  - Files: `app/main.py`

- [ ] **8. Improve CSP Header**

  **What to do**:
  - Remove `'unsafe-inline'` from `script-src` (frontend uses external scripts only)
  - Keep `'unsafe-inline'` for `style-src` if needed
  - Verify frontend still works

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 5-7, 9
  - **Blocked By**: Tasks 1-4

  **References**:
  - `app/main.py:186-194` - Current CSP
  - Frontend analysis confirmed no inline scripts

  **Acceptance Criteria**:
  - [ ] CSP `script-src` does not have `'unsafe-inline'`
  - [ ] Frontend still loads and functions
  - [ ] Console shows no CSP violations

  **QA Scenarios**:
  ```
  Scenario: CSP improved and frontend works
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:8000
      2. Check browser console for CSP errors
      3. Verify page loads correctly
    Expected: No CSP violations, page functional
    Evidence: .sisyphus/evidence/task-8-csp.png
  ```

  **Commit**: YES
  - Message: `fix(security): remove unsafe-inline from CSP script-src`
  - Files: `app/main.py`

- [ ] **9. Add Security Header Tests**

  **What to do**:
  - Create `tests/test_security_headers.py`
  - Test each security header is present
  - Test header values are correct

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 5-8
  - **Blocked By**: Tasks 1-4

  **Acceptance Criteria**:
  - [ ] Test file created
  - [ ] All security headers tested
  - [ ] Tests pass

  **QA Scenarios**:
  ```
  Scenario: Security header tests pass
    Tool: Bash (pytest)
    Steps:
      1. Run: pytest tests/test_security_headers.py -v
    Expected: All tests PASS
    Evidence: .sisyphus/evidence/task-9-security-tests.txt
  ```

  **Commit**: YES
  - Message: `test(security): add security header verification tests`
  - Files: `app/tests/test_security_headers.py`

### Wave 3: Code Quality

- [ ] **10. Fix SQLAlchemy Type Errors**

  **What to do**:
  - Fix type annotations in `analytics_routes.py:59,148`
  - Use proper SQLAlchemy 2.0 patterns for attribute assignment
  - Fix Column comparison issues

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Task 11
  - **Blocked By**: Wave 2 complete

  **References**:
  - `app/analytics_routes.py:59,148` - Type errors
  - `app/analytics_models.py` - Model definitions
  - SQLAlchemy 2.0 documentation

  **Acceptance Criteria**:
  - [ ] No LSP errors in analytics_routes.py
  - [ ] mypy passes for analytics files
  - [ ] Analytics endpoints still work

  **QA Scenarios**:
  ```
  Scenario: Type errors fixed
    Tool: Bash (mypy)
    Steps:
      1. Run: mypy app/analytics_routes.py --no-error-summary
    Expected: Exit code 0, no errors
    Failure Indicators: Any type errors reported
    Evidence: .sisyphus/evidence/task-10-mypy.txt
  ```

  **Commit**: YES
  - Message: `fix(types): correct SQLAlchemy type annotations in analytics`
  - Files: `app/analytics_routes.py`, `app/analytics_models.py`

- [ ] **11. Add Type Hints to Analytics Functions**

  **What to do**:
  - Add return type hints to functions missing them
  - Add parameter type hints where missing
  - Ensure mypy passes

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Task 10
  - **Blocked By**: Wave 2 complete

  **Acceptance Criteria**:
  - [ ] All public functions have type hints
  - [ ] mypy passes

  **Commit**: YES
  - Message: `refactor(types): add type hints to analytics functions`
  - Files: `app/analytics_utils.py`, `app/analytics_middleware.py`

- [ ] **12. Extract Routes from main.py (Phase 1)**

  **What to do**:
  - Create `app/routes/` directory
  - Extract route handlers into modules:
    - `routes/scan.py` - scan-topic, fast-search, deep-scan
    - `routes/extract.py` - extract endpoint
    - `routes/analytics_proxy.py` - check-density, analyze-results
  - Update main.py to use `app.include_router()`
  - Keep main.py under 500 lines after this phase

  **Must NOT do**:
  - Do not change API contracts
  - Do not remove any functionality

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO - large refactoring
  - **Blocks**: Task 13
  - **Blocked By**: Tasks 10-11

  **References**:
  - `app/main.py` - Source file
  - `app/analytics_routes.py` - Example of route module pattern
  - FastAPI router documentation

  **Acceptance Criteria**:
  - [ ] Routes organized in `app/routes/` directory
  - [ ] main.py < 500 lines
  - [ ] All endpoints still functional
  - [ ] All tests pass

  **QA Scenarios**:
  ```
  Scenario: All endpoints work after refactor
    Tool: Bash (curl)
    Steps:
      1. Test /health
      2. Test /fast-search (with valid request)
      3. Test /extract (with sample URL)
      4. Test /deep-scan (with sample URL)
    Expected: All return expected responses
    Evidence: .sisyphus/evidence/task-12-routes-refactor.txt
  ```

  **Commit**: YES
  - Message: `refactor(routes): extract route handlers to separate modules`
  - Files: `app/routes/*.py`, `app/main.py`

- [ ] **13. Extract Services from main.py (Phase 2)**

  **What to do**:
  - Move business logic from route handlers to `services/`
  - Create service classes/functions for:
    - SearchService (fast-search, scan-topic logic)
    - ExtractionService (deep-scan, extract logic)
  - Keep main.py under 300 lines after this phase

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO - depends on Task 12
  - **Blocked By**: Task 12

  **Acceptance Criteria**:
  - [ ] main.py < 300 lines
  - [ ] Business logic in services/
  - [ ] All tests pass
  - [ ] No functionality changes

  **QA Scenarios**:
  ```
  Scenario: Code organization improved
    Tool: Bash
    Steps:
      1. Run: wc -l app/main.py
      2. Run: pytest tests/ -v
    Expected: main.py < 300 lines, all tests pass
    Evidence: .sisyphus/evidence/task-13-services-refactor.txt
  ```

  **Commit**: YES
  - Message: `refactor(services): extract business logic to service layer`
  - Files: `app/services/*.py`, `app/main.py`

### Wave 4: Developer Tooling

- [ ] **14. Configure Ruff Linter/Formatter**

  **What to do**:
  - Add Ruff configuration to `pyproject.toml`
  - Set line length to 100
  - Enable linting rules
  - Run `ruff format app/` to format code
  - Run `ruff check app/ --fix` to fix issues

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 15-17
  - **Blocked By**: Wave 3 complete

  **Acceptance Criteria**:
  - [ ] `pyproject.toml` has Ruff config
  - [ ] `ruff check app/` passes
  - [ ] `ruff format --check app/` passes

  **QA Scenarios**:
  ```
  Scenario: Ruff passes
    Tool: Bash (ruff)
    Steps:
      1. Run: ruff check app/
      2. Run: ruff format --check app/
    Expected: No errors
    Evidence: .sisyphus/evidence/task-14-ruff.txt
  ```

  **Commit**: YES
  - Message: `chore(tooling): configure Ruff for linting and formatting`
  - Files: `pyproject.toml`, all Python files

- [ ] **15. Configure mypy Type Checking**

  **What to do**:
  - Add mypy configuration to `pyproject.toml`
  - Set Python version to 3.11
  - Configure strict mode with reasonable exceptions
  - Fix any remaining type issues

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 14, 16-17
  - **Blocked By**: Wave 3 complete

  **Acceptance Criteria**:
  - [ ] `pyproject.toml` has mypy config
  - [ ] `mypy app/` passes

  **Commit**: YES
  - Message: `chore(tooling): configure mypy for type checking`
  - Files: `pyproject.toml`

- [ ] **16. Add Pre-commit Hooks**

  **What to do**:
  - Create `.pre-commit-config.yaml`
  - Include: ruff, mypy, check for large files
  - Run `pre-commit install`
  - Run `pre-commit run --all-files`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 14-15, 17
  - **Blocked By**: Tasks 14-15 (tools configured)

  **Acceptance Criteria**:
  - [ ] `.pre-commit-config.yaml` exists
  - [ ] Hooks installed
  - [ ] All files pass pre-commit

  **Commit**: YES
  - Message: `chore(tooling): add pre-commit hooks`
  - Files: `.pre-commit-config.yaml`

- [ ] **17. Create GitHub Actions CI Workflow**

  **What to do**:
  - Create `.github/workflows/ci.yml`
  - Run on: push, pull_request
  - Steps: install deps, ruff check, mypy, pytest with coverage
  - Upload coverage report

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 14-16
  - **Blocked By**: Tasks 14-15 (tools configured)

  **Acceptance Criteria**:
  - [ ] `.github/workflows/ci.yml` exists
  - [ ] Workflow runs on push
  - [ ] All checks pass

  **Commit**: YES
  - Message: `ci(github): add CI workflow with lint, type-check, and test`
  - Files: `.github/workflows/ci.yml`

### Wave FINAL: Verification

- [ ] **F1. Plan Compliance Audit**

  **What to do**:
  - Read plan end-to-end
  - Verify each "Must Have" is implemented
  - Check "Must NOT Have" guardrails respected
  - Verify evidence files exist

  **Recommended Agent Profile**:
  - **Category**: `oracle`
  - **Skills**: []

  **Output Format**:
  ```
  Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT
  ```

- [ ] **F2. Code Quality Review**

  **What to do**:
  - Run `ruff check app/`
  - Run `mypy app/`
  - Run `pytest tests/ --cov=app`
  - Check for code smells: `as any`, empty catches, `print` statements

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Output Format**:
  ```
  Lint [PASS/FAIL] | Types [PASS/FAIL] | Tests [N pass/N fail] | Coverage [N%] | VERDICT
  ```

- [ ] **F3. Full Test Suite Execution**

  **What to do**:
  - Run full pytest suite with coverage
  - Verify coverage >= 80%
  - Document any failures

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Output Format**:
  ```
  Unit [N/N] | Integration [N/N] | Coverage [N%] | VERDICT
  ```

- [ ] **F4. Security Verification**

  **What to do**:
  - Verify Docker runs as non-root
  - Verify all security headers present
  - Verify analytics heartbeat works
  - Run security header tests

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Output Format**:
  ```
  Docker [PASS/FAIL] | Headers [N/N] | Analytics [PASS/FAIL] | VERDICT
  ```

---

## Final Verification Wave

### Verification Commands

```bash
# Analytics heartbeat
curl -X POST http://localhost:8000/analytics/heartbeat \
  -H "Content-Type: text/plain;charset=UTF-8" \
  -d '{"session_id":"test","path":"/"}'
# Expected: {"status":"ok"}

# Security headers
curl -I http://localhost:8000/health | grep -i "strict-transport-security"

# Docker security
docker exec sgnl-api whoami
# Expected: appuser (not root)

# Code quality
ruff check app/
mypy app/

# Tests
pytest tests/ --cov=app --cov-report=term-missing
```

### Final Checklist

- [ ] Analytics heartbeat returns 200 for text/plain
- [ ] Docker runs as non-root user
- [ ] HSTS header present
- [ ] CSP header improved
- [ ] SQLAlchemy type errors fixed
- [ ] main.py < 300 lines
- [ ] Ruff passes
- [ ] mypy passes
- [ ] All tests pass with >80% coverage
- [ ] CI pipeline runs successfully

---

## Commit Strategy

### Wave 1 (Analytics Fix)
```
test(analytics): add failing test for text/plain heartbeat
fix(analytics): accept text/plain content-type in heartbeat endpoint
test(analytics): add integration tests for sendBeacon behavior
test(analytics): add error handling tests for heartbeat
```

### Wave 2 (Security)
```
security(docker): run container as non-root user with healthcheck
feat(security): add HSTS header to security middleware
fix(security): remove unsafe-inline from CSP script-src
test(security): add security header verification tests
```

### Wave 3 (Code Quality)
```
fix(types): correct SQLAlchemy type annotations in analytics
refactor(routes): extract routes from main.py to separate modules
refactor(services): extract business logic to services layer
```

### Wave 4 (Tooling)
```
chore(tooling): configure Ruff for linting and formatting
chore(tooling): configure mypy for type checking
chore(tooling): add pre-commit hooks
ci(github): add CI workflow with lint, type-check, and test
```

---

## Success Criteria

### Verification Commands
```bash
# All must pass
pytest tests/ -v                    # Tests pass
ruff check app/                     # No lint errors
mypy app/                           # No type errors
docker exec sgnl-api whoami         # Returns 'appuser'
curl -I localhost:8000/health | grep -i hsts  # Header present
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass with >80% coverage
- [ ] No type errors
- [ ] No lint errors
- [ ] Security headers verified