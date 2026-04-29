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

document.addEventListener('DOMContentLoaded', () => {
    autoDismissAlerts();
});
