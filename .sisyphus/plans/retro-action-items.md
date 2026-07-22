# Retro Action Items Fix — Work Plan

## TL;DR

> **Quick Summary**: Fix 3 retrospective action items: Redis async initialization bug, Ruff documentation in AGENTS.md, and temp file cleanup.
> 
> **Deliverables**:
> - Health endpoint returns `redis_available: true`
> - AGENTS.md updated with Ruff commands
> - 5 temp files deleted from repo
> 
> **Estimated Effort**: Quick
> **Parallel Execution**: YES — Wave 1 (2 tasks), Wave 2 (Redis fix)
> **Critical Path**: Task 1 (Redis fix) → Task 4 (QA verification)

---

## Context

### Original Request
Fix 3 action items from sprint retrospective:
1. Redis async initialization bug → `redis_available: true` in health check
2. Verify Ruff works locally, update AGENTS.md documentation
3. Delete temp files (`100`, `20`, `50`, `=5.0.0`, `main-searchfix.css`)

### Interview Summary
**Key Discussions**:
- Redis bug: `HybridCache._init_redis()` uses `loop.run_until_complete()` during `__init__` — fails when FastAPI has running event loop
- Ruff: Already configured in `pyproject.toml` (lines 35-65), issue is local tool availability + AGENTS.md documentation
- Temp files: All untracked (`??`), never committed. `=5.0.0` is pip error output, safe to delete

**Research Findings**:
- `=5.0.0` content: Pip externally-managed-environment error output — junk file
- `run_until_complete`: 5 occurrences in `cache/__init__.py` — fix localized to that file
- Module-level singletons (`extractor`, `heuristic_analyzer`) call `get_cache()` inside functions — no import-time initialization issue

### Metis Review
**Identified Gaps** (addressed):
- **Redis edge cases**: What if Redis down during startup? → Graceful fallback required
- **Missing acceptance criteria**: Added QA commands with exact curl/jq expectations
- **Guardrails**: Must not change HybridCache public API, must preserve sync interface

---

## Work Objectives

### Core Objective
Fix Redis async initialization, document Ruff commands, clean repo root.

### Concrete Deliverables
- `app/cache/__init__.py` — Fixed async initialization with lazy pattern
- `AGENTS.md` — Updated Linting section with Ruff commands
- Deleted files: `100`, `20`, `50`, `=5.0.0`, `app/static/css/main-searchfix.css`

### Definition of Done
- [ ] `curl -s http://localhost:8000/health | jq '.redis.available'` → `true`
- [ ] `grep -A 3 "### Linting" AGENTS.md` shows Ruff commands
- [ ] `ls /root/sgnl-backend/{100,20,50,=5.0.0}` → "No such file"
- [ ] `ls /root/sgnl-backend/app/static/css/main-searchfix.css` → "No such file"
- [ ] All tests pass: `pytest app/tests/ -v`

### Must Have
- Redis shows `available: true` in health check (when Redis container running)
- Graceful fallback if Redis unavailable (no startup hang)
- AGENTS.md has exact Ruff commands: `ruff check app/` and `ruff format app/`

### Must NOT Have (Guardrails)
- **Redis**: Do NOT change HybridCache public API (`get`, `set`, `clear`, `get_stats`)
- **Redis**: Do NOT break existing tests
- **Redis**: Do NOT make sync methods async-only — preserve sync interface
- **Ruff**: Do NOT add new linting rules beyond existing config
- **Ruff**: Do NOT auto-fix violations without review
- **Files**: Do NOT delete files beyond the 5 named

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest in pyproject.toml)
- **Automated tests**: Tests-after (verify after implementation)
- **Framework**: pytest

### QA Policy
Every task includes agent-executed QA scenarios.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately - independent tasks):
├── Task 1: Delete temp files [quick]
├── Task 2: Update AGENTS.md with Ruff commands [quick]

Wave 2 (After Wave 1 - Redis fix):
├── Task 3: Fix Redis async initialization [deep]
└── Task 4: QA verification [quick]

Critical Path: Task 3 → Task 4
Parallel Speedup: 2 tasks in Wave 1 run concurrently
```

---

## TODOs

- [x] 1. Delete temporary files from repo root

  **What to do**:
  - Delete untracked files: `100`, `20`, `50`, `=5.0.0` from `/root/sgnl-backend/`
  - Delete `app/static/css/main-searchfix.css` (patch CSS file, no code references)
  - Verify deletion doesn't affect any functionality

  **Must NOT do**:
  - Do NOT search for or delete other "suspicious" files beyond the 5 named
  - Do NOT investigate file purposes (already verified: `=5.0.0` is pip error output)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple file deletion, no logic changes
  - **Skills**: [`git-master`]
    - `git-master`: Verify clean git operations, commit with proper message

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 2)
  - **Blocks**: None
  - **Blocked By**: None

  **References**:
  - `/root/sgnl-backend/=5.0.0` — Pip error output file (lines 1-20 show externally-managed-environment error)
  - `app/static/css/main.css` — Canonical CSS (main-searchfix.css is patch override)

  **Acceptance Criteria**:
  - [ ] `ls /root/sgnl-backend/{100,20,50,=5.0.0}` → "No such file or directory"
  - [ ] `ls /root/sgnl-backend/app/static/css/main-searchfix.css` → "No such file or directory"

  **QA Scenarios**:
  ```
  Scenario: Files deleted successfully
    Tool: Bash
    Preconditions: Files exist before deletion
    Steps:
      1. ls /root/sgnl-backend/100 /root/sgnl-backend/20 /root/sgnl-backend/50 /root/sgnl-backend/=5.0.0 2>&1
      2. Assert: all return "No such file or directory"
      3. ls /root/sgnl-backend/app/static/css/main-searchfix.css 2>&1
      4. Assert: returns "No such file or directory"
    Expected Result: All 5 files no longer exist
    Evidence: .sisyphus/evidence/task-1-files-deleted.txt
  ```

  **Evidence to Capture**:
  - [ ] ls output showing files don't exist

  **Commit**: YES
  - Message: `chore: remove temporary files (100, 20, 50, =5.0.0, main-searchfix.css)`
  - Files: All 5 deleted files

---

- [x] 2. Update AGENTS.md with Ruff linting commands

  **What to do**:
  - Add Ruff commands to AGENTS.md "### Linting" section
  - Commands to document: `ruff check app/` and `ruff format app/`
  - Note that pyproject.toml already has Ruff configuration (lines 35-65)

  **Must NOT do**:
  - Do NOT add new linting rules to pyproject.toml
  - Do NOT auto-fix existing violations
  - Do NOT add pre-commit hooks (out of scope)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Documentation update, no code changes
  - **Skills**: []
    - No special skills needed for documentation edit

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: None
  - **Blocked By**: None

  **References**:
  - `AGENTS.md:## Commands` — Existing command documentation structure
  - `pyproject.toml:35-65` — Ruff configuration (target-version, lint rules, format settings)
  - CI workflow: `.github/workflows/ci.yml:31-33` — Shows `ruff check app/` usage

  **Acceptance Criteria**:
  - [ ] AGENTS.md has "### Linting" section with `ruff check app/` command
  - [ ] AGENTS.md has `ruff format app/` command
  - [ ] Note about pyproject.toml config included

  **QA Scenarios**:
  ```
  Scenario: AGENTS.md contains Ruff commands
    Tool: Bash (grep)
    Preconditions: AGENTS.md exists
    Steps:
      1. grep -A 5 "### Linting" AGENTS.md
      2. Assert output contains "ruff check app/"
      3. Assert output contains "ruff format app/"
    Expected Result: Both commands documented in Linting section
    Evidence: .sisyphus/evidence/task-2-ruff-docs.txt
  ```

  **Evidence to Capture**:
  - [ ] grep output showing Ruff commands in AGENTS.md

  **Commit**: YES
  - Message: `docs: add Ruff linting commands to AGENTS.md`
  - Files: `AGENTS.md`

---

- [x] 3. Fix Redis async initialization in HybridCache

  **What to do**:
  - Fix `HybridCache._init_redis()` in `app/cache/__init__.py`
  - Replace `loop.run_until_complete()` pattern with lazy async initialization
  - Use proper async context when Redis needs to be accessed
  - Preserve synchronous public API (`get`, `set`, `clear`, `get_stats`)

  **Implementation approach**:
  - Option A: Lazy initialization — defer Redis connection until first async call
  - Option B: FastAPI lifespan — register startup event to initialize Redis
  - Recommended: **Lazy initialization** with `asyncio.get_running_loop()` check

  **Key changes**:
  - Remove `loop.run_until_complete(self._redis_cache.ping())` from `_init_redis()`
  - Add `_ensure_redis_connected()` async method called before each Redis operation
  - Keep `_redis_available = False` initially, set to `True` on successful first operation

  **Must NOT do**:
  - Do NOT change HybridCache public API signature
  - Do NOT make sync methods async-only
  - Do NOT break existing tests
  - Do NOT add new Redis features (connection pooling config, retries beyond existing)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Requires understanding async lifecycle, potential ripple effects
  - **Skills**: [`git-master`, `modern-python`]
    - `git-master`: Atomic commits, verify no unintended changes
    - `modern-python`: Python async patterns, tooling expertise

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (sequential)
  - **Blocks**: Task 4 (QA verification)
  - **Blocked By**: Task 1, Task 2 (Wave 1 complete)

  **References**:
  - `app/cache/__init__.py:155-170` — `_init_redis()` method (broken pattern)
  - `app/cache/__init__.py:191-206` — `get()` method (needs lazy init)
  - `app/cache/__init__.py:209-223` — `set()` method (needs lazy init)
  - `app/cache/redis_cache.py` — RedisCache async implementation
  - `app/main.py:932-934` — Existing shutdown event pattern

  **Acceptance Criteria**:
  - [ ] `curl -s http://localhost:8000/health | jq '.redis.available'` returns `true` (when Redis running)
  - [ ] No "RuntimeWarning: coroutine was never awaited" in logs
  - [ ] App starts without hanging (< 30 seconds)
  - [ ] All tests pass: `cd app && pytest tests/ -v`

  **QA Scenarios**:
  ```
  Scenario: Redis shows available in health check
    Tool: Bash (curl + jq)
    Preconditions: Redis container running, app started
    Steps:
      1. docker compose up -d --build
      2. sleep 10
      3. curl -s http://localhost:8000/health | jq '.redis.available'
      4. Assert: returns "true" (boolean, not string)
    Expected Result: redis.available = true
    Evidence: .sisyphus/evidence/task-3-health-check.json

  Scenario: App starts without hang
    Tool: Bash
    Preconditions: Clean state
    Steps:
      1. time docker compose up -d --build 2>&1
      2. Assert: startup time < 30 seconds
      3. curl -s http://localhost:8000/health
      4. Assert: returns valid JSON with status "ok"
    Expected Result: App operational within 30s
    Evidence: .sisyphus/evidence/task-3-startup-time.txt

  Scenario: No async warnings in logs
    Tool: Bash
    Preconditions: App running
    Steps:
      1. docker compose logs sgnl-api 2>&1 | grep -i "coroutine\|RuntimeWarning\|never awaited"
      2. Assert: no matches (empty output)
    Expected Result: Clean logs without async warnings
    Evidence: .sisyphus/evidence/task-3-logs-clean.txt
  ```

  **Evidence to Capture**:
  - [ ] Health check JSON output
  - [ ] Startup time measurement
  - [ ] Log grep showing no warnings

  **Commit**: YES
  - Message: `fix(cache): use lazy async initialization for Redis connection`
  - Files: `app/cache/__init__.py`
  - Pre-commit: `cd app && pytest tests/ -v`

---

- [x] 4. Final QA verification

  **What to do**:
  - Run full test suite
  - Verify health endpoint
  - Check all acceptance criteria from previous tasks

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Verification, no code changes
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (sequential, after Task 3)
  - **Blocks**: None (final task)
  - **Blocked By**: Task 3

  **Acceptance Criteria**:
  - [ ] All tests pass: `cd app && pytest tests/ -v`
  - [ ] Health check returns `redis.available: true`
  - [ ] No async warnings in logs
  - [ ] Temp files deleted
  - [ ] AGENTS.md has Ruff commands

  **QA Scenarios**:
  ```
  Scenario: All acceptance criteria verified
    Tool: Bash
    Steps:
      1. cd app && pytest tests/ -v --tb=short
      2. curl -s http://localhost:8000/health | jq
      3. ls /root/sgnl-backend/{100,20,50,=5.0.0} 2>&1
      4. grep -A 5 "### Linting" AGENTS.md
    Expected Result: All pass
    Evidence: .sisyphus/evidence/task-4-final-qa.txt
  ```

  **Commit**: NO (verification only)

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search for forbidden patterns. Check evidence files exist.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `cd app && pytest tests/ -v`. Review changed files for: `as any`, empty catches, unused imports.
  Output: `Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Health Check Verification** — `unspecified-high`
  Start Docker containers. Execute health check QA scenario. Capture full JSON output.
  Output: `Health [redis.available: true/false] | Startup [<30s/>30s] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  Verify 1:1 — only the 3 action items addressed. No scope creep. Check temp files don't exist.
  Output: `Tasks [N/N compliant] | Files [N deleted/N remaining] | VERDICT`

---

## Commit Strategy

| Task | Commit Message | Files | Pre-commit Check |
|------|----------------|-------|------------------|
| 1 | `chore: remove temporary files (100, 20, 50, =5.0.0, main-searchfix.css)` | Deleted files | None |
| 2 | `docs: add Ruff linting commands to AGENTS.md` | `AGENTS.md` | None |
| 3 | `fix(cache): use lazy async initialization for Redis connection` | `app/cache/__init__.py` | `pytest tests/ -v` |
| 4 | NO commit (verification) | — | — |

---

## Success Criteria

### Verification Commands
```bash
# Health check with Redis available
curl -s http://localhost:8000/health | jq '.redis.available'
# Expected: true

# Temp files deleted
ls /root/sgnl-backend/{100,20,50,=5.0.0} 2>&1
# Expected: "No such file or directory" for all

# Ruff documentation
grep -A 5 "### Linting" AGENTS.md
# Expected: Contains "ruff check app/" and "ruff format app/"

# All tests pass
cd app && pytest tests/ -v --tb=short
# Expected: 100% pass rate
```

### Final Checklist
- [ ] `redis.available: true` in health check
- [ ] No async warnings in logs
- [ ] 5 temp files deleted
- [ ] AGENTS.md has Ruff commands
- [ ] All tests pass
- [ ] No scope creep (only 3 action items addressed)