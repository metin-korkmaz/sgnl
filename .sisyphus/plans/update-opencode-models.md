# Update OpenCode Models: MiniMax-M2.5 → Kimi-K2.5

## TL;DR

> **Quick Summary**: Change 4 agent model references from MiniMax-M2.5 to kimi-k2.5 in oh-my-opencode.json
> 
> **Deliverables**: Updated `/root/.config/opencode/oh-my-opencode.json`
> 
> **Estimated Effort**: Quick (< 1 minute)
> **Parallel Execution**: NO - single file edit
> **Critical Path**: Single task

---

## Context

### Original Request
User wants to change model references from "minimax 2.5" to "kimi 2.5" in the opencode JSON config file and see all oh-my-opencode agents and models.

### Current State
- File: `/root/.config/opencode/oh-my-opencode.json`
- 4 agents using `bailian-coding-plan/MiniMax-M2.5`
- Target model `kimi-k2.5` already exists in the provider config

---

## Work Objectives

### Core Objective
Replace all `MiniMax-M2.5` model references with `kimi-k2.5` in oh-my-opencode.json

### Concrete Deliverables
- Updated `/root/.config/opencode/oh-my-opencode.json`

### Definition of Done
- [ ] All 4 occurrences of `MiniMax-M2.5` changed to `kimi-k2.5`
- [ ] JSON file is valid (no syntax errors)

---

## TODOs

- [x] 1. Update oh-my-opencode.json model references

  **What to do**:
  Edit `/root/.config/opencode/oh-my-opencode.json` and change all 4 occurrences:
  - Line 9: `sisyphus-junior` → `bailian-coding-plan/kimi-k2.5`
  - Line 12: `librarian` → `bailian-coding-plan/kimi-k2.5`
  - Line 15: `explore` → `bailian-coding-plan/kimi-k2.5`
  - Line 30: `hephaestus` → `bailian-coding-plan/kimi-k2.5`

  **Acceptance Criteria**:
  - [ ] `cat /root/.config/opencode/oh-my-opencode.json | grep MiniMax` returns empty
  - [ ] `cat /root/.config/opencode/oh-my-opencode.json | grep kimi-k2.5` shows 8 matches (4 original + 4 new)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: None
  - **Blocked By**: None

  **QA Scenarios**:
  ```
  Scenario: Verify JSON is valid
    Tool: Bash
    Steps:
      1. python3 -c "import json; json.load(open('/root/.config/opencode/oh-my-opencode.json'))"
    Expected Result: No error output (exit code 0)
    Evidence: .sisyphus/evidence/task-1-json-valid.txt

  Scenario: Verify MiniMax removed
    Tool: Bash
    Steps:
      1. grep -c "MiniMax" /root/.config/opencode/oh-my-opencode.json || true
    Expected Result: Output is 0
    Evidence: .sisyphus/evidence/task-1-minimax-removed.txt
  ```

  **Commit**: NO (config file outside project)

---

## Success Criteria

### Verification Commands
```bash
# Verify JSON validity
python3 -c "import json; json.load(open('/root/.config/opencode/oh-my-opencode.json'))" && echo "JSON OK"

# Verify MiniMax is gone
grep -c "MiniMax" /root/.config/opencode/oh-my-opencode.json || echo "MiniMax removed (count: 0)"

# Verify kimi-k2.5 count (should be 8: 4 existing + 4 new)
grep -c "kimi-k2.5" /root/.config/opencode/oh-my-opencode.json
```

### Final Checklist
- [x] All "Must Have" present
- [x] All "Must NOT Have" absent
- [x] JSON file is valid