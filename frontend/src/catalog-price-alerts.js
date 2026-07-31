const alertEuro = new Intl.NumberFormat('de-DE', {style: 'currency', currency: 'EUR'});
const alertDateTime = new Intl.DateTimeFormat('de-DE', {dateStyle: 'short', timeStyle: 'short'});

const alertCache = new Map();
const alertRequests = new Map();

function alertFragranceId() {
  return new URLSearchParams(window.location.search).get('fragrance') || '';
}

function alertEscape(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function alertDate(value) {
  if (!value) return 'Noch nie';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unbekannt' : alertDateTime.format(date);
}

function optionalNumber(value) {
  const text = String(value ?? '').trim().replace(',', '.');
  if (!text) return null;
  const parsed = Number(text);
  return Number.isFinite(parsed) ? parsed : NaN;
}

function ensureAlertStyles() {
  if (document.getElementById('catalog-price-alert-styles')) return;
  const style = document.createElement('style');
  style.id = 'catalog-price-alert-styles';
  style.textContent = `
    .catalog-price-alert{display:grid;gap:.8rem;padding:.9rem;border:1px solid rgba(217,168,95,.28);border-radius:13px;background:rgba(217,168,95,.055)}
    .catalog-price-alert-head{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem}.catalog-price-alert-head h4{margin:0 0 .22rem}.catalog-price-alert-head p{margin:0;color:#aaa;font-size:.82rem;line-height:1.4}
    .catalog-price-alert-status{padding:.32rem .55rem;border:1px solid rgba(255,255,255,.18);border-radius:999px;font-size:.75rem;white-space:nowrap}
    .catalog-price-alert-status.triggered{border-color:rgba(92,205,130,.65);background:rgba(92,205,130,.13);color:#bceaca}
    .catalog-price-alert-status.waiting{border-color:rgba(217,168,95,.55);color:#f2cf99}.catalog-price-alert-status.inactive{opacity:.68}
    .catalog-price-alert-status.problem{border-color:rgba(255,180,0,.55);color:#ffd37d}
    .catalog-price-alert-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.55rem}.catalog-price-alert-summary div{display:grid;gap:.16rem;padding:.58rem .65rem;border:1px solid rgba(255,255,255,.08);border-radius:10px;background:rgba(0,0,0,.1)}
    .catalog-price-alert-summary small{color:#aaa}.catalog-price-alert-summary b{font-size:.88rem;overflow-wrap:anywhere}
    .catalog-price-alert-form{display:grid;grid-template-columns:minmax(150px,1fr) minmax(170px,1fr) auto;gap:.65rem;align-items:end}.catalog-price-alert-form label{display:grid;gap:.3rem;font-size:.78rem;color:#bbb}.catalog-price-alert-form input[type=number]{width:100%;border:1px solid rgba(255,255,255,.16);border-radius:9px;padding:.58rem .62rem;background:rgba(0,0,0,.2);color:inherit;font:inherit}
    .catalog-price-alert-active{display:flex!important;grid-column:1/-1;align-items:center;gap:.45rem}.catalog-price-alert-actions{display:flex;flex-wrap:wrap;gap:.5rem}.catalog-price-alert-actions button{border:1px solid rgba(255,255,255,.16);border-radius:9px;padding:.58rem .72rem;background:rgba(255,255,255,.04);color:inherit;font:inherit;cursor:pointer}.catalog-price-alert-actions button.primary{border-color:#d9a85f;background:rgba(217,168,95,.16);color:#f4d39f}.catalog-price-alert-actions button.danger{border-color:rgba(255,100,100,.42)}
    .catalog-price-alert-actions button:disabled{opacity:.5;cursor:wait}.catalog-price-alert-note,.catalog-price-alert-error{font-size:.78rem;color:#aaa;line-height:1.4}.catalog-price-alert-error{color:#ffb5b5}.catalog-price-alert-loading{padding:.75rem;color:#aaa}
    @media(max-width:850px){.catalog-price-alert-summary{grid-template-columns:repeat(2,minmax(0,1fr))}.catalog-price-alert-form{grid-template-columns:1fr 1fr}.catalog-price-alert-actions{grid-column:1/-1}}
    @media(max-width:560px){.catalog-price-alert-head{display:grid}.catalog-price-alert-summary,.catalog-price-alert-form{grid-template-columns:1fr}}
  `;
  document.head.appendChild(style);
}

function statusInfo(status) {
  return ({
    TRIGGERED: {label: 'Ziel erreicht', className: 'triggered'},
    WAITING: {label: 'Wartet auf Zielpreis', className: 'waiting'},
    INACTIVE: {label: 'Deaktiviert', className: 'inactive'},
    NO_ELIGIBLE_OFFER: {label: 'Nichts lieferbar', className: 'problem'},
    VARIANT_MISSING: {label: 'Variante fehlt', className: 'problem'},
  })[status] || {label: status || 'Nicht eingerichtet', className: 'inactive'};
}

async function alertApi(url, options = {}) {
  const response = await fetch(url, {
    headers: {'Content-Type': 'application/json', ...(options.headers || {})},
    ...options,
  });
  if (!response.ok) {
    let message = `Fehler ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') message = body.detail;
      else if (Array.isArray(body.detail)) message = body.detail.map(row => row.msg).filter(Boolean).join(' · ') || message;
    } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

async function loadAlerts(fragranceId, force = false) {
  if (!force && alertCache.has(fragranceId)) return alertCache.get(fragranceId);
  if (!force && alertRequests.has(fragranceId)) return alertRequests.get(fragranceId);
  const request = alertApi(`/api/prices/fragrances/${encodeURIComponent(fragranceId)}/alerts`)
    .then(body => {
      const alerts = body?.alerts || [];
      alertCache.set(fragranceId, alerts);
      alertRequests.delete(fragranceId);
      return alerts;
    })
    .catch(error => {
      alertRequests.delete(fragranceId);
      throw error;
    });
  alertRequests.set(fragranceId, request);
  return request;
}

function findAlert(alerts, variantKey) {
  return (alerts || []).find(row => row.variant_key === variantKey) || null;
}

function alertSummaryMarkup(alert) {
  if (!alert) return '';
  const target = alert.target_total_eur == null ? 'Nicht gesetzt' : alertEuro.format(alert.target_total_eur);
  const lowRule = alert.max_percent_above_low == null ? 'Nicht gesetzt' : `max. ${Number(alert.max_percent_above_low).toLocaleString('de-DE')} % über Tief`;
  const current = alert.current_total_eur == null ? 'Nicht verfügbar' : alertEuro.format(alert.current_total_eur);
  return `<div class="catalog-price-alert-summary">
    <div><small>Aktueller Bestpreis</small><b>${alertEscape(current)}</b></div>
    <div><small>Zielpreis</small><b>${alertEscape(target)}</b></div>
    <div><small>Tiefpreis-Regel</small><b>${alertEscape(lowRule)}</b></div>
    <div><small>Letzte Auslösung</small><b>${alertEscape(alertDate(alert.last_triggered_at))}</b></div>
  </div>`;
}

function renderAlertPanel(section, fragranceId, variantKey, alert, error = '') {
  section.querySelector('.catalog-price-alert')?.remove();
  const incomplete = Boolean(section.querySelector('.catalog-price-warning'));
  const status = statusInfo(alert?.status);
  const targetValue = alert?.target_total_eur ?? '';
  const percentValue = alert?.max_percent_above_low ?? '';
  const active = alert ? Boolean(alert.active) : true;

  const panel = document.createElement('section');
  panel.className = 'catalog-price-alert';
  panel.dataset.variantKey = variantKey;
  panel.innerHTML = `
    <div class="catalog-price-alert-head">
      <div><h4>Preisalarm</h4><p>Lokaler In-App-Alarm für genau diese Größe, Konzentration und Produktart.</p></div>
      <span class="catalog-price-alert-status ${alertEscape(status.className)}">${alertEscape(status.label)}</span>
    </div>
    ${alertSummaryMarkup(alert)}
    ${incomplete ? '<div class="catalog-price-alert-error">Größe und Konzentration müssen vollständig gepflegt sein, bevor ein Alarm angelegt werden kann.</div>' : ''}
    ${error ? `<div class="catalog-price-alert-error">${alertEscape(error)}</div>` : ''}
    <form class="catalog-price-alert-form">
      <label>Zielpreis inklusive Versand
        <input name="target" type="number" min="0.01" max="100000" step="0.01" inputmode="decimal" value="${alertEscape(targetValue)}" placeholder="z. B. 79,99" ${incomplete ? 'disabled' : ''}>
      </label>
      <label>Maximal über historischem Tief
        <input name="percent" type="number" min="0" max="500" step="0.1" inputmode="decimal" value="${alertEscape(percentValue)}" placeholder="z. B. 5" ${incomplete ? 'disabled' : ''}>
      </label>
      <div class="catalog-price-alert-actions">
        <button type="submit" class="primary" ${incomplete ? 'disabled' : ''}>${alert ? 'Alarm speichern' : 'Alarm anlegen'}</button>
        ${alert ? '<button type="button" class="catalog-price-alert-delete danger">Alarm löschen</button>' : ''}
      </div>
      <label class="catalog-price-alert-active"><input name="active" type="checkbox" ${active ? 'checked' : ''} ${incomplete ? 'disabled' : ''}> Alarm aktiv auswerten</label>
    </form>
    <div class="catalog-price-alert-note">Mindestens eine Regel ist nötig. Erfüllt eine davon den Preis, wechselt der Alarm auf „Ziel erreicht“. E-Mail und Push folgen erst in einem späteren Paket.</div>
  `;
  section.appendChild(panel);

  const form = panel.querySelector('form');
  form?.addEventListener('submit', async event => {
    event.preventDefault();
    const target = optionalNumber(form.elements.target.value);
    const percent = optionalNumber(form.elements.percent.value);
    if (Number.isNaN(target) || Number.isNaN(percent)) {
      renderAlertPanel(section, fragranceId, variantKey, alert, 'Bitte nur gültige Zahlen eingeben.');
      return;
    }
    if (target == null && percent == null) {
      renderAlertPanel(section, fragranceId, variantKey, alert, 'Bitte einen Zielpreis oder einen Abstand zum historischen Tief angeben.');
      return;
    }
    const buttons = panel.querySelectorAll('button');
    buttons.forEach(button => { button.disabled = true; });
    try {
      await alertApi(`/api/prices/fragrances/${encodeURIComponent(fragranceId)}/alerts/${encodeURIComponent(variantKey)}`, {
        method: 'PUT',
        body: JSON.stringify({
          active: Boolean(form.elements.active.checked),
          target_total_eur: target,
          max_percent_above_low: percent,
        }),
      });
      const alerts = await loadAlerts(fragranceId, true);
      renderAlertPanel(section, fragranceId, variantKey, findAlert(alerts, variantKey));
    } catch (saveError) {
      renderAlertPanel(section, fragranceId, variantKey, alert, saveError.message);
    }
  });

  panel.querySelector('.catalog-price-alert-delete')?.addEventListener('click', async event => {
    if (!confirm('Diesen Preisalarm wirklich löschen?')) return;
    event.currentTarget.disabled = true;
    try {
      await alertApi(`/api/prices/fragrances/${encodeURIComponent(fragranceId)}/alerts/${encodeURIComponent(variantKey)}`, {method: 'DELETE'});
      const alerts = await loadAlerts(fragranceId, true);
      renderAlertPanel(section, fragranceId, variantKey, findAlert(alerts, variantKey));
    } catch (deleteError) {
      renderAlertPanel(section, fragranceId, variantKey, alert, deleteError.message);
    }
  });
}

async function enhancePriceAlert() {
  ensureAlertStyles();
  const fragranceId = alertFragranceId();
  const section = document.querySelector('.catalog-price-monitoring');
  const activeVariant = section?.querySelector('[data-variant-key].active');
  const variantKey = activeVariant?.dataset.variantKey || '';
  if (!fragranceId || !section || !variantKey) return;
  if (section.dataset.priceAlertEnhanced === variantKey && section.querySelector('.catalog-price-alert')) return;

  section.dataset.priceAlertEnhanced = variantKey;
  const loading = document.createElement('section');
  loading.className = 'catalog-price-alert';
  loading.innerHTML = '<div class="catalog-price-alert-loading">Preisalarm wird geladen …</div>';
  section.appendChild(loading);

  try {
    const alerts = await loadAlerts(fragranceId);
    const currentSection = document.querySelector('.catalog-price-monitoring');
    const currentKey = currentSection?.querySelector('[data-variant-key].active')?.dataset.variantKey;
    if (currentSection !== section || currentKey !== variantKey) return;
    renderAlertPanel(section, fragranceId, variantKey, findAlert(alerts, variantKey));
  } catch (error) {
    renderAlertPanel(section, fragranceId, variantKey, null, error.message);
  }
}

ensureAlertStyles();
enhancePriceAlert();
new MutationObserver(enhancePriceAlert).observe(document.documentElement, {childList: true, subtree: true});
window.addEventListener('popstate', () => {
  alertCache.clear();
  enhancePriceAlert();
});
