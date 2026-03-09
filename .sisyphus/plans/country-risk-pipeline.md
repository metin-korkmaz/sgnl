# Multi-Agent Country Risk Analysis Pipeline

## TL;DR

> **Quick Summary**: Build a 5-step automated daily pipeline that analyzes political/economic risks for 10 countries using AI agents with web search, persistent memory, and email alerts.
>
> **Deliverables**:
> - Dockerized Python application with cron scheduling
> - LangGraph agent with Tavily web search and pgvector memory
> - PostgreSQL database with risk scores and semantic memory
> - SendGrid email alerts for critical findings
> - TDD test suite with pytest
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 5 waves
> **Critical Path**: Database → Agent Core → Pipeline Integration → End-to-End Test

---

## Context

### Original Request
Build an automated, daily "Multi-Agent Country Risk Analysis Pipeline" for a bank. The system acts as a digital risk department, analyzing political and economic risks for a portfolio of countries and generating structured reports.

### Interview Summary
**Key Discussions**:
- **Scale**: 10 countries for MVP (production: 160)
- **Agents**: 5 distinct agent roles (Orchestrator, Traffic, Chief Analyst, Archiver, Alert)
- **LLM**: Alibaba Cloud Model Studio (Qwen) via DashScope API
- **Memory**: pgvector for semantic memory per country session
- **Notifications**: SendGrid email with summary (no dashboard yet)
- **Testing**: TDD approach with pytest

**Research Findings**:
- **DashScope API**: OpenAI-compatible endpoint, use `langchain-qwq` package
- **LangGraph**: Modern agent pattern with `create_react_agent`
- **pgvector**: Requires `langchain-postgres` + `psycopg3`, HNSW index
- **Tavily**: Free tier 1,000 credits/month, advanced search = 2 credits
- **Google Sheets**: gspread with BackOffClient for retries

### Gap Analysis (Self-Identified)
**Questions Addressed**:
- Error handling: Exponential backoff for all external APIs
- Rate limiting: 5-second pacing between countries, Tavily 100 RPM
- Data retention: 90-day cleanup policy for old analyses
- Failure recovery: Log failed countries, continue pipeline, retry report

---

## Work Objectives

### Core Objective
Build a production-ready, Dockerized Python application that runs daily via cron, processes 10 countries through an AI-powered risk analysis agent, stores results in PostgreSQL with semantic memory, and alerts risk managers via email for critical findings.

### Concrete Deliverables
- `Dockerfile` and `docker-compose.yml` for containerized deployment
- `src/orchestrator.py` - Cron trigger and pipeline coordinator
- `src/agents/` - LangGraph agent implementations (traffic, analyst, archiver, alert)
- `src/tools/` - Tavily search tool wrapper
- `src/memory/` - pgvector integration for country session memory
- `src/models/` - Pydantic models for risk analysis JSON schema
- `src/database/` - PostgreSQL schema, migrations, and queries
- `src/sheets/` - Google Sheets client with gspread
- `src/email_client/` - SendGrid email sender
- `tests/` - TDD test suite with pytest
- `.env.example` - Environment variable template

### Definition of Done
- [ ] Docker container builds and runs successfully
- [ ] Pipeline processes all 10 countries from Google Sheets
- [ ] Chief Analyst agent searches web and outputs valid JSON
- [ ] Risk scores saved to PostgreSQL with embeddings
- [ ] Critical findings trigger SendGrid email
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Cron job configured and verified

### Must Have
- All 5 agents implemented and functional
- Tavily web search integrated with agent
- pgvector memory per country session
- Structured JSON output (Country, Risk_Score, Justification, Red_Flag)
- SendGrid email alerts for scores 1-2 or Red_Flag=true
- TDD with pytest, minimum 80% coverage on core modules
- Docker containerization with volume mounts
- Idempotent daily writes (unique constraint on `country + analysis_date`, upsert behavior)
- Overlap-safe scheduling (run lock prevents concurrent duplicate pipeline runs)
- Explicit retry/fallback policy for all external services (Tavily, DashScope, Sheets, SendGrid, DB)
- Explicit embedding provider selection with matching vector dimensions
- Structured scoring rubric (1–5 with defined criteria per level)

### Must NOT Have (Guardrails)
- NO web dashboard (out of scope)
- NO 160 countries (MVP is 10 only)
- NO real-time processing (batch daily only)
- NO authentication/authorization (internal tool)
- NO frontend/UI components
- NO legacy LangChain patterns (AgentExecutor, old chains)
- NO psycopg2 (use psycopg3 only)
- CI-enforced forbidden pattern checks: `grep -r "AgentExecutor\|psycopg2\|dashboard" src/` must return empty

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: NO (new project)
- **Automated tests**: YES - TDD
- **Framework**: pytest
- **Pattern**: RED (failing test) → GREEN (minimal impl) → REFACTOR for each task

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **CLI/Scripts**: Use Bash — Run command, validate output, check exit code
- **Database**: Use Bash (psql/curl) — Query tables, assert row counts and values
- **API/External**: Use Bash (curl) — Test endpoints, mock external services
- **Email**: Use Bash — Verify SendGrid API call structure
- **Reliability**: Verify retry/backoff and dead-letter persistence on final failure
- **Idempotency**: Re-run same date and assert no duplicate writes/alerts
- **Concurrency**: Trigger overlapping runs and assert lock/skip behavior

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation, ALL PARALLEL):
├── Task 1:  Project scaffolding + dependencies [quick]
├── Task 2:  Docker setup (Dockerfile, compose — 2 services: app + db) [quick]
├── Task 3:  Environment config + secrets management (full var list) [quick]
├── Task 4:  Pydantic models + scoring rubric [quick]
├── Task 5:  PostgreSQL schema + pgvector + pipeline_runs + failed_alerts [quick]
└── Task 6:  Google Sheets client (with input contract validation) [quick]

Wave 2 (After Wave 1 — core components, ALL PARALLEL):
├── Task 7:  pgvector memory module (namespace-based, embedding config) [deep]
├── Task 8:  Tavily search tool wrapper [quick]
├── Task 9a: Chief Analyst — LLM + prompt contract [quick]
├── Task 10: Database queries (upsert risk scores, query critical) [quick]
└── Task 11: SendGrid email client (retry + dead-letter) [quick]

Wave 2b (After Task 9a + 7 + 8 — agent assembly, SEQUENTIAL):
├── Task 9b: Chief Analyst — Tavily tool integration [quick]
├── Task 9c: Chief Analyst — memory integration [quick]
└── Task 9d: Chief Analyst — full assembly + error handling [deep]

Wave 3 (After Wave 2b — pipeline integration, ALL PARALLEL):
├── Task 12:  Traffic Agent (pacing/iteration) [quick]
├── Task 13:  Archiver Agent (JSON parse + upsert) [quick]
├── Task 14:  Alert Agent (query critical + email) [quick]
├── Task 15a: Pipeline run-state + run lock [quick]
└── Task 16:  Scheduler configuration (cron in app container) [quick]

Wave 3b (After Wave 3 — orchestrator, SEQUENTIAL):
├── Task 15b: Orchestration flow + partial-failure policy [deep]
└── Task 15c: CLI entrypoint [quick]

Wave 4 (After Wave 3b — testing, ALL PARALLEL):
├── Task 17: Unit tests — agents [deep]
├── Task 18: Unit tests — tools and clients [quick]
├── Task 19: Integration tests — full pipeline (mock LLM, real DB) [deep]
└── Task 20: Operational E2E QA (containers, cron, logs, DB, email) [deep]

Wave FINAL (After ALL tasks — verification):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality + forbidden pattern check (unspecified-high)
├── Task F3: Real pipeline run verification (unspecified-high)
└── Task F4: Scope fidelity check (deep)

Critical Path: Task 1 → Task 5 → Task 7 → Task 9a → Task 9d → Task 15b → Task 19 → F1-F4
Parallel Speedup: ~65% faster than sequential
Total Tasks: 24 implementation + 4 final = 28
```

### Dependency Matrix

| Task | Depends On | Unlocks |
|------|-----------|---------|
| 1–6 | — | Wave 2 |
| 7 | 3, 5 | 9c |
| 8 | 3 | 9b |
| 9a | 3, 4 | 9b, 9c |
| 9b | 8, 9a | 9c |
| 9c | 7, 9b | 9d |
| 9d | 9a, 9b, 9c | 13, 17 |
| 10 | 5 | 13, 14, 15a |
| 11 | 3, 5 | 14 |
| 12 | 6 | 15b |
| 13 | 4, 9d, 10 | 15b |
| 14 | 10, 11 | 15b |
| 15a | 5, 10 | 15b |
| 15b | 12, 13, 14, 15a | 15c, 19 |
| 15c | 15b | 19, 20 |
| 16 | 2, 3 | 20 |
| 17 | 9d, 12, 13, 14, 15b | 19 |
| 18 | 6, 7, 8, 10, 11 | 19 |
| 19 | 15b, 15c, 17, 18 | 20 |
| 20 | 15c, 16, 19 | F1–F4 |

---

## TODOs

### Wave 1: Foundation (6 tasks - PARALLEL)

- [x] **Task 1**: Project scaffolding + dependencies
  - **Category**: `quick`
  - **What**: Create Python project structure with pyproject.toml, install all dependencies
  - **Files**: `pyproject.toml`, `src/__init__.py`, `src/agents/__init__.py`, `src/tools/__init__.py`, `src/memory/__init__.py`, `src/models/__init__.py`, `src/database/__init__.py`, `src/sheets/__init__.py`, `src/email_client/__init__.py`
  - **Dependencies**: `langchain`, `langgraph`, `langchain-qwq`, `langchain-postgres`, `langchain-tavily`, `psycopg[binary]`, `gspread`, `sendgrid`, `pydantic`, `pytest`, `pytest-asyncio`, `pytest-cov`
  - **QA**: `pip install -e .` succeeds, `python -c "import src"` succeeds

- [x] **Task 2**: Docker setup (Dockerfile, compose)
  - **Category**: `quick`
  - **What**: Create Dockerfile for Python app and docker-compose.yml with app + PostgreSQL containers
  - **Files**: `Dockerfile`, `docker-compose.yml`
  - **Config**: Python 3.11-slim base, pgvector/pgvector:pg16 for DB, volume mounts for data
  - **QA**: `docker compose build` succeeds, `docker compose up -d` creates 2 running containers

- [x] **Task 3**: Environment config + secrets management
  - **Category**: `quick`
  - **What**: Create .env.example template with all required environment variables, implement config loader with pydantic-settings validation
  - **Files**: `.env.example`, `src/config.py`
  - **Variables**: `DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL` (default: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`), `DASHSCOPE_MODEL` (default: `qwen-plus`), `TAVILY_API_KEY`, `TAVILY_MAX_RESULTS` (default: 5), `TAVILY_SEARCH_DEPTH` (default: `advanced`), `TAVILY_TOPIC` (default: `news`), `GOOGLE_SHEETS_CREDENTIALS_PATH`, `SPREADSHEET_NAME`, `SPREADSHEET_WORKSHEET` (default: `Sheet1`), `DATABASE_URL`, `EMBEDDING_PROVIDER` (default: `openai`), `EMBEDDING_MODEL` (default: `text-embedding-3-small`), `EMBEDDING_API_KEY`, `VECTOR_DIM` (default: 1536), `SENDGRID_API_KEY`, `EMAIL_FROM`, `EMAIL_TO`, `PIPELINE_TIMEZONE` (default: `UTC`), `CRON_SCHEDULE` (default: `0 6 * * *`), `COUNTRY_PROCESS_DELAY_SECONDS` (default: 5), `MAX_RETRIES` (default: 3), `REQUEST_TIMEOUT_SECONDS` (default: 30), `RUN_LOCK_TIMEOUT_SECONDS` (default: 3600), `LOG_LEVEL` (default: `INFO`)
  - **QA**: `python -c "from src.config import settings; print(settings.DASHSCOPE_MODEL)"` works with .env

- [x] **Task 4**: Pydantic models for risk analysis
  - **Category**: `quick`
  - **What**: Define Pydantic v2 models for risk analysis JSON schema, country list, and database entities
  - **Files**: `src/models/risk.py`, `src/models/country.py`, `src/models/__init__.py`
  - **Models**: `RiskAnalysisResult(Country, Risk_Score, Justification, Red_Flag)`, `CountryList`, `RiskScoreDB`, `PipelineRun`, `SendResult`
  - **Scoring Rubric** (embed in model docstring and system prompt):
    - `1 = STOP`: Active default, capital controls, sovereign default, armed conflict, sanctions
    - `2 = HIGH RISK`: Political crisis, currency collapse >30%, IMF emergency, mass protests
    - `3 = ELEVATED`: Recession, political instability, elevated inflation >15%, credit downgrade
    - `4 = MODERATE`: Stable but watchlist — slowing growth, political transition, mild FX pressure
    - `5 = CLEAR`: Stable democracy, strong institutions, investment-grade, no active alerts
  - **QA**: `python -c "from src.models import RiskAnalysisResult; r = RiskAnalysisResult(Country='France', Risk_Score=3, Justification=['a'], Red_Flag=False)"` succeeds

- [x] **Task 5**: PostgreSQL schema + pgvector setup
  - **Category**: `quick`
  - **What**: Create SQL schema with all tables, pgvector extension, HNSW index, and unique constraints
  - **Files**: `src/database/schema.sql`, `src/database/__init__.py`, `src/database/init_db.py`
  - **Tables**:
    - `pipeline_runs(id UUID PK, run_id TEXT UNIQUE, started_at TIMESTAMP, finished_at TIMESTAMP, status TEXT, countries_processed INT, countries_failed INT)`
    - `risk_scores(id UUID PK, run_id TEXT FK, country TEXT, risk_score INT, justification JSONB, red_flag BOOL, analysis_date DATE, created_at TIMESTAMP, UNIQUE(country, analysis_date))`
    - `failed_alerts(id UUID PK, run_id TEXT, payload JSONB, error TEXT, created_at TIMESTAMP, retried_at TIMESTAMP)`
    - `semantic_memory` — use `langchain-postgres` managed schema via `PGVector.create_tables_if_not_exists()`
  - **Constraints**: `UNIQUE(country, analysis_date)` on risk_scores; HNSW index on embedding column
  - **QA**: `docker exec country-risk-db psql -U postgres -d risk_analysis -c "SELECT * FROM risk_scores LIMIT 1;"` works after init

- [x] **Task 6**: Google Sheets client
  - **Category**: `quick`
  - **What**: Implement Google Sheets reader using gspread with service account auth and BackOffClient retry
  - **Files**: `src/sheets/client.py`
  - **Methods**: `get_country_list(spreadsheet_name: str, worksheet: str) -> List[str]`
  - **Input Contract**: Required header column named `country` (case-insensitive); trim whitespace; deduplicate; skip blank rows; raise `ValueError` if header missing
  - **Error Handling**: Exponential backoff via `BackOffClient`; raise after `MAX_RETRIES` exhausted
  - **QA**: `python -c "from src.sheets import get_country_list; print(get_country_list('Test', 'Sheet1'))"` returns list

### Wave 2: Core Components (5 tasks - depends on Wave 1)

- [x] **Task 7**: pgvector memory module
  - **Category**: `deep`
  - **What**: Implement LangChain PGVector store integration for semantic memory with namespace-based retrieval
  - **Files**: `src/memory/vector_store.py`, `src/memory/__init__.py`
  - **Dependencies**: Requires Task 3 (config — embedding provider/model/key/dim), Task 5 (database)
  - **Embedding**: Use `EMBEDDING_PROVIDER`/`EMBEDDING_MODEL`/`EMBEDDING_API_KEY` from config; default OpenAI `text-embedding-3-small` (1536d)
  - **Namespace**: Filter by `metadata={"country": country_name}` — do NOT rely on country name alone in content
  - **Methods**: `save_memory(country: str, content: str, metadata: dict)`, `get_memories(country: str, query: str, k: int = 5) -> List[str]`
  - **Schema**: Use `langchain-postgres` managed schema (`PGVector.create_tables_if_not_exists()`)
  - **QA**: Save 3 memories for "France", query with semantic phrase, verify top-k returns France-namespaced results only

- [x] **Task 8**: Tavily search tool wrapper
  - **Category**: `quick`
  - **What**: Create LangChain-compatible Tavily search tool with country + risk keywords, advanced search depth
  - **Files**: `src/tools/tavily_search.py`
  - **Dependencies**: Requires Task 3 (config)
  - **Methods**: `search_country_risk(country: str) -> str` - returns formatted search results
  - **Config**: max_results=5, search_depth="advanced", topic="news"
  - **QA**: `python -c "from src.tools import search_country_risk; print(search_country_risk('France'))"` returns results

- [x] **Task 9a**: Chief Analyst — LLM client + prompt contract
  - **Category**: `quick`
  - **What**: Wire `ChatQwQ` (DashScope) with system prompt embedding the scoring rubric (1–5 criteria), JSON output mode
  - **Files**: `src/agents/chief_analyst_llm.py`
  - **Dependencies**: Requires Task 3 (config), Task 4 (models with rubric)
  - **Prompt**: Senior Credit Risk Analyst persona; must cite specific evidence per justification point; must output ONLY valid JSON matching `RiskAnalysisResult` schema
  - **Output Validation**: Parse → Pydantic validate → if invalid, repair-prompt once → if still invalid, raise `AnalysisError`
  - **QA**: Mock LLM response, verify Pydantic parse succeeds; mock malformed response, verify repair-prompt triggered

- [ ] **Task 9b**: Chief Analyst — Tavily tool integration
  - **Category**: `quick`
  - **What**: Bind Tavily search tool to LangGraph agent; verify tool-call round-trip with Qwen model
  - **Files**: `src/agents/chief_analyst_tools.py`
  - **Dependencies**: Requires Task 8 (Tavily wrapper), Task 9a (LLM client)
  - **QA**: Agent invokes Tavily for a country, receives search results, incorporates into analysis

- [ ] **Task 9c**: Chief Analyst — memory integration (PGVector read/write)
  - **Category**: `quick`
  - **What**: Before analysis, retrieve past memories for country; after analysis, save new assessment to memory
  - **Files**: `src/agents/chief_analyst_memory.py`
  - **Dependencies**: Requires Task 7 (vector store), Task 9b
  - **QA**: Run agent twice for same country; second run retrieves first run's memory

- [ ] **Task 9d**: Chief Analyst — full agent assembly + error handling
  - **Category**: `deep`
  - **What**: Assemble complete LangGraph ReAct agent from 9a/9b/9c; add bounded retries (max 3), timeout, and structured error output
  - **Files**: `src/agents/chief_analyst.py` (main entry point)
  - **Dependencies**: Requires Task 9a, 9b, 9c
  - **Error Policy**: On `AnalysisError` after retries → return `RiskAnalysisResult(Risk_Score=0, Red_Flag=True, Justification=["Analysis failed: {reason}"])`
  - **QA**: Full agent run for one country returns valid `RiskAnalysisResult`; simulate LLM timeout, verify graceful failure output

- [x] **Task 10**: Database queries (save/query risk scores)
  - **Category**: `quick`
  - **What**: Implement async database operations for saving and querying risk scores with psycopg3
  - **Files**: `src/database/queries.py`
  - **Dependencies**: Requires Task 5 (schema)
  - **Methods**: `save_risk_score(result: RiskAnalysisResult)`, `get_critical_scores(date: date) -> List[RiskAnalysisResult]`, `get_country_history(country: str) -> List[RiskAnalysisResult]`
  - **QA**: Save a score, query it back, verify data integrity

- [x] **Task 11**: SendGrid email client
  - **Category**: `quick`
  - **What**: Implement SendGrid email sender for risk alerts with HTML formatting, retry, and dead-letter persistence
  - **Files**: `src/email_client/sender.py`
  - **Dependencies**: Requires Task 3 (config), Task 5 (schema — `failed_alerts` table)
  - **Methods**: `send_risk_alert(critical_results: List[RiskAnalysisResult], run_id: str) -> SendResult`
  - **Template**: Executive summary with country table (Country | Score | Red Flag | Top Justification)
  - **Failure Policy**: Retry up to `MAX_RETRIES` with exponential backoff + jitter; on final failure, persist payload to `failed_alerts` table and return `SendResult(success=False, error=...)`
  - **Deduplication**: Check `failed_alerts` for same `run_id` before retrying to avoid double-send
  - **QA**: Mock SendGrid failure, verify retry attempts, verify `failed_alerts` row inserted on exhaustion

### Wave 3: Pipeline Integration (5 tasks - depends on Wave 2)

- [ ] **Task 12**: Traffic Agent (pacing/iteration)
  - **Category**: `quick`
  - **What**: Implement iteration logic with 5-second pacing between countries
  - **Files**: `src/agents/traffic.py`
  - **Dependencies**: Requires Task 6 (sheets client)
  - **Methods**: `iterate_countries(countries: List[str], process_fn: Callable) -> List[Result]`
  - **Features**: Rate limiting, progress logging, error handling per country
  - **QA**: Process 3 test countries, verify 5-second delays

- [ ] **Task 13**: Archiver Agent (JSON parsing + save)
  - **Category**: `quick`
  - **What**: Parse agent JSON output, validate schema, save to database with timestamp
  - **Files**: `src/agents/archiver.py`
  - **Dependencies**: Requires Task 4 (models), Task 9 (analyst), Task 10 (queries)
  - **Methods**: `archive_result(agent_output: str) -> RiskAnalysisResult`
  - **Validation**: Pydantic validation, JSON parse errors handling
  - **QA**: Parse mock agent output, save to DB, query back

- [ ] **Task 14**: Alert Agent (query critical + format email)
  - **Category**: `quick`
  - **What**: Query database for critical scores (1-2 or Red_Flag=true), format executive summary
  - **Files**: `src/agents/alert.py`
  - **Dependencies**: Requires Task 10 (queries), Task 11 (email)
  - **Methods**: `check_and_alert(date: date) -> bool`
  - **Logic**: Query critical scores, if any exist, send email alert
  - **QA**: Insert critical score, run alert agent, verify email sent

- [ ] **Task 15a**: Pipeline run-state model + run lock
  - **Category**: `quick`
  - **What**: Implement `pipeline_runs` DB record lifecycle (start/finish/fail) and advisory lock to prevent concurrent runs
  - **Files**: `src/orchestrator_state.py`
  - **Dependencies**: Requires Task 5 (schema — `pipeline_runs` table), Task 10 (queries)
  - **Lock**: PostgreSQL advisory lock (`pg_try_advisory_lock`) keyed on fixed integer; if lock fails, log "pipeline already running" and exit 0
  - **Run ID**: UUID generated per run, propagated to all `risk_scores` and `failed_alerts` rows
  - **QA**: Start two pipeline processes simultaneously; verify second exits immediately with lock message

- [ ] **Task 15b**: Orchestration flow + partial-failure policy
  - **Category**: `deep`
  - **What**: Main pipeline flow: acquire lock → load countries → iterate (Traffic) → analyze (Analyst) → archive (Archiver) → alert (Alert) → release lock
  - **Files**: `src/orchestrator.py`
  - **Dependencies**: Requires Task 12, 13, 14, 15a
  - **Failure Policy**: Per-country failure → log error, mark country as failed in run record, continue to next country (never abort full pipeline for one country)
  - **Exit Codes**: 0 = success (even partial), 1 = lock contention, 2 = unrecoverable startup error
  - **Logging**: Structured JSON logs with `run_id`, `country`, `step`, `status`, `duration_ms`
  - **QA**: Run with 3 countries where 1 mock-fails; verify 2 succeed, 1 logged as failed, pipeline completes

- [ ] **Task 15c**: CLI entrypoint
  - **Category**: `quick`
  - **What**: CLI with `--run-now` flag and `--dry-run` flag (loads countries, skips analysis, prints list)
  - **Files**: `src/__main__.py`
  - **Dependencies**: Requires Task 15b
  - **QA**: `python -m src --run-now` triggers pipeline; `python -m src --dry-run` prints country list without API calls

- [ ] **Task 16**: Scheduler configuration (single-owner model)
  - **Category**: `quick`
  - **What**: Configure cron inside the app container (NOT a separate container); cron reads `CRON_SCHEDULE` and `PIPELINE_TIMEZONE` from env
  - **Files**: `cron/entrypoint.sh`, `cron/crontab.template`, updated `Dockerfile`
  - **Architecture Decision**: Cron runs inside the single app container; `docker-compose.yml` has only 2 services: `app` + `db`
  - **Schedule**: Driven by `CRON_SCHEDULE` env var (default `0 6 * * *`); timezone set via `PIPELINE_TIMEZONE`
  - **Concurrency Guard**: Cron calls `python -m src --run-now`; run lock in Task 15a prevents overlap
  - **Log Rotation**: `logrotate` config for `/var/log/pipeline.log`
  - **QA**: `docker exec country-risk-pipeline crontab -l` shows correct schedule; verify timezone applied

### Wave 4: Testing (4 tasks - depends on Wave 3b)

- [ ] **Task 17**: Unit tests — agents
  - **Category**: `deep`
  - **What**: Comprehensive unit tests for all agent modules with mocks (TDD: write tests first, then verify they pass against implementation)
  - **Files**: `tests/test_chief_analyst.py`, `tests/test_traffic.py`, `tests/test_archiver.py`, `tests/test_alert.py`, `tests/test_orchestrator.py`
  - **Coverage**: Mock LLM (malformed output + valid output), mock Tavily, mock DB, test retry logic, test partial-failure policy, test run lock
  - **QA**: `pytest tests/test_chief_analyst.py tests/test_traffic.py tests/test_archiver.py tests/test_alert.py tests/test_orchestrator.py -v` all pass

- [ ] **Task 18**: Unit tests — tools and clients
  - **Category**: `quick`
  - **What**: Unit tests for Tavily wrapper, Google Sheets client (including bad header), SendGrid client (retry + dead-letter), database queries (upsert idempotency)
  - **Files**: `tests/test_tavily_search.py`, `tests/test_sheets_client.py`, `tests/test_email_sender.py`, `tests/test_queries.py`, `tests/test_vector_store.py`
  - **Coverage**: Mock external APIs, test retry/backoff, test error handling, test idempotency (upsert same row twice = 1 row)
  - **QA**: `pytest tests/test_tavily_search.py tests/test_sheets_client.py tests/test_email_sender.py tests/test_queries.py tests/test_vector_store.py -v` all pass

- [ ] **Task 19**: Integration tests — full pipeline (mock LLM, real DB)
  - **Category**: `deep`
  - **What**: End-to-end integration test with mock LLM responses, real PostgreSQL (Docker), mock email
  - **Files**: `tests/test_integration.py`, `tests/fixtures/mock_data.py`, `tests/conftest.py`
  - **Scope**: Mock Google Sheets (3 countries), mock LLM (valid + 1 malformed), real DB, mock SendGrid
  - **Scenarios**: (1) Normal run — 3 countries processed, DB populated; (2) Idempotency — re-run same date, no duplicates; (3) Partial failure — 1 country fails, 2 succeed, pipeline completes
  - **QA**: `pytest tests/test_integration.py -v` passes all 3 scenarios

- [ ] **Task 20**: Operational E2E QA (containers, cron, logs, DB, email)
  - **Category**: `deep`
  - **What**: Full operational verification: build container, start services, run pipeline manually, verify all outputs
  - **Files**: `.sisyphus/evidence/task-20-e2e-qa.log`
  - **Steps**: 1) `docker compose build` — exit 0; 2) `docker compose up -d` — 2 containers running; 3) `docker exec country-risk-pipeline python -m src --dry-run` — prints 10 countries; 4) `docker exec country-risk-pipeline python -m src --run-now` — pipeline completes; 5) Query DB — `risk_scores` has rows; 6) Check `failed_alerts` — empty (no failures); 7) Verify cron schedule set; 8) Check logs for structured JSON format
  - **QA**: All 8 steps pass; evidence saved to `.sisyphus/evidence/task-20-e2e-qa.log`

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `pytest tests/ -v --cov=src --cov-report=term-missing`. Review all files for: `as any`, `# type: ignore`, empty catches, unused imports. Check for legacy patterns (AgentExecutor). Verify error handling has exponential backoff.
  Output: `Tests [N pass/N fail] | Coverage [X%] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Pipeline Run Verification** — `unspecified-high`
  Run pipeline with test Google Sheet (10 countries). Verify: all countries processed, JSON outputs valid, database records created, embeddings stored, email sent for critical scores. Check logs for errors.
  Output: `Countries [10/10] | JSON valid [Y/N] | DB records [N] | Email sent [Y/N] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", check actual implementation. Verify 1:1 — everything in spec was built, nothing beyond spec. Check "Must NOT do" compliance. Detect unaccounted files.
  Output: `Tasks [N/N compliant] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1**: `feat(core): project scaffolding and configuration` — pyproject.toml, Dockerfile, .env.example
- **Wave 2**: `feat(agents): chief analyst agent with tools` — src/agents/, src/tools/, src/memory/
- **Wave 3**: `feat(pipeline): orchestrator and integration` — src/orchestrator.py, src/email_client/
- **Wave 4**: `test: comprehensive test suite` — tests/

---

## Success Criteria

### Verification Commands
```bash
# Build and run container
docker compose up -d --build
docker compose logs -f country-risk-pipeline

# Run tests
pytest tests/ -v --cov=src --cov-report=term-missing

# Verify database
docker exec -it country-risk-db psql -U postgres -d risk_analysis -c "SELECT COUNT(*) FROM risk_scores;"

# Manual pipeline run
docker exec -it country-risk-pipeline python -m src.orchestrator --run-now

# Check cron job
docker exec -it country-risk-pipeline crontab -l
```

### Final Checklist
- [ ] Docker container builds without errors
- [ ] All 10 countries processed successfully
- [ ] JSON output matches schema (Country, Risk_Score, Justification, Red_Flag)
- [ ] PostgreSQL contains risk_scores and semantic_memory tables
- [ ] pgvector embeddings searchable for past analyses
- [ ] Email sent for any score 1-2 or Red_Flag=true
- [ ] Tests pass with ≥80% coverage on core modules
- [ ] Cron job scheduled and verified
- [ ] No forbidden patterns (AgentExecutor, psycopg2, dashboard code)