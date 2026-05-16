/* Plate Theory — Shared Utilities */

function escapeHtml(s) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(s ?? ''));
  return d.innerHTML;
}
window.escapeHtml = escapeHtml;

function toggleFollow(username, btn) {
  const isFollowing = btn.dataset.following === 'true';
  fetch(`/user/${username}/follow`, {
    method: 'POST',
    headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
  })
  .then(r => r.json())
  .then(data => {
    if (!data.success) return;

    // 1. Flip the clicked button + any other follow-button for the SAME user
    //    on this page (e.g. recipe cards showing the same creator).
    document.querySelectorAll(`.follow-btn[data-username="${username}"], button[data-username="${username}"]`).forEach(b => {
      b.dataset.following = String(!isFollowing);
      b.textContent = isFollowing ? 'Follow' : 'Unfollow';
    });

    // 2. Update FOLLOWER COUNT — only if the displayed count belongs to the
    //    user we just followed/unfollowed (matched via data-username).
    const followerEl = document.getElementById('profile-follower-count');
    if (followerEl && followerEl.dataset.username === username && typeof data.follower_count === 'number') {
      followerEl.textContent = data.follower_count;
    }

    // 3. Update FOLLOWING COUNT — only if we're on the CURRENT USER's own
    //    profile (their following count changed by ±1).
    const currentUser = document.querySelector('meta[name="current-user"]')?.content || '';
    const followingEl = document.getElementById('profile-following-count');
    if (followingEl && followingEl.dataset.username === currentUser && currentUser) {
      const delta = isFollowing ? -1 : 1;
      followingEl.textContent = (parseInt(followingEl.textContent, 10) || 0) + delta;
    }
  })
  .catch(() => showErrorToast('Could not update follow status.'));
}
window.toggleFollow = toggleFollow;

async function apiCall(url, method = 'GET', data = null) {
    const opts = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
        }
    };
    if (data && method !== 'GET') opts.body = JSON.stringify(data);
    const resp = await fetch(url, opts);
    if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || resp.statusText);
    }
    return resp.json();
}

function autoDismissAlerts() {
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
}

/* ── Styled confirm modal ──
 * Themed equivalent of native confirm(). Uses #ptConfirmModal defined in base.html.
 * Returns a Promise<boolean> that resolves true on Confirm, false on Cancel/close.
 *
 *   ptConfirm({ title, message, confirmText, cancelText, variant }) → Promise<bool>
 *
 * `variant` toggles the confirm button colour: 'danger' (default) = coral, 'primary' = mint.
 */
function ptConfirm(opts) {
    opts = opts || {};
    const modalEl   = document.getElementById('ptConfirmModal');
    if (!modalEl || !window.bootstrap) {
        // Graceful fallback if base.html modal is somehow missing.
        return Promise.resolve(window.confirm((opts.title ? opts.title + '\n\n' : '') + (opts.message || 'Are you sure?')));
    }
    const titleEl   = modalEl.querySelector('#ptConfirmTitle');
    const bodyEl    = modalEl.querySelector('#ptConfirmBody');
    const okBtn     = modalEl.querySelector('#ptConfirmOk');
    const cancelBtn = modalEl.querySelector('#ptConfirmCancel');

    titleEl.textContent = opts.title   || 'Confirm';
    bodyEl.textContent  = opts.message || 'Are you sure?';
    okBtn.textContent   = opts.confirmText || 'Confirm';
    cancelBtn.textContent = opts.cancelText || 'Cancel';

    // Reset variant classes
    okBtn.classList.remove('btn-coral', 'btn-mint', 'btn-outline-mint');
    okBtn.classList.add(opts.variant === 'primary' ? 'btn-mint' : 'btn-coral');

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    return new Promise((resolve) => {
        let resolved = false;
        function onOk() {
            resolved = true;
            cleanup();
            modal.hide();
            resolve(true);
        }
        function onHidden() {
            if (!resolved) {
                cleanup();
                resolve(false);
            }
        }
        function cleanup() {
            okBtn.removeEventListener('click', onOk);
            modalEl.removeEventListener('hidden.bs.modal', onHidden);
        }
        okBtn.addEventListener('click', onOk);
        modalEl.addEventListener('hidden.bs.modal', onHidden);
        modal.show();
    });
}
window.ptConfirm = ptConfirm;

// Backward-compat: existing confirmAction(title, message, callback) callers still work,
// but now they see the styled modal instead of the browser dialog.
function confirmAction(title, message, callback) {
    ptConfirm({ title: title, message: message }).then((ok) => { if (ok) callback(); });
}

function showSpinner(container) {
    if (!container || container.querySelector('.pt-spinner-overlay')) return;
    const overlay = document.createElement('div');
    overlay.className = 'pt-spinner-overlay';
    Object.assign(overlay.style, {
        position: 'absolute',
        inset: '0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(15, 14, 20, 0.7)',
        borderRadius: 'inherit',
        zIndex: '10'
    });
    overlay.innerHTML = '<div class="spinner-border text-light" role="status"><span class="visually-hidden">Loading…</span></div>';

    const pos = getComputedStyle(container).position;
    if (pos === 'static') container.style.position = 'relative';

    container.appendChild(overlay);
}

function hideSpinner(container) {
    if (!container) return;
    const overlay = container.querySelector('.pt-spinner-overlay');
    if (overlay) overlay.remove();
}

/* ── Toast helpers ──
 * Shows a small floating message bottom-right that fades after ~2.5s.
 * Use showToast(msg) for success/info (mint).
 * Use showErrorToast(msg) for failures (coral).
 */
function _ensureToastContainer() {
    let container = document.getElementById('pt-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'pt-toast-container';
        document.body.appendChild(container);
    }
    return container;
}

function showToast(message, variant) {
    const container = _ensureToastContainer();
    const toast = document.createElement('div');
    toast.className = 'pt-toast pt-toast--' + (variant === 'error' ? 'error' : 'success');
    toast.setAttribute('role', 'status');  // a11y: screen readers announce it
    toast.textContent = message;
    container.appendChild(toast);

    // Trigger CSS transition by adding .show on the next frame.
    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);  // wait for fade-out before removing
    }, 2500);
}

function showErrorToast(message) {
    showToast(message, 'error');
}

// Expose globally so other scripts (planner.js, detail.html, etc.) can use them.
window.showToast = showToast;
window.showErrorToast = showErrorToast;

/* ─────────────────────────────────────────────
   SCROLL REVEAL — row-aware stagger
   Cards in the same visual row fire together,
   staggered left→right by column position.
   Already-visible elements get no animation.
   window.revealElements() is exposed so Load
   More / dynamic content can register new cards.
───────────────────────────────────────────── */
const _prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const _revealObserver = _prefersReducedMotion
    ? { observe: () => {}, unobserve: () => {} }
    : new IntersectionObserver((entries) => {
        // Group simultaneous entries by their rounded top position = visual row
        const rows = new Map();
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const rowKey = Math.round(entry.boundingClientRect.top / 10) * 10;
            if (!rows.has(rowKey)) rows.set(rowKey, []);
            rows.get(rowKey).push(entry.target);
        });

        rows.forEach(rowEls => {
            // Sort by horizontal position so stagger goes left → right
            rowEls.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left);
            rowEls.forEach((el, colIdx) => {
                el.style.setProperty('--reveal-index', colIdx);
                el.classList.add('visible');
                _revealObserver.unobserve(el);
            });
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -24px 0px' });

function revealElements(nodeList) {
    if (_prefersReducedMotion) return;
    const vh = window.innerHeight;

    Array.from(nodeList).forEach(el => {
        if (el.classList.contains('reveal')) return; // already registered
        const top = el.getBoundingClientRect().top;
        el.classList.add('reveal');
        if (top < vh - 10) {
            // In viewport on load — show immediately, no delay
            el.style.setProperty('--reveal-index', 0);
            el.classList.add('visible');
        } else {
            _revealObserver.observe(el);
        }
    });
}
window.revealElements = revealElements;

function initScrollReveal() {
    revealElements(document.querySelectorAll(
        '.pt-card, .card:not(.navbar *):not(header *), .pt-panel, .animate-fade'
    ));
}

/* ─────────────────────────────────────────────
   SMART NAVBAR — hide on scroll down,
   reveal on scroll up, blur when not at top
───────────────────────────────────────────── */
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    let lastY = window.scrollY;
    let ticking = false;

    function update() {
        const y = window.scrollY;
        const atTop = y < 60;

        if (atTop) {
            navbar.classList.remove('nav-hidden', 'nav-scrolled');
        } else if (y > lastY + 4) {
            // Scrolling down — hide
            navbar.classList.add('nav-hidden', 'nav-scrolled');
        } else if (y < lastY - 4) {
            // Scrolling up — reveal with blur
            navbar.classList.remove('nav-hidden');
            navbar.classList.add('nav-scrolled');
        }

        lastY = y;
        ticking = false;
    }

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(update);
            ticking = true;
        }
    }, { passive: true });

    update();
}

/* ─────────────────────────────────────────────
   TOP PAGE LOAD PROGRESS BAR
───────────────────────────────────────────── */
(function initProgressBar() {
    const bar = document.createElement('div');
    bar.id = 'pt-progress';
    document.body.prepend(bar);
    let raf, width = 0;

    function tick() {
        width = Math.min(width + (100 - width) * 0.07, 90);
        bar.style.width = width + '%';
        raf = requestAnimationFrame(tick);
    }

    document.addEventListener('click', e => {
        const a = e.target.closest('a[href]');
        if (!a) return;
        const href = a.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('mailto') ||
            href.startsWith('javascript') || a.target === '_blank') return;
        width = 15;
        bar.style.opacity = '1';
        bar.style.width = '15%';
        bar.classList.remove('pt-progress-done');
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(tick);
    });

    window.addEventListener('DOMContentLoaded', () => {
        cancelAnimationFrame(raf);
        bar.style.width = '100%';
        setTimeout(() => bar.classList.add('pt-progress-done'), 180);
    });
})();

/* ─────────────────────────────────────────────
   AUTO HEADING REVEAL — all h1 + h2 sitewide
   Preserves icons/non-text children.
   h1 in viewport → animates on load.
   h2 + below-fold h1 → animates on scroll.
───────────────────────────────────────────── */
function _splitHeading(el) {
    if (el.dataset.wordReady) return; // already processed

    const isGradient = el.classList.contains('gradient-text');
    if (isGradient) el.classList.remove('gradient-text');

    let wordIdx = 0;
    let html = '';

    // Walk child nodes: preserve element nodes (icons), split text nodes
    el.childNodes.forEach(node => {
        if (node.nodeType === 3) { // text node
            const words = node.textContent.trim().split(/\s+/).filter(Boolean);
            words.forEach(w => {
                const cls = 'word-reveal-inner' + (isGradient ? ' gradient-text' : '');
                html += `<span class="word-reveal-wrap"><span class="${cls}" style="--wi:${wordIdx++}">${w}</span></span> `;
            });
        } else if (node.nodeType === 1) { // element (icon etc) — pass through untouched
            html += node.outerHTML + ' ';
        }
    });

    el.innerHTML = html.trim();
    el.dataset.wordReady = '1';
}

function _triggerWordReveal(el) {
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            el.classList.add('words-ready');
        });
    });
}

function initHeadingReveal() {
    if (_prefersReducedMotion) return;

    const headings = Array.from(
        document.querySelectorAll('h1, h2')
    ).filter(el => !el.closest('header, nav, footer, .modal, .btn, button'));

    if (!headings.length) return;

    // Split all headings into word spans up-front
    headings.forEach(_splitHeading);

    const vh = window.innerHeight;
    const belowFold = [];

    headings.forEach(el => {
        const top = el.getBoundingClientRect().top;
        if (el.tagName === 'H1' && top < vh - 20) {
            // h1 in viewport on load — fire immediately
            _triggerWordReveal(el);
        } else {
            // h2 or below-fold h1 — fire on scroll
            belowFold.push(el);
        }
    });

    if (!belowFold.length) return;

    const headingObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            _triggerWordReveal(entry.target);
            headingObserver.unobserve(entry.target);
        });
    }, { threshold: 0.25, rootMargin: '0px 0px -30px 0px' });

    belowFold.forEach(el => headingObserver.observe(el));
}

/* ─────────────────────────────────────────────
   COUNT-UP — .stat-number animates 0 → value
   on scroll. Handles integers and decimals.
───────────────────────────────────────────── */
function initCountUp() {
    if (_prefersReducedMotion) return;

    const els = document.querySelectorAll('.stat-number');
    if (!els.length) return;

    // easeOutQuart
    const ease = t => 1 - Math.pow(1 - t, 4);

    function animate(el) {
        const raw = el.dataset.countTarget || '';
        const target = parseFloat(raw);
        if (isNaN(target) || target === 0) return;

        const decimals = raw.includes('.') ? (raw.split('.')[1] || '').length : 0;
        const duration = 850;
        const startTime = performance.now();

        el.textContent = decimals ? '0.' + '0'.repeat(decimals) : '0';

        function tick(now) {
            const p = Math.min((now - startTime) / duration, 1);
            const v = target * ease(p);
            el.textContent = decimals ? v.toFixed(decimals) : Math.round(v);
            if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    // Store target values before observer changes textContent
    els.forEach(el => {
        el.dataset.countTarget = el.textContent.trim();
    });

    const countObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            animate(entry.target);
            countObs.unobserve(entry.target);
        });
    }, { threshold: 0.6 });

    els.forEach(el => countObs.observe(el));
}

/* ─────────────────────────────────────────────
   GROCERY STRIKETHROUGH
───────────────────────────────────────────── */
function initGroceryCheck() {
    document.addEventListener('change', e => {
        if (e.target.type !== 'checkbox') return;
        const row = e.target.closest('.grocery-row');
        if (row) row.classList.toggle('checked', e.target.checked);
    });
}

/* ── Global form-level confirm interceptor ──
 * Any <form class="pt-confirm-form"> will route its submit through the styled
 * ptConfirm modal instead of native confirm(). Configure per-form via data-*:
 *   data-confirm-title   — modal title       (default: "Confirm")
 *   data-confirm-message — modal body text   (default: "Are you sure?")
 *   data-confirm-text    — primary btn label (default: "Confirm")
 *   data-confirm-variant — "danger" (default coral) | "primary" (mint)
 *
 * Uses delegation so dynamically-added forms work too.
 */
function initConfirmForms() {
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!(form instanceof HTMLFormElement)) return;
        if (!form.classList.contains('pt-confirm-form')) return;
        if (form.dataset.ptConfirmed === '1') return;  // already approved — let it through

        e.preventDefault();
        ptConfirm({
            title:       form.dataset.confirmTitle   || 'Confirm',
            message:     form.dataset.confirmMessage || 'Are you sure?',
            confirmText: form.dataset.confirmText    || 'Confirm',
            variant:     form.dataset.confirmVariant || 'danger',
        }).then(function (ok) {
            if (ok) {
                form.dataset.ptConfirmed = '1';
                form.submit();
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    autoDismissAlerts();
    initScrollReveal();
    initNavbarScroll();
    initHeadingReveal();
    initCountUp();
    initGroceryCheck();
    initConfirmForms();
});
