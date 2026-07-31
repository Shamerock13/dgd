const browserQueueDate = new Intl.DateTimeFormat('de-DE', {
  dateStyle: 'short',
  timeStyle: 'short',
});

let browserQueueLoading = false;
let browserQueueRefreshTimer = null;

function browserQueueEsc(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function browserQueueDateLabel(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unbekannt' : browserQueueDate.format(date);
}

function browserQueueStatusLabel(item) {
  if (item.manual_status === 'NEVER_CHECKED') {
    return {
      title: 'Noch nie manuell geprüft',
      detail: 'Diese Quelle steht zuerst in der Browser-Prüfrunde.',
      className: 'never-checked',
    };
  }
  if (item.manual_status === 'DUE') {
    return {
      title: 'Manuelle Prüfung fällig',
      detail: `Zuletzt geprüft: ${browserQueueDateLabel(item.manual_checked_at)}`,
      className: 'due',
    };
  }
  return {
    title: 'Manuelle Prüfung aktuell',
    detail: item.next_due_at
      ? `Nächste Prüfung: ${browserQueueDateLabel(item.next_due_at)}`
      : `Zuletzt geprüft: ${browserQueueDateLabel(item.manual_checked_at)}`,
    className: 'current',
  };
}

async function browserQueueRequest() {
  const response = await fetch(
    '/api/prices/browser-connector/queue?due_only=false&limit=1000',
    {cache: 'no-store'},
  );
  if (!response.ok) {
    let message = `Fehler ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') message = body.detail;
    } catch {}
    throw new Error(message);
  }
  return response.json();
}

function decorateBrowserQueueCards(panel, items) {
  const byOfferId = new Map(items.map(item => [item.offer_id, item]));
  panel.querySelectorAll('.price-source-review-card[data-offer-id]').forEach(card => {
    card.querySelector('.browser-review-card-status')?.remove();
    const item = byOfferId.get(card.dataset.offerId);
    if (!item) return;
    const status = browserQueueStatusLabel(item);
    const block = document.createElement('div');
    block.className = `browser-review-card-status ${status.className}`;
    block.innerHTML = `<b>${browserQueueEsc(status.title)}</b><span>${browserQueueEsc(status.detail)}</span>`;
    const history = card.querySelector('.price-source-review-history');
    if (history) card.insertBefore(block, history);
    else card.appendChild(block);
  });
}

function renderBrowserQueue(panel, data, container) {
  const summary = data.summary || {};
  const dueItems = (data.items || []).filter(item => item.manual_check_due);
  const nextItem = dueItems[0] || null;
  container.className = 'browser-review-queue';
  container.innerHTML = `
    <div>
      <span>Browser-Prüfrunde 18.3</span>
      <h3>Manuelle Preisquellen nacheinander prüfen</h3>
      <p>Die Erweiterung übernimmt immer nur die geöffnete Seite. Nach dem Speichern bietet sie die nächste fällige Quelle an.</p>
    </div>
    <div class="browser-review-queue-counts">
      <article><b>${Number(summary.due || 0)}</b><span>fällig</span></article>
      <article><b>${Number(summary.never_checked || 0)}</b><span>noch nie geprüft</span></article>
      <article><b>${Number(summary.current || 0)}</b><span>aktuell</span></article>
    </div>
    <div class="browser-review-queue-actions">
      <button type="button" class="primary browser-review-start" ${nextItem ? '' : 'disabled'}>
        ${nextItem ? 'Browser-Prüfrunde starten' : 'Keine Quelle fällig'}
      </button>
      <a href="/api/prices/browser-connector/extension.zip">Aktuelle Erweiterung herunterladen</a>
    </div>
    <small>${nextItem
      ? `Als Nächstes: ${browserQueueEsc([nextItem.brand_name, nextItem.fragrance_name, nextItem.retailer_name].filter(Boolean).join(' · '))}`
      : 'Alle Browser-Quellen liegen innerhalb ihres Prüfintervalls.'}</small>
  `;

  container.querySelector('.browser-review-start')?.addEventListener('click', () => {
    if (!nextItem?.product_url) return;
    const label = [nextItem.brand_name, nextItem.fragrance_name, nextItem.retailer_name]
      .filter(Boolean)
      .join(' · ');
    if (!confirm(`Browser-Prüfrunde mit „${label}“ starten?`)) return;
    window.open(nextItem.product_url, '_blank', 'noopener,noreferrer');
  });
  decorateBrowserQueueCards(panel, data.items || []);
}

async function enhanceBrowserReviewQueue() {
  const panel = document.querySelector('.price-source-review-panel');
  if (!panel || panel.hidden || !panel.querySelector('.price-source-review-head')) return;
  if (panel.querySelector('.browser-review-queue')) return;
  if (browserQueueLoading) return;

  browserQueueLoading = true;
  const container = document.createElement('section');
  container.className = 'browser-review-queue loading';
  container.textContent = 'Browser-Prüfrunde wird geladen …';
  panel.querySelector('.price-source-review-head').after(container);

  try {
    const data = await browserQueueRequest();
    if (!container.isConnected) return;
    renderBrowserQueue(panel, data, container);
  } catch (error) {
    if (!container.isConnected) return;
    container.className = 'browser-review-queue error';
    container.textContent = `Browser-Prüfrunde konnte nicht geladen werden: ${error.message}`;
  } finally {
    browserQueueLoading = false;
  }
}

function scheduleBrowserQueueEnhancement() {
  clearTimeout(browserQueueRefreshTimer);
  browserQueueRefreshTimer = setTimeout(enhanceBrowserReviewQueue, 40);
}

scheduleBrowserQueueEnhancement();
new MutationObserver(scheduleBrowserQueueEnhancement).observe(document.documentElement, {
  childList: true,
  subtree: true,
});
