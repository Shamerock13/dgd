const money = new Intl.NumberFormat('de-DE', {style: 'currency', currency: 'EUR'});
const reviewDate = new Intl.DateTimeFormat('de-DE', {dateStyle: 'short', timeStyle: 'short'});
let reviewPanel;
let reviewData = {summary: {}, offers: []};
let reviewFilter = 'PENDING_REVIEW';

function reviewEsc(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

async function reviewRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: {'Content-Type': 'application/json', ...(options.headers || {})},
    ...options,
  });
  if (!response.ok) {
    let message = `Fehler ${response.status}`;
    try {
      const body = await response.json();
      message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail || body);
    } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function reviewStatusLabel(status) {
  return ({
    PENDING_REVIEW: 'Offen',
    APPROVED: 'Freigegeben',
    REJECTED: 'Abgelehnt',
  })[status] || status;
}

function reviewTypeLabel(type) {
  return ({
    bottle: 'Flakon',
    tester: 'Tester',
    sample: 'Probe',
    set: 'Set',
    refill: 'Nachfüllung',
  })[type] || type || 'Unbekannt';
}

function eventActionLabel(action) {
  return ({
    APPROVED: 'Quelle freigegeben',
    REJECTED: 'Quelle abgelehnt',
    SCANNER_ENABLED: 'Scanner aktiviert',
    SCANNER_DISABLED: 'Scanner deaktiviert',
    TEST_SUCCESS: 'Einzeltest erfolgreich',
    TEST_FAILED: 'Einzeltest fehlgeschlagen',
    BROWSER_REQUIRED: 'Browser-Connector erforderlich',
  })[action] || action;
}

function eventDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value || '') : reviewDate.format(date);
}

function reviewHistory(row) {
  const events = row.events || [];
  if (!events.length) return '';
  return `<details class="price-source-review-history">
    <summary>Prüfverlauf (${events.length})</summary>
    <div>${events.map(event => `<article class="history-${reviewEsc(event.action.toLowerCase())}">
      <span>${reviewEsc(eventDate(event.created_at))}</span>
      <b>${reviewEsc(eventActionLabel(event.action))}</b>
      ${event.retailer_activated ? '<em>Händler aktiviert</em>' : ''}
      ${event.note ? `<p>${reviewEsc(event.note)}</p>` : ''}
    </article>`).join('')}</div>
  </details>`;
}

function scannerActions(row) {
  if (row.review_status !== 'APPROVED') return '';
  if (row.browser_connector_required) {
    return '<div class="price-source-review-warning browser-required"><b>Browser-Connector erforderlich</b><span>Der Händler blockiert HTTP und serverseitiges Chromium. Der Server-Scanner wurde deaktiviert. Die Erfassung über deinen normalen Chrome-/Edge-Browser folgt mit Paket 16.7.6.</span></div>';
  }
  if (!row.retailer?.scanner_supported) {
    return '<div class="price-source-review-warning"><b>Scanner nicht verfügbar</b><span>Für diesen Händler ist noch kein automatischer Preisadapter freigegeben.</span></div>';
  }

  const testButton = row.retailer?.active
    ? '<button type="button" class="price-source-test">Quelle jetzt testen</button>'
    : '';

  if (row.scanner_active) {
    return `<div class="price-source-review-actions">${testButton}<button type="button" class="price-source-scanner danger" data-enabled="false" data-activate-retailer="false">Scanner deaktivieren</button></div>`;
  }

  const activateRetailer = !row.retailer?.active;
  return `<div class="price-source-review-actions">
    ${testButton}
    <button type="button" class="primary price-source-scanner" data-enabled="true" data-activate-retailer="${activateRetailer ? 'true' : 'false'}">${activateRetailer ? 'Scanner + Händler aktivieren' : 'Scanner aktivieren'}</button>
  </div>`;
}

function reviewCard(row) {
  const pending = row.review_status === 'PENDING_REVIEW';
  const retailerInactive = !row.retailer?.active;
  const details = [
    reviewTypeLabel(row.product_type),
    row.size_ml ? `${row.size_ml} ml` : 'Größe offen',
    row.concentration || 'Konzentration offen',
    row.product_variant || row.product_name || 'Variante offen',
  ];
  const adapterLabel = row.browser_connector_required
    ? 'Browser erforderlich'
    : (row.retailer.scanner_supported ? 'Server verfügbar' : 'Nicht verfügbar');
  return `<article class="price-source-review-card" data-offer-id="${reviewEsc(row.id)}">
    <div class="price-source-review-top">
      <div>
        <small>${reviewEsc(row.fragrance.brand_name)} · ${reviewEsc(row.retailer.name)}</small>
        <h3>${reviewEsc(row.fragrance.name)}</h3>
      </div>
      <span class="price-source-review-status status-${reviewEsc(row.review_status.toLowerCase())}">${reviewStatusLabel(row.review_status)}</span>
    </div>
    <div class="price-source-review-details">${details.map(item => `<span>${reviewEsc(item)}</span>`).join('')}</div>
    <div class="price-source-review-price"><b>${money.format(row.total_eur)}</b><span>${money.format(row.price_eur)} + ${money.format(row.shipping_eur)} Versand</span></div>
    <a href="${reviewEsc(row.product_url)}" target="_blank" rel="noreferrer">Produktseite beim Händler öffnen</a>
    <dl>
      <div><dt>Quellen-ID</dt><dd>${reviewEsc(row.offer_source_id || 'fehlt')}</dd></div>
      <div><dt>Händler</dt><dd>${row.retailer.active ? 'Aktiv' : 'Inaktiv'}</dd></div>
      <div><dt>Scanner</dt><dd>${row.scanner_active ? 'Aktiv' : 'Deaktiviert'}</dd></div>
      <div><dt>Adapter</dt><dd>${reviewEsc(adapterLabel)}</dd></div>
      <div><dt>Zuletzt geprüft</dt><dd>${row.checked_at ? reviewEsc(eventDate(row.checked_at)) : 'Noch nie'}</dd></div>
      ${row.ean_gtin ? `<div><dt>EAN/GTIN</dt><dd>${reviewEsc(row.ean_gtin)}</dd></div>` : ''}
    </dl>
    ${row.variant_warning ? `<div class="price-source-review-warning"><b>Prüfhinweis</b><span>${reviewEsc(row.variant_warning)}</span></div>` : ''}
    ${pending ? `<div class="price-source-review-actions">
      <button type="button" class="primary price-source-decision" data-action="approve" data-activate-retailer="false">Freigeben</button>
      ${retailerInactive ? '<button type="button" class="price-source-decision" data-action="approve" data-activate-retailer="true">Freigeben + Händler aktivieren</button>' : ''}
      <button type="button" class="price-source-decision danger" data-action="reject" data-activate-retailer="false">Ablehnen</button>
    </div>` : ''}
    ${scannerActions(row)}
    ${reviewHistory(row)}
  </article>`;
}

function renderPriceSourceReview() {
  if (!reviewPanel) return;
  const summary = reviewData.summary || {};
  const rows = (reviewData.offers || []).filter(row => reviewFilter === 'ALL' || row.review_status === reviewFilter);
  reviewPanel.innerHTML = `
    <section class="price-source-review-head">
      <div><span>Preisquellen 16.7.5</span><h2>Importierte Preisquellen prüfen</h2><p>Produktseite, Variante, Größe und Händler bewusst kontrollieren. Scanner werden je Quelle separat freigegeben und können einzeln getestet werden.</p></div>
      <button type="button" class="price-source-review-refresh">Aktualisieren</button>
    </section>
    <section class="price-source-review-summary">
      <button type="button" data-filter="PENDING_REVIEW" class="${reviewFilter === 'PENDING_REVIEW' ? 'active' : ''}"><b>${summary.pending || 0}</b><span>Offen</span></button>
      <button type="button" data-filter="APPROVED" class="${reviewFilter === 'APPROVED' ? 'active' : ''}"><b>${summary.approved || 0}</b><span>Freigegeben</span></button>
      <button type="button" data-filter="REJECTED" class="${reviewFilter === 'REJECTED' ? 'active' : ''}"><b>${summary.rejected || 0}</b><span>Abgelehnt</span></button>
      <button type="button" data-filter="ALL" class="${reviewFilter === 'ALL' ? 'active' : ''}"><b>${(reviewData.offers || []).length}</b><span>Alle geladen</span></button>
      <div class="price-source-review-counter"><b>${summary.scanner_active || 0}</b><span>Scanner aktiv</span></div>
      <div class="price-source-review-counter browser-required"><b>${summary.browser_required || 0}</b><span>Browser nötig</span></div>
    </section>
    <section class="price-source-review-list">
      ${rows.length ? rows.map(reviewCard).join('') : '<div class="price-source-review-empty">Für diesen Filter gibt es keine Preisquellen.</div>'}
    </section>`;

  reviewPanel.querySelector('.price-source-review-refresh').addEventListener('click', loadPriceSourceReview);
  reviewPanel.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    reviewFilter = button.dataset.filter;
    renderPriceSourceReview();
  }));
  reviewPanel.querySelectorAll('.price-source-decision').forEach(button => button.addEventListener('click', submitPriceSourceDecision));
  reviewPanel.querySelectorAll('.price-source-scanner').forEach(button => button.addEventListener('click', submitScannerDecision));
  reviewPanel.querySelectorAll('.price-source-test').forEach(button => button.addEventListener('click', submitSourceTest));
}

async function loadPriceSourceReview() {
  if (!reviewPanel) return;
  reviewPanel.innerHTML = '<div class="price-source-review-loading">Preisquellen werden geladen …</div>';
  try {
    reviewData = await reviewRequest('/api/prices/review/offers?status=ALL&limit=500');
    renderPriceSourceReview();
  } catch (error) {
    reviewPanel.innerHTML = `<div class="price-source-review-error">${reviewEsc(error.message)}</div>`;
  }
}

async function submitPriceSourceDecision(event) {
  const button = event.currentTarget;
  const card = button.closest('[data-offer-id]');
  const offerId = card?.dataset.offerId;
  const action = button.dataset.action;
  if (!offerId || !action) return;

  const label = action === 'approve' ? 'freigeben' : 'ablehnen';
  if (!confirm(`Diese Preisquelle wirklich ${label}?`)) return;
  const note = prompt('Prüfnotiz (optional):', '');
  if (note === null) return;

  button.disabled = true;
  try {
    await reviewRequest(`/api/prices/review/offers/${offerId}/decision`, {
      method: 'POST',
      body: JSON.stringify({
        action,
        activate_retailer: button.dataset.activateRetailer === 'true',
        note: note.trim() || null,
      }),
    });
    await loadPriceSourceReview();
  } catch (error) {
    alert(error.message);
    button.disabled = false;
  }
}

async function submitScannerDecision(event) {
  const button = event.currentTarget;
  const card = button.closest('[data-offer-id]');
  const offerId = card?.dataset.offerId;
  const enabled = button.dataset.enabled === 'true';
  if (!offerId) return;

  const description = enabled
    ? (button.dataset.activateRetailer === 'true' ? 'Händler und Scanner wirklich aktivieren?' : 'Scanner für diese Preisquelle wirklich aktivieren?')
    : 'Scanner für diese Preisquelle wirklich deaktivieren?';
  if (!confirm(description)) return;
  const note = prompt('Notiz zur Scanner-Entscheidung (optional):', '');
  if (note === null) return;

  button.disabled = true;
  try {
    await reviewRequest(`/api/prices/review/offers/${offerId}/scanner`, {
      method: 'POST',
      body: JSON.stringify({
        enabled,
        activate_retailer: button.dataset.activateRetailer === 'true',
        note: note.trim() || null,
      }),
    });
    await loadPriceSourceReview();
  } catch (error) {
    alert(error.message);
    button.disabled = false;
  }
}

async function submitSourceTest(event) {
  const button = event.currentTarget;
  const card = button.closest('[data-offer-id]');
  const offerId = card?.dataset.offerId;
  if (!offerId || !confirm('Diese Produktseite jetzt einmal beim Händler prüfen?')) return;

  button.disabled = true;
  button.textContent = 'Prüfe …';
  try {
    const result = await reviewRequest(`/api/prices/review/offers/${offerId}/test`, {method: 'POST'});
    const availability = result.in_stock ? 'lieferbar' : 'nicht lieferbar';
    alert(`Test erfolgreich: ${money.format(result.price_eur)} · ${availability}.`);
    await loadPriceSourceReview();
  } catch (error) {
    alert(error.message);
    await loadPriceSourceReview();
  }
}

function enhancePriceSourceReview() {
  const tabs = document.querySelector('.admin-tabs');
  if (!tabs || tabs.dataset.priceSourceReviewEnhanced === 'true') return;
  tabs.dataset.priceSourceReviewEnhanced = 'true';

  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'price-source-review-tab';
  button.textContent = 'Preisquellen prüfen';
  tabs.appendChild(button);

  button.addEventListener('click', () => {
    tabs.querySelectorAll('button').forEach(item => item.classList.remove('active'));
    button.classList.add('active');
    const main = tabs.closest('.admin-main');
    [...main.children].forEach(child => {
      if (child !== tabs && !child.classList.contains('admin-head') && !child.classList.contains('price-source-review-panel')) child.hidden = true;
    });
    reviewPanel = main.querySelector('.price-source-review-panel');
    if (!reviewPanel) {
      reviewPanel = document.createElement('section');
      reviewPanel.className = 'price-source-review-panel';
      main.appendChild(reviewPanel);
    }
    reviewPanel.hidden = false;
    loadPriceSourceReview();
  });

  tabs.addEventListener('click', event => {
    if (event.target === button || event.target.closest('.price-source-review-tab')) return;
    if (reviewPanel) reviewPanel.hidden = true;
  }, true);
}

enhancePriceSourceReview();
new MutationObserver(enhancePriceSourceReview).observe(document.documentElement, {childList: true, subtree: true});
