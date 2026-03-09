# SGNL UI Design Improvements Work Plan

## TL;DR

> **Objective**: Implement high-impact UI improvements including dark mode, skeleton loaders, enhanced mobile experience, and modern design patterns.
>
> **Deliverables**:
> - Dark mode toggle with theme persistence
> - Skeleton loading states for better UX
> - Enhanced mobile touch targets and navigation
> - Secondary accent colors for signal levels
> - Bento grid layout for results
> - Keyboard shortcuts for power users
>
> **Estimated Effort**: Quick (~2-4 hours)
> **Parallel Execution**: YES - 3 waves with 2-3 tasks each
> **Critical Path**: CSS updates → HTML structure → JavaScript functionality

---

## Context

### Original Request
User requested implementation of high-impact UI design improvements after research into 2025 design trends and analysis of current brutalist design.

### Interview Summary
**Key Discussions**:
- Current design uses brutalist aesthetic (strong identity)
- High-impact improvements needed: dark mode, skeleton loaders, mobile optimization
- User wants to maintain brutalist identity while modernizing

**Research Findings**:
- 2025 trends: Bento grids, skeleton loaders, dark mode expectations
- Brutalist evolution: "Soft brutalism" with secondary accent colors
- Power user features: keyboard shortcuts are expected
- Mobile: Touch targets need to be 48px minimum (WCAG)

### Current Design Analysis
**Strengths:**
- Strong brutalist identity
- Bold typography hierarchy
- Visible grid system (Swiss-style)
- High contrast color palette

**Improvement Areas:**
- No dark mode option
- Basic loading states
- Mobile touch targets too small
- Missing visual feedback for signal levels

---

## Work Objectives

### Core Objective
Implement high-impact, low-effort UI improvements that enhance user experience while maintaining the brutalist design identity.

### Concrete Deliverables
- Dark mode with localStorage persistence
- Skeleton loading animations
- 48px minimum touch targets on mobile
- Signal level color coding (green/yellow/red)
- Keyboard shortcut system (⌘K for search)
- Bento grid layout for results

### Definition of Done
- [ ] Dark mode toggle works and persists across sessions
- [ ] Skeleton loaders show during search/analysis
- [ ] All touch targets meet 48px minimum on mobile
- [ ] Signal scores have color-coded feedback
- [ ] Keyboard shortcuts work and show hints
- [ ] No breaking changes to existing functionality

### Must Have
1. Dark mode with toggle in navigation
2. Skeleton loaders for results section
3. Mobile touch target improvements
4. Signal level color coding

### Must NOT Have (Guardrails)
- Do not change existing brutalist color palette
- Do not remove any existing functionality
- Do not break mobile responsiveness
- Do not add dependencies
- Do not change the core design philosophy

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (existing test setup)
- **Automated tests**: NO (visual changes, manual QA sufficient)
- **Framework**: Manual browser testing
- **Agent-Executed QA**: YES - Playwright for UI verification

### QA Policy
Every task includes visual verification via browser testing.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (CSS Foundation - Start Immediately):
├── Task 1: Add dark mode CSS variables and theme styles [quick]
├── Task 2: Add skeleton loader animations [quick]
└── Task 3: Add signal level color classes [quick]

Wave 2 (HTML Structure):
├── Task 4: Add dark mode toggle to navigation [quick]
├── Task 5: Add skeleton loader templates [quick]
└── Task 6: Add keyboard shortcut hints [quick]

Wave 3 (JavaScript Functionality):
├── Task 7: Implement dark mode toggle with localStorage [quick]
├── Task 8: Add skeleton loader display logic [quick]
└── Task 9: Implement keyboard shortcuts [quick]

Wave FINAL (Verification):
├── Task F1: Visual QA - desktop and mobile [unspecified-high]
├── Task F2: Dark mode persistence test [quick]
└── Task F3: Accessibility verification [unspecified-high]
```

---

## TODOs

### Wave 1: CSS Foundation

- [x] **1. Add Dark Mode CSS Variables and Theme Styles**

  **What to do**:
  - Add dark mode CSS variables to `:root` in `main.css`
  - Create `[data-theme="dark"]` selector with inverted colors
  - Ensure all existing components work in dark mode
  - Test contrast ratios meet WCAG AA standards

  **Must NOT do**:
  - Do not change existing color values in light mode
  - Do not add new dependencies

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: CSS styling and theme implementation

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 2-3
  - **Blocks**: Task 4 (HTML needs CSS ready)
  - **Blocked By**: None

  **References**:
  - `app/static/css/main.css:9-32` - Current CSS variables
  - Current color palette: `--bg-color: #F2F0E9`, `--ink-color: #050505`, `--alert-color: #FF4400`
  - Dark mode should invert: `--bg-color: #0A0A0A`, `--ink-color: #F2F0E9`

  **Acceptance Criteria**:
  - [ ] Dark mode CSS variables defined
  - [ ] All components visible in dark mode
  - [ ] Contrast ratios meet WCAG AA (4.5:1 for text)

  **QA Scenarios**:
  ```
  Scenario: Dark mode applies correctly
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:8000
      2. Click dark mode toggle
      3. Verify background changes to dark
      4. Verify text is visible with high contrast
    Expected: Dark theme applied, all text readable
    Evidence: .sisyphus/evidence/task-1-dark-mode.png
  ```

  **Commit**: YES
  - Message: `feat(ui): add dark mode CSS variables and theme support`
  - Files: `app/static/css/main.css`

- [x] **2. Add Skeleton Loader Animations**

  **What to do**:
  - Add skeleton loader CSS classes to `main.css`
  - Create shimmer animation using CSS gradients
  - Support both light and dark mode
  - Add skeleton variants: title, text, image, card

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 1, 3
  - **Blocks**: Task 5 (HTML needs skeleton classes)
  - **Blocked By**: None

  **References**:
  - `app/static/css/main.css` - Add after existing styles
  - Animation pattern: `background: linear-gradient(90deg, ...)`

  **Acceptance Criteria**:
  - [ ] Skeleton classes defined (.skeleton, .skeleton-title, etc.)
  - [ ] Shimmer animation works smoothly
  - [ ] Works in both light and dark mode

  **QA Scenarios**:
  ```
  Scenario: Skeleton loader displays correctly
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:8000
      2. Trigger search
      3. Verify skeleton loaders appear
      4. Verify shimmer animation runs
    Expected: Skeleton loaders visible with smooth animation
    Evidence: .sisyphus/evidence/task-2-skeleton.png
  ```

  **Commit**: YES
  - Message: `feat(ui): add skeleton loader animations`
  - Files: `app/static/css/main.css`

- [x] **3. Add Signal Level Color Classes**

  **What to do**:
  - Add CSS classes for signal levels: `.signal-high`, `.signal-medium`, `.signal-low`
  - Use secondary accent colors:
    - High: `#00FF94` (green)
    - Medium: `#FFD600` (yellow)
    - Low: `#FF4400` (existing alert color)
  - Apply to signal bars, text, badges

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 1-2
  - **Blocks**: None (CSS-only change)
  - **Blocked By**: None

  **References**:
  - `app/static/css/main.css` - Add after existing color variables
  - `app/static/js/main.js:989` - Signal score calculation

  **Acceptance Criteria**:
  - [ ] Signal level classes defined
  - [ ] Colors visible and distinct
  - [ ] Applied to existing signal elements

  **Commit**: YES
  - Message: `feat(ui): add signal level color coding`
  - Files: `app/static/css/main.css`

### Wave 2: HTML Structure

- [x] **4. Add Dark Mode Toggle to Navigation**

  **What to do**:
  - Add theme toggle button to `index.html` navigation
  - Position before mobile GitHub link
  - Use simple icon: ◐ or ☾
  - Add appropriate aria-label for accessibility

  **Must NOT do**:
  - Do not break existing navigation layout
  - Do not remove existing nav items

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO - depends on Task 1
  - **Blocks**: Task 7 (JS needs toggle element)
  - **Blocked By**: Task 1 (CSS must be ready)

  **References**:
  - `app/templates/index.html:59-75` - Navigation section
  - Position: After `.nav-links`, before `.mobile-github-link`

  **Acceptance Criteria**:
  - [x] Toggle button added to nav
  - [x] Visible on both desktop and mobile
  - [x] Accessible via keyboard

  **Commit**: YES
  - Message: `feat(ui): add dark mode toggle button to navigation`
  - Files: `app/templates/index.html`

- [x] **5. Add Skeleton Loader Templates**

  **What to do**:
  - Add skeleton card templates to `index.html`
  - Create hidden template that JS can clone
  - Include variants: result card, intelligence report

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 4, 6
  - **Blocks**: Task 8 (JS needs templates)
  - **Blocked By**: Task 2 (CSS must be ready)

  **References**:
  - `app/templates/index.html:124-191` - Results section
  - Add templates after results section

  **Acceptance Criteria**:
  - [ ] Skeleton templates defined
  - [ ] Hidden by default
  - [ ] Ready for JS cloning

  **Commit**: YES
  - Message: `feat(ui): add skeleton loader HTML templates`
  - Files: `app/templates/index.html`

- [x] **6. Add Keyboard Shortcut Hints**

  **What to do**:
  - Add keyboard shortcut hints to search section
  - Display: `⌘K` or `Ctrl+K` for quick search
  - Add to footer or bottom of search box
  - Use `<kbd>` HTML element for styling

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 4-5
  - **Blocks**: None (visual only)
  - **Blocked By**: None

  **References**:
  - `app/templates/index.html:105-122` - Search section
  - Add hint below or beside search input

  **Acceptance Criteria**:
  - [ ] Keyboard hint visible
  - [ ] Styled with <kbd> element
  - [ ] Non-intrusive design

  **Commit**: YES
  - Message: `feat(ui): add keyboard shortcut hints`
  - Files: `app/templates/index.html`

### Wave 3: JavaScript Functionality

- [x] **7. Implement Dark Mode Toggle with localStorage**

  **What to do**:
  - Add JavaScript to toggle dark mode
  - Store preference in localStorage
  - Apply saved theme on page load
  - Update button text/icon on toggle

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 8-9
  - **Blocks**: Task F2 (persistence test)
  - **Blocked By**: Tasks 1, 4 (CSS and HTML must be ready)

  **References**:
  - `app/static/js/main.js` - Add after existing event listeners
  - localStorage key: `sgnl-theme`
  - Pattern: `document.documentElement.setAttribute('data-theme', 'dark')`

  **Acceptance Criteria**:
  - [ ] Toggle switches theme
  - [ ] Preference saved to localStorage
  - [ ] Theme persists across page reloads
  - [ ] Default to light mode if no preference

  **QA Scenarios**:
  ```
  Scenario: Dark mode persists across reload
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:8000
      2. Click dark mode toggle
      3. Verify dark mode active
      4. Reload page
      5. Verify dark mode still active
    Expected: Theme preference persisted
    Evidence: .sisyphus/evidence/task-7-persistence.png
  ```

  **Commit**: YES
  - Message: `feat(ui): implement dark mode toggle with persistence`
  - Files: `app/static/js/main.js`

- [x] **8. Add Skeleton Loader Display Logic**

  **What to do**:
  - Show skeleton loaders when search starts
  - Hide when results arrive
  - Use existing skeleton templates
  - Add GSAP fade-in animation for results

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 7, 9
  - **Blocks**: None
  - **Blocked By**: Tasks 2, 5 (CSS and HTML must be ready)

  **References**:
  - `app/static/js/main.js:334-492` - Search handling function
  - Show skeletons after line 346 (when state.isLoading = true)
  - Hide when results render

  **Acceptance Criteria**:
  - [ ] Skeletons appear during search
  - [ ] Smooth transition to results
  - [ ] No layout shift

  **Commit**: YES
  - Message: `feat(ui): add skeleton loader display logic`
  - Files: `app/static/js/main.js`

- [x] **9. Implement Keyboard Shortcuts**

  **What to do**:
  - Add ⌘K / Ctrl+K shortcut to focus search
  - Add Escape to clear results
  - Add keyboard event listener
  - Prevent default browser behavior

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 7-8
  - **Blocks**: None
  - **Blocked By**: Task 6 (hints must be added)

  **References**:
  - `app/static/js/main.js` - Add after DOMContentLoaded
  - Pattern: `document.addEventListener('keydown', (e) => { ... })`

  **Acceptance Criteria**:
  - [ ] ⌘K / Ctrl+K focuses search input
  - [ ] Escape clears results
  - [ ] Works on both Mac and Windows/Linux

  **Commit**: YES
  - Message: `feat(ui): implement keyboard shortcuts`
  - Files: `app/static/js/main.js`

### Wave FINAL: Verification

- [x] **F1. Visual QA - Desktop and Mobile**

  **What to do**:
  - Test all UI improvements on desktop
  - Test all UI improvements on mobile viewport
  - Take screenshots for evidence
  - Verify no breaking changes

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`playwright`]

  **Output Format**:
  ```
  Desktop [PASS/FAIL] | Mobile [PASS/FAIL] | Screenshots [N/N] | VERDICT
  ```

- [x] **F2. Dark Mode Persistence Test**

  **What to do**:
  - Toggle dark mode
  - Reload page multiple times
  - Verify preference persists
  - Test across different browsers if possible

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`playwright`]

  **Output Format**:
  ```
  Toggle [PASS] | Reload [PASS] | Persistence [PASS] | VERDICT
  ```

- [x] **F3. Accessibility Verification**

  **What to do**:
  - Test keyboard navigation
  - Verify all touch targets meet 48px minimum
  - Check color contrast ratios
  - Test screen reader compatibility if possible

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`playwright`]

  **Output Format**:
  ```
  Keyboard [PASS] | Touch Targets [PASS] | Contrast [PASS] | VERDICT
  ```

---

## Final Verification Wave

### Verification Commands

```bash
# Start development server
docker compose -f docker-compose.dev.yml up --build

# Navigate to http://localhost:8000
# Test dark mode toggle
# Test keyboard shortcuts (⌘K / Ctrl+K)
# Test mobile responsiveness (resize browser)
# Test skeleton loaders (trigger search)
```

### Final Checklist

- [ ] Dark mode toggle works and persists
- [ ] Skeleton loaders display during search
- [ ] All touch targets ≥ 48px on mobile
- [ ] Signal levels color-coded
- [ ] Keyboard shortcuts functional
- [ ] No visual regressions
- [ ] Mobile layout intact

---

## Commit Strategy

### Wave 1 (CSS)
```
feat(ui): add dark mode CSS variables and theme support
feat(ui): add skeleton loader animations
feat(ui): add signal level color coding
```

### Wave 2 (HTML)
```
feat(ui): add dark mode toggle button to navigation
feat(ui): add skeleton loader HTML templates
feat(ui): add keyboard shortcut hints
```

### Wave 3 (JavaScript)
```
feat(ui): implement dark mode toggle with persistence
feat(ui): add skeleton loader display logic
feat(ui): implement keyboard shortcuts
```

---

## Success Criteria

### Verification Commands
```bash
# All must pass
# Visual inspection in browser
# Dark mode toggle visible and working
# Skeleton loaders appear during search
# Keyboard shortcuts responsive
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] No visual regressions
- [ ] Mobile experience improved
- [ ] User feedback positive