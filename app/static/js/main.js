/* Plate Theory — Shared Utilities */

function escapeHtml(s) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(s ?? ''));
  return d.innerHTML;
}
window.escapeHtml = escapeHtml;

function showErrorToast(message) {
  const el = document.createElement('div');
  el.className = 'alert alert-danger position-fixed bottom-0 end-0 m-3';
  el.style.zIndex = 9999;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}
window.showErrorToast = showErrorToast;

function toggleFollow(username, btn) {
  const isFollowing = btn.dataset.following === 'true';
  fetch(`/user/${username}/follow`, {
    method: 'POST',
    headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      btn.dataset.following = !isFollowing;
      btn.textContent = isFollowing ? 'Follow' : 'Unfollow';
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

function confirmAction(title, message, callback) {
    if (confirm(`${title}\n\n${message}`)) {
        callback();
    }
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
   HERO WORD-BY-WORD REVEAL
───────────────────────────────────────────── */
function initHeroReveal() {
    if (_prefersReducedMotion) return;
    document.querySelectorAll('[data-word-reveal]').forEach(el => {
        const words = el.textContent.trim().split(/\s+/);
        el.innerHTML = words.map((w, i) =>
            `<span class="word-reveal-wrap"><span class="word-reveal-inner" style="--wi:${i}">${w}</span></span>`
        ).join(' ');
        // Double rAF: first frame paints the hidden state,
        // second frame triggers the transition to visible state.
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                el.classList.add('words-ready');
            });
        });
    });
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

document.addEventListener('DOMContentLoaded', () => {
    autoDismissAlerts();
    initScrollReveal();
    initNavbarScroll();
    initHeroReveal();
    initGroceryCheck();
});
