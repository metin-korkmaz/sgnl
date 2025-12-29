/**
 * SGNL Heavy Brutalist UI v4
 * ===========================
 * Industrial machinery. Clicks, clacks, scrambles.
 * 
 * Dependencies:
 * - GSAP (loaded via CDN)
 */

'use strict';

/* ========== CONFIGURATION ========== */
const CONFIG = {
    apiEndpoint: '/scan-topic',
    maxResults: 5,
    // Rotator slogans
    rotatorSlogans: [
        'FILTERS SEO SLOP',
        'DEEP RESEARCH ONLY',
        'NO AFFILIATE LINKS',
        'PURE SIGNAL',
        'ENGINEER GRADE'
    ],
    rotatorInterval: 4000, // 4 seconds
    // Scramble effect
    scrambleChars: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*',
    scrambleSpeed: 30,
    scrambleIterations: 8,
    // Status messages
    statusTexts: [
        'INITIALIZING...',
        'SCANNING NETWORK...',
        'FILTERING SLOP...',
        'EXTRACTING SIGNAL...',
        'ANALYZING DEPTH...',
        'COMPILING RESULTS...'
    ],
    statusCycleDelay: 600
};

/* ========== STATE ========== */
const state = {
    isLoading: false,
    currentStatusIndex: 0,
    statusInterval: null,
    // Rotator state
    currentRotatorIndex: 0,
    rotatorTimer: null,
    isScrambling: false
};

/* ========== DOM REFERENCES ========== */
const DOM = {
    searchInput: null,
    searchBtn: null,
    resultsSection: null,
    resultsHeader: null,
    resultsCount: null,
    resultsBody: null,
    garbageText: null,
    statusDisplay: null,
    ctaButtons: null,
    // Rotator
    rotatorText: null,
    rotatorPrev: null,
    rotatorNext: null,
    heroSection: null
};

/* ========== UTILITY FUNCTIONS ========== */

function extractDomain(url) {
    try {
        return new URL(url).hostname.replace('www.', '').toUpperCase();
    } catch {
        return 'UNKNOWN';
    }
}

function createElement(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => {
        if (key === 'className') {
            el.className = value;
        } else if (key === 'textContent') {
            el.textContent = value;
        } else if (key.startsWith('data')) {
            el.setAttribute(key.replace(/([A-Z])/g, '-$1').toLowerCase(), value);
        } else if (key === 'style') {
            el.setAttribute('style', value);
        } else {
            el.setAttribute(key, value);
        }
    });
    children.forEach(child => {
        if (typeof child === 'string') {
            el.appendChild(document.createTextNode(child));
        } else if (child instanceof Node) {
            el.appendChild(child);
        }
    });
    return el;
}

function escapeHTML(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/* ========== TEXT SCRAMBLE/DECRYPT EFFECT ========== */

/**
 * Scramble text to target with decrypt effect
 * @param {HTMLElement} element - Target element
 * @param {string} targetText - Final text to reveal
 * @param {Function} onComplete - Callback when done
 */
function scrambleToText(element, targetText, onComplete) {
    if (state.isScrambling) return;
    state.isScrambling = true;

    const originalText = element.textContent;
    const chars = CONFIG.scrambleChars;
    let iteration = 0;
    const maxIterations = CONFIG.scrambleIterations;

    const interval = setInterval(() => {
        element.textContent = targetText
            .split('')
            .map((char, index) => {
                // Progressively reveal characters from left to right
                if (index < (iteration / maxIterations) * targetText.length) {
                    return char;
                }
                if (char === ' ') return ' ';
                return chars[Math.floor(Math.random() * chars.length)];
            })
            .join('');

        iteration++;

        if (iteration >= maxIterations) {
            clearInterval(interval);
            element.textContent = targetText;
            state.isScrambling = false;
            if (onComplete) onComplete();
        }
    }, CONFIG.scrambleSpeed);
}

/* ========== ROTATOR ========== */

function setupRotator() {
    DOM.rotatorText = document.getElementById('rotator-text');
    DOM.rotatorPrev = document.getElementById('rotator-prev');
    DOM.rotatorNext = document.getElementById('rotator-next');

    if (!DOM.rotatorText) {
        console.warn('[SGNL] Rotator elements not found');
        return;
    }

    // Event listeners
    DOM.rotatorPrev.addEventListener('click', () => {
        goToRotatorSlide(state.currentRotatorIndex - 1);
        resetRotatorTimer();
    });

    DOM.rotatorNext.addEventListener('click', () => {
        goToRotatorSlide(state.currentRotatorIndex + 1);
        resetRotatorTimer();
    });

    // Start auto-advance
    startRotatorTimer();

    console.log('[SGNL] Rotator initialized');
}

function goToRotatorSlide(index) {
    if (state.isScrambling) return;

    // Wrap around
    let targetIndex = index;
    if (index < 0) targetIndex = CONFIG.rotatorSlogans.length - 1;
    if (index >= CONFIG.rotatorSlogans.length) targetIndex = 0;

    if (targetIndex === state.currentRotatorIndex && DOM.rotatorText.textContent === CONFIG.rotatorSlogans[targetIndex]) {
        return;
    }

    state.currentRotatorIndex = targetIndex;
    const targetText = CONFIG.rotatorSlogans[targetIndex];

    // GSAP bounce + scramble
    if (typeof gsap !== 'undefined') {
        gsap.to(DOM.rotatorText, {
            y: -10,
            duration: 0.1,
            ease: 'power2.in',
            onComplete: () => {
                scrambleToText(DOM.rotatorText, targetText, () => {
                    gsap.to(DOM.rotatorText, {
                        y: 0,
                        duration: 0.15,
                        ease: 'elastic.out(1, 0.5)'
                    });
                });
            }
        });
    } else {
        scrambleToText(DOM.rotatorText, targetText);
    }
}

function startRotatorTimer() {
    state.rotatorTimer = setInterval(() => {
        goToRotatorSlide(state.currentRotatorIndex + 1);
    }, CONFIG.rotatorInterval);
}

function resetRotatorTimer() {
    clearInterval(state.rotatorTimer);
    startRotatorTimer();
}

/* ========== SMOOTH SCROLL ========== */

function setupSmoothScroll() {
    DOM.ctaButtons = document.querySelectorAll('[data-scroll-to]');
    DOM.ctaButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetId = btn.getAttribute('data-scroll-to');
            const targetEl = document.getElementById(targetId);
            if (targetEl) {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

/* ========== GSAP ANIMATIONS ========== */

function initAnimations() {
    if (typeof gsap === 'undefined') {
        console.warn('[SGNL] GSAP not loaded');
        return;
    }

    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    tl.from('.nav', { y: -50, opacity: 0, duration: 0.6 });
    tl.from('.hero-title', { y: 60, opacity: 0, duration: 0.8 }, '-=0.3');
    tl.from('.rotator-wrap', { x: 40, opacity: 0, duration: 0.6 }, '-=0.4');
    tl.from('.hero-ctas', { y: 30, opacity: 0, duration: 0.6 }, '-=0.3');

    tl.add(() => {
        if (DOM.garbageText) {
            DOM.garbageText.classList.add('active');
        }
    }, '-=0.3');
}

function setupGarbageEffect() {
    if (!DOM.garbageText || typeof gsap === 'undefined') return;

    DOM.garbageText.addEventListener('mouseenter', () => {
        gsap.to(DOM.garbageText, {
            duration: 0.1,
            opacity: 0.7,
            x: -2,
            repeat: 5,
            yoyo: true,
            ease: 'power1.inOut',
            onComplete: () => {
                gsap.set(DOM.garbageText, { opacity: 1, x: 0 });
            }
        });
    });
}

/* ========== SEARCH HANDLING ========== */

async function handleSearch(event) {
    if (event) event.preventDefault();

    const topic = DOM.searchInput.value.trim();
    if (!topic || state.isLoading) return;

    console.log('[SGNL] Starting parallel scan for:', topic);

    state.isLoading = true;
    state.currentStatusIndex = 0;

    DOM.searchBtn.disabled = true;
    DOM.searchBtn.textContent = '[ SCANNING... ]';

    // Show results section
    showResultsSection();

    // Show initial loader
    showStatus();

    // ========== PARALLEL FETCH STRATEGY ==========
    // 1. Fast Search: Get raw results instantly (~1-2s)
    // 2. Deep Scan: Get LLM analysis in background (~5-10s)

    const fastSearchPromise = fetch('/fast-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, max_results: CONFIG.maxResults })
    });

    const deepScanPromise = fetch(CONFIG.apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, max_results: CONFIG.maxResults })
    });

    // --- PHASE 1: Handle Fast Search (render results immediately) ---
    try {
        const fastResponse = await fastSearchPromise;

        // Check for rate limit
        if (fastResponse.status === 429) {
            const errorData = await fastResponse.json();
            const retryAfter = errorData.retry_after || 60;
            showError('Rate limit exceeded', 'rate-limit', retryAfter);
            state.isLoading = false;
            DOM.searchBtn.disabled = false;
            DOM.searchBtn.textContent = '[ INITIATE SCAN ]';
            return;
        }

        if (!fastResponse.ok) {
            throw new Error(`Fast search failed: HTTP ${fastResponse.status}`);
        }

        const fastData = await fastResponse.json();
        console.log('[SGNL] Fast search results:', fastData);

        // Extract results array
        let results = [];
        if (fastData.results && Array.isArray(fastData.results)) {
            results = fastData.results;
        } else if (Array.isArray(fastData)) {
            results = fastData;
        }

        // Check for empty results
        if (results.length === 0) {
            showError('No results found', 'no-signal');
            state.isLoading = false;
            DOM.searchBtn.disabled = false;
            DOM.searchBtn.textContent = '[ INITIATE SCAN ]';
            return;
        }

        // Render table immediately (no AI analysis yet)
        renderResults(results, null);

        // Update button but keep disabled (deep scan still running)
        DOM.searchBtn.textContent = '[ ANALYZING... ]';

        // Show "Analyzing Signals" indicator
        showAnalyzingIndicator();

    } catch (fastError) {
        console.error('[SGNL] Fast search error:', fastError);
        showError('Search failed: ' + fastError.message, 'generic');
        state.isLoading = false;
        DOM.searchBtn.disabled = false;
        DOM.searchBtn.textContent = '[ INITIATE SCAN ]';
        return; // Stop here if fast search fails
    }

    // --- PHASE 2: Handle Deep Scan (inject AI analysis when ready) ---
    try {
        const deepResponse = await deepScanPromise;

        if (!deepResponse.ok) {
            throw new Error(`Deep scan failed: HTTP ${deepResponse.status}`);
        }

        const deepData = await deepResponse.json();
        console.log('[SGNL] Deep scan results:', deepData);

        // Parse intelligence report
        let aiAnalysis = null;
        if (deepData.intelligence_report && deepData.best_source) {
            aiAnalysis = {
                summary: deepData.intelligence_report.executive_summary,
                key_findings: deepData.intelligence_report.key_findings || [],
                signal_score: deepData.intelligence_report.signal_score || 0,
                verdict: deepData.intelligence_report.verdict || 'ANALYZED',
                best_source: {
                    url: deepData.best_source.url,
                    title: deepData.best_source.title,
                    reason: deepData.best_source.reason
                }
            };
        } else if (deepData.summary) {
            // Fallback for simpler format
            aiAnalysis = {
                summary: deepData.summary,
                key_findings: deepData.key_findings || [],
                signal_score: deepData.signal_score || 50,
                verdict: 'ANALYZED',
                best_source: deepData.best_source
            };
        }

        // Inject the Intelligence Report (slides in at top)
        if (aiAnalysis) {
            injectIntelligenceReport(aiAnalysis);
        }

        // Hide analyzing indicator
        hideAnalyzingIndicator();

    } catch (deepError) {
        console.error('[SGNL] Deep scan error (non-blocking):', deepError);
        // Silently hide loader - don't break the results
        hideAnalyzingIndicator();
    } finally {
        state.isLoading = false;
        DOM.searchBtn.disabled = false;
        DOM.searchBtn.textContent = '[ INITIATE SCAN ]';
    }
}

/* ========== ANALYZING INDICATOR ========== */

function showAnalyzingIndicator() {
    const indicator = document.getElementById('analyzing-indicator');
    if (indicator) {
        indicator.style.display = 'flex';
        // Pulse animation
        if (typeof gsap !== 'undefined') {
            gsap.to(indicator, {
                opacity: 0.5,
                duration: 0.8,
                repeat: -1,
                yoyo: true,
                ease: 'power1.inOut'
            });
        }
    }
}

function hideAnalyzingIndicator() {
    const indicator = document.getElementById('analyzing-indicator');
    if (indicator) {
        if (typeof gsap !== 'undefined') {
            gsap.killTweensOf(indicator);
        }
        indicator.style.display = 'none';
    }
}

/* ========== INJECT INTELLIGENCE REPORT ========== */

function injectIntelligenceReport(aiAnalysis) {
    const aiSection = document.getElementById('ai-analysis');
    if (!aiSection) return;

    // Populate data
    const verdictEl = document.getElementById('ai-verdict');
    const scoreEl = document.getElementById('ai-signal-score');
    const summaryEl = document.getElementById('ai-summary');
    const findingsEl = document.getElementById('ai-findings');
    const bestLink = document.getElementById('ai-best-link');
    const bestReason = document.getElementById('ai-best-reason');

    if (verdictEl && aiAnalysis.verdict) {
        verdictEl.textContent = aiAnalysis.verdict;
        if (aiAnalysis.verdict.includes('HIGH')) {
            verdictEl.style.background = 'var(--alert-color)';
        }
    }

    if (scoreEl && aiAnalysis.signal_score !== undefined) {
        scoreEl.textContent = aiAnalysis.signal_score;

        // Apply color class based on score level
        const scoreDisplay = scoreEl.closest('.signal-score-display');
        if (scoreDisplay) {
            scoreDisplay.classList.remove('score-low', 'score-mid', 'score-high');
            const score = parseFloat(aiAnalysis.signal_score);
            if (score < 60) {
                scoreDisplay.classList.add('score-low');
            } else if (score < 80) {
                scoreDisplay.classList.add('score-mid');
            } else {
                scoreDisplay.classList.add('score-high');
            }

            // Animate the ring
            const ringFill = document.getElementById('signal-ring-fill');
            if (ringFill) {
                const circumference = 283; // 2 * PI * 45 (radius)
                const offset = circumference - (score / 100) * circumference;
                setTimeout(() => {
                    ringFill.style.strokeDashoffset = offset;
                }, 100);
            }
        }
    }

    // Update timestamp
    const timestampEl = document.getElementById('ai-timestamp');
    if (timestampEl) {
        const today = new Date().toISOString().split('T')[0];
        timestampEl.textContent = `DATE: ${today}`;
    }

    // Update source metadata
    if (aiAnalysis.best_source) {
        const sourceDomainEl = document.getElementById('ai-source-domain');
        if (sourceDomainEl && aiAnalysis.best_source.url) {
            try {
                const domain = new URL(aiAnalysis.best_source.url).hostname.replace('www.', '');
                sourceDomainEl.textContent = domain.toUpperCase();
            } catch (e) {
                sourceDomainEl.textContent = '—';
            }
        }
    }

    if (summaryEl && aiAnalysis.summary) {
        scrambleToText(summaryEl, aiAnalysis.summary);
    }

    if (findingsEl && aiAnalysis.key_findings) {
        findingsEl.innerHTML = '';
        aiAnalysis.key_findings.forEach(finding => {
            const li = document.createElement('li');
            li.textContent = finding;
            findingsEl.appendChild(li);
        });
    }

    if (bestLink && aiAnalysis.best_source) {
        bestLink.textContent = aiAnalysis.best_source.title || aiAnalysis.best_source.url || 'Best Source';
        bestLink.href = aiAnalysis.best_source.url || '#';
    }

    if (bestReason && aiAnalysis.best_source) {
        bestReason.textContent = aiAnalysis.best_source.reason || '';
    }

    // Update CTA button href
    const ctaButton = document.getElementById('ai-cta-button');
    if (ctaButton && aiAnalysis.best_source) {
        ctaButton.href = aiAnalysis.best_source.url || '#';
    }

    // Apply score color class to best-source-card
    const bestSourceCard = document.querySelector('.best-source-card');
    if (bestSourceCard && aiAnalysis.signal_score !== undefined) {
        bestSourceCard.classList.remove('score-low', 'score-mid', 'score-high');
        const score = parseFloat(aiAnalysis.signal_score);
        if (score < 60) {
            bestSourceCard.classList.add('score-low');
        } else if (score < 80) {
            bestSourceCard.classList.add('score-mid');
        } else {
            bestSourceCard.classList.add('score-high');
        }
    }

    // Show with slide-down animation
    aiSection.style.display = 'block';
    if (typeof gsap !== 'undefined') {
        gsap.fromTo(aiSection,
            { opacity: 0, y: -30 },
            {
                opacity: 1,
                y: 0,
                duration: 0.6,
                ease: 'power2.out',
                onComplete: () => {
                    // Auto-scroll to report smoothly
                    aiSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        );
    } else {
        // Fallback if GSAP is missing
        aiSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

/* ========== RESULTS RENDERING ========== */

function showResultsSection() {
    DOM.resultsSection.classList.remove('results-section--hidden');
    DOM.resultsSection.classList.add('results-section--visible');

    // GSAP expand animation
    if (typeof gsap !== 'undefined') {
        gsap.fromTo(DOM.resultsSection,
            { opacity: 0 },
            {
                opacity: 1,
                duration: 0.4,
                ease: 'power2.out',
                onComplete: () => {
                    DOM.resultsSection.style.maxHeight = 'none';
                    DOM.resultsSection.style.overflow = 'visible';
                }
            }
        );
    }
}

function showStatus() {
    DOM.resultsBody.innerHTML = '';
    DOM.resultsHeader.style.display = 'none';

    const statusEl = createElement('div', {
        className: 'status-display active',
        id: 'status-text'
    }, ['INITIALIZING...']);

    DOM.resultsBody.appendChild(statusEl);
    DOM.statusDisplay = statusEl;
}

function cycleStatusMessages() {
    if (!state.isLoading) return;

    const statusEl = DOM.statusDisplay;
    if (!statusEl) return;

    const text = CONFIG.statusTexts[state.currentStatusIndex];
    scrambleToText(statusEl, text, () => {
        state.currentStatusIndex = (state.currentStatusIndex + 1) % CONFIG.statusTexts.length;
        if (state.isLoading) {
            setTimeout(cycleStatusMessages, CONFIG.statusCycleDelay);
        }
    });
}

function showError(message, errorType = 'generic', retryAfter = 60) {
    DOM.resultsBody.innerHTML = '';
    DOM.resultsHeader.style.display = 'none';

    // Hide analyzing indicator if visible
    hideAnalyzingIndicator();

    let errorHtml = '';

    if (errorType === 'no-signal') {
        // NO SIGNAL FOUND - stark brutalist design
        errorHtml = `
            <div class="error-state error-state--no-signal">
                <div class="error-icon">[ / ]</div>
                <h2 class="error-headline">NO SIGNAL FOUND</h2>
                <p class="error-subtext">The internet is full of noise, but not this kind.</p>
                <p class="error-hint">Try a different search vector.</p>
            </div>
        `;
    } else if (errorType === 'rate-limit') {
        // RATE LIMIT - aggressive Access Denied style
        errorHtml = `
            <div class="error-state error-state--rate-limit">
                <h2 class="error-headline error-headline--alert">SYSTEM OVERLOAD // 429</h2>
                <p class="error-subtext">REQUEST LIMIT EXCEEDED. COOLDOWN INITIATED.</p>
                <p class="error-countdown" id="rate-limit-countdown">
                    TRY AGAIN IN <span class="countdown-value">${retryAfter}</span> SECONDS.<span class="error-cursor">_</span>
                </p>
            </div>
        `;
    } else {
        // Generic error
        errorHtml = `
            <div class="error-state error-state--generic">
                <h2 class="error-headline">ERROR</h2>
                <p class="error-subtext">${escapeHTML(message)}</p>
            </div>
        `;
    }

    DOM.resultsBody.innerHTML = errorHtml;

    // Start countdown AFTER HTML is in DOM
    if (errorType === 'rate-limit') {
        setTimeout(() => startRateLimitCountdown(retryAfter), 50);
    }
}

function startRateLimitCountdown(seconds) {
    const countdownEl = document.querySelector('.countdown-value');
    if (!countdownEl) return;

    let remaining = seconds;
    const interval = setInterval(() => {
        remaining--;
        if (countdownEl) {
            countdownEl.textContent = remaining;
        }
        if (remaining <= 0) {
            clearInterval(interval);
            const countdownP = document.getElementById('rate-limit-countdown');
            if (countdownP) {
                countdownP.innerHTML = 'SYSTEM READY. <span class="retry-link" onclick="retrySearch()">[ RETRY NOW ]</span>';
            }
        }
    }, 1000);
}

function retrySearch() {
    const topic = DOM.searchInput.value.trim();
    if (topic) {
        handleSearch();
    }
}

function renderResults(data, aiAnalysis = null) {
    DOM.resultsBody.innerHTML = '';

    // Clear & Hide AI Analysis by default
    const aiSection = document.getElementById('ai-analysis');
    if (aiSection) {
        aiSection.style.display = 'none';
        document.getElementById('ai-summary').textContent = '';
        document.getElementById('ai-best-link').textContent = '';
        document.getElementById('ai-best-link').href = '#';
        document.getElementById('ai-best-reason').textContent = '';
        document.getElementById('ai-findings').innerHTML = '';
        document.getElementById('ai-signal-score').textContent = '--';
        document.getElementById('ai-verdict').textContent = 'ANALYZING';
    }

    // NEW: Render AI Analysis if available (even if results array is empty)
    if (aiAnalysis && aiSection) {
        aiSection.style.display = 'block';

        // Render Verdict Badge
        const verdictEl = document.getElementById('ai-verdict');
        if (aiAnalysis.verdict) {
            verdictEl.textContent = aiAnalysis.verdict;
            // Color based on verdict
            if (aiAnalysis.verdict.includes('HIGH')) {
                verdictEl.style.background = 'var(--alert-color)';
            } else if (aiAnalysis.verdict.includes('LOW')) {
                verdictEl.style.background = '#666';
            }
        }

        // Render Signal Score
        const scoreEl = document.getElementById('ai-signal-score');
        if (aiAnalysis.signal_score !== undefined) {
            scoreEl.textContent = aiAnalysis.signal_score;

            // Apply color class based on score level
            const scoreDisplay = scoreEl.closest('.signal-score-display');
            if (scoreDisplay) {
                scoreDisplay.classList.remove('score-low', 'score-mid', 'score-high');
                const score = parseFloat(aiAnalysis.signal_score);
                if (score < 60) {
                    scoreDisplay.classList.add('score-low');
                } else if (score < 80) {
                    scoreDisplay.classList.add('score-mid');
                } else {
                    scoreDisplay.classList.add('score-high');
                }
            }
        }

        // Render Summary with scramble effect
        if (aiAnalysis.summary) {
            scrambleToText(document.getElementById('ai-summary'), aiAnalysis.summary);
        }

        // Render Key Findings
        const findingsEl = document.getElementById('ai-findings');
        if (aiAnalysis.key_findings && aiAnalysis.key_findings.length > 0) {
            findingsEl.innerHTML = '';
            aiAnalysis.key_findings.forEach(finding => {
                const li = document.createElement('li');
                li.textContent = finding;
                findingsEl.appendChild(li);
            });
        }

        // Render Best Source
        if (aiAnalysis.best_source) {
            const bestLink = document.getElementById('ai-best-link');
            const bestReason = document.getElementById('ai-best-reason');

            // Use title if available, otherwise URL
            bestLink.textContent = aiAnalysis.best_source.title || aiAnalysis.best_source.url || 'UNKNOWN SOURCE';
            bestLink.href = aiAnalysis.best_source.url || '#';
            bestReason.textContent = aiAnalysis.best_source.reason || '';

            // Apply score color class to best-source-card
            const bestSourceCard = document.querySelector('.best-source-card');
            if (bestSourceCard && aiAnalysis.signal_score !== undefined) {
                bestSourceCard.classList.remove('score-low', 'score-mid', 'score-high');
                const score = parseFloat(aiAnalysis.signal_score);
                if (score < 60) {
                    bestSourceCard.classList.add('score-low');
                } else if (score < 80) {
                    bestSourceCard.classList.add('score-mid');
                } else {
                    bestSourceCard.classList.add('score-high');
                }
            }
        }

        // Animate entrance
        if (typeof gsap !== 'undefined') {
            gsap.fromTo(aiSection,
                { opacity: 0, y: 20 },
                { opacity: 1, y: 0, duration: 0.5, delay: 0.2 }
            );
        }
    }

    // Handle empty results (but AI analysis is shown above)
    if (!data || data.length === 0) {
        DOM.resultsHeader.style.display = 'none';
        // Only show "no signal" if there's also no AI analysis
        if (!aiAnalysis) {
            const emptyEl = createElement('div', {
                className: 'results-empty'
            }, ['NO SIGNAL DETECTED. TRY A DIFFERENT VECTOR.']);
            DOM.resultsBody.appendChild(emptyEl);
        }
        return;
    }

    // Show header
    DOM.resultsHeader.style.display = 'flex';
    DOM.resultsCount.textContent = `${data.length} SOURCES FOUND`;

    // Create table
    const table = createElement('table', { className: 'results-table' });
    const thead = createElement('thead');
    const headerRow = createElement('tr');

    ['ID', 'SOURCE', 'SIGNAL %', 'TITLE', 'TIMESTAMP'].forEach(text => {
        headerRow.appendChild(createElement('th', { textContent: text }));
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = createElement('tbody');

    data.forEach((item, index) => {
        const row = createElement('tr');
        const score = item.score ?? item.signal_score ?? 0.5;
        const normalizedScore = score > 1 ? score / 10 : score;
        const scorePercent = (normalizedScore * 100).toFixed(0);

        row.appendChild(createElement('td', { textContent: String(index + 1).padStart(2, '0') }));
        row.appendChild(createElement('td', { textContent: extractDomain(item.url) }));

        const signalCell = createElement('td');
        const signalWrap = createElement('div', { style: 'display: flex; align-items: center;' });
        const signalBar = createElement('div', { className: 'signal-bar' });
        const signalFill = createElement('div', {
            className: 'signal-bar-fill',
            style: `width: ${scorePercent}%`
        });
        signalBar.appendChild(signalFill);
        signalWrap.appendChild(signalBar);
        signalWrap.appendChild(createElement('span', {
            className: 'signal-value',
            textContent: `${scorePercent}%`
        }));
        signalCell.appendChild(signalWrap);
        row.appendChild(signalCell);

        const titleCell = createElement('td');
        titleCell.appendChild(createElement('a', {
            href: item.url,
            target: '_blank',
            rel: 'noopener noreferrer',
            textContent: escapeHTML(item.title || 'Untitled')
        }));
        row.appendChild(titleCell);

        const timestamp = item.timestamp || new Date().toISOString().split('T')[0];
        row.appendChild(createElement('td', { textContent: timestamp }));

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    DOM.resultsBody.appendChild(table);

    // Animate rows
    if (typeof gsap !== 'undefined') {
        gsap.from('tbody tr', {
            y: 20,
            opacity: 0,
            duration: 0.3,
            stagger: 0.06,
            ease: 'power2.out'
        });
    }

    // Scroll to results after a short delay (ensures DOM is painted)
    setTimeout(() => {
        const resultsHeader = document.getElementById('results-header');
        if (resultsHeader) {
            resultsHeader.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 100);
}

/* ========== EVENT LISTENERS ========== */

function setupEventListeners() {
    DOM.searchBtn.addEventListener('click', handleSearch);

    DOM.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch(e);
        }
    });

    DOM.searchInput.addEventListener('input', () => {
        if (DOM.searchInput.value.length > 0) {
            DOM.searchBtn.style.borderColor = 'var(--alert-color)';
        } else {
            DOM.searchBtn.style.borderColor = 'var(--ink-color)';
        }
    });
}

/* ========== INITIALIZATION ========== */

function init() {
    console.log('[SGNL] Initializing Heavy Brutalist UI v4');

    // Cache DOM references
    DOM.searchInput = document.getElementById('search-input');
    DOM.searchBtn = document.getElementById('search-btn');
    DOM.resultsSection = document.getElementById('results-section');
    DOM.resultsHeader = document.getElementById('results-header');
    DOM.resultsCount = document.getElementById('results-count');
    DOM.resultsBody = document.getElementById('results-body');
    DOM.garbageText = document.querySelector('.garbage');
    DOM.heroSection = document.getElementById('hero');

    if (!DOM.searchInput || !DOM.searchBtn || !DOM.resultsBody) {
        console.error('[SGNL] Required DOM elements not found');
        return;
    }

    // Setup
    setupEventListeners();
    setupGarbageEffect();
    setupSmoothScroll();
    setupRotator();

    // Animations
    setTimeout(initAnimations, 100);

    console.log('[SGNL] Initialization complete');
}

// Run on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
