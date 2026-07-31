const euro = new Intl.NumberFormat('de-DE', {style:'currency', currency:'EUR'});
const priceDate = new Intl.DateTimeFormat('de-DE', {dateStyle:'medium'});
const priceDateTime = new Intl.DateTimeFormat('de-DE', {dateStyle:'short', timeStyle:'short'});

let activeFragranceId = null;
let requestToken = 0;
let selectedVariantKey = null;
let selectedHistoryDays = 90;
let currentPriceData = null;

function currentFragranceId() {
  return new URLSearchParams(window.location.search).get('fragrance') || '';
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function numberValue(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function typeLabel(value) {
  return ({
    bottle: 'Flakon',
    tester: 'Tester',
    set: 'Set',
    sample: 'Probe',
    refill: 'Nachfüllung',
  })[value] || 'Sonstige Variante';
}

function concentrationLabel(value) {
  if (!value) return 'Konzentration offen';
  return String(value).replace(/\b\w/g, char => char.toUpperCase());
}

function variantLabel(row) {
  return [
    typeLabel(row.product_type),
    row.size_ml ? `${row.size_ml} ml` : 'Größe offen',
    concentrationLabel(row.concentration),
  ].join(' · ');
}

function formattedDate(value, withTime = false) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unbekannt';
  return withTime ? priceDateTime.format(date) : priceDate.format(date);
}

function ensureStyles() {
  if (document.getElementById('catalog-live-price-styles')) return;
  const style = document.createElement('style');
  style.id = 'catalog-live-price-styles';
  style.textContent = `
    .catalog-live-price-link{display:inline-flex;align-items:center;gap:.35rem;margin-top:.45rem;color:#d9a85f;text-decoration:none;font-weight:700}
    .catalog-live-price-link:hover{text-decoration:underline}
    .catalog-live-price-meta{display:block;margin-top:.3rem;color:#aaa;font-size:.82rem;line-height:1.35}
    .catalog-price-monitoring{grid-column:1/-1;margin-top:1.25rem;padding:1.15rem;border:1px solid rgba(255,255,255,.12);border-radius:16px;background:rgba(255,255,255,.025);display:grid;gap:1rem}
    .catalog-price-head{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem}
    .catalog-price-head h3{margin:0 0 .25rem;font-size:1.08rem}.catalog-price-head p{margin:0;color:#aaa;font-size:.86rem}
    .catalog-price-periods,.catalog-price-variants{display:flex;flex-wrap:wrap;gap:.5rem}
    .catalog-price-periods button,.catalog-price-variants button{border:1px solid rgba(255,255,255,.14);border-radius:999px;background:rgba(255,255,255,.035);color:inherit;padding:.48rem .72rem;cursor:pointer;font:inherit;font-size:.82rem}
    .catalog-price-periods button.active,.catalog-price-variants button.active{border-color:#d9a85f;background:rgba(217,168,95,.13);color:#f6d7a8}
    .catalog-price-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem}
    .catalog-price-summary article{padding:.75rem .8rem;border:1px solid rgba(255,255,255,.09);border-radius:11px;background:rgba(255,255,255,.025);display:grid;gap:.2rem}
    .catalog-price-summary small{color:#aaa}.catalog-price-summary b{font-size:1rem}.catalog-price-summary span{font-size:.78rem;color:#aaa}
    .catalog-price-warning{padding:.75rem .85rem;border:1px solid rgba(255,180,0,.3);border-radius:11px;background:rgba(255,180,0,.08);font-size:.84rem;line-height:1.4}
    .catalog-price-chart-wrap{position:relative;min-height:230px;padding:.5rem .35rem .15rem;border:1px solid rgba(255,255,255,.08);border-radius:12px;background:rgba(0,0,0,.12)}
    .catalog-price-chart{display:block;width:100%;height:auto;min-height:220px;overflow:visible}
    .catalog-price-chart-grid{stroke:rgba(255,255,255,.09);stroke-width:1}.catalog-price-chart-label{fill:#999;font-size:12px}
    .catalog-price-chart-area{fill:rgba(217,168,95,.1)}.catalog-price-chart-line{fill:none;stroke:#d9a85f;stroke-width:3;stroke-linejoin:round;stroke-linecap:round}
    .catalog-price-chart-point{fill:#171513;stroke:#e5b36c;stroke-width:2}
    .catalog-price-chart-empty{min-height:220px;display:grid;place-items:center;text-align:center;color:#999;padding:1rem}
    .catalog-live-offer-list{display:grid;gap:.65rem}
    .catalog-live-offer{display:flex;justify-content:space-between;gap:1rem;align-items:center;padding:.78rem;border:1px solid rgba(255,255,255,.09);border-radius:11px}
    .catalog-live-offer.out-of-stock{opacity:.62}.catalog-live-offer div{display:grid;gap:.2rem}.catalog-live-offer small{color:#aaa}.catalog-live-offer b{font-size:1rem}.catalog-live-offer span{font-size:.82rem;color:#bbb}
    .catalog-live-offer a{color:#d9a85f;text-decoration:none;font-weight:700;white-space:nowrap}.catalog-live-offer a:hover{text-decoration:underline}
    .catalog-price-offer-head{display:flex;align-items:baseline;justify-content:space-between;gap:1rem}.catalog-price-offer-head h4{margin:0}.catalog-price-offer-head span{color:#aaa;font-size:.8rem}
    @media(max-width:900px){.catalog-price-summary{grid-template-columns:repeat(2,minmax(0,1fr))}}
    @media(max-width:700px){.catalog-price-head{display:grid}.catalog-live-offer{align-items:flex-start;flex-direction:column}.catalog-price-summary{grid-template-columns:1fr 1fr}.catalog-price-monitoring{padding:.9rem}}
    @media(max-width:430px){.catalog-price-summary{grid-template-columns:1fr}}
  `;
  document.head.appendChild(style);
}

function rememberEditorialPrice(priceFact) {
  if (priceFact.dataset.editorialPriceRemembered === 'true') return;
  priceFact.dataset.editorialPriceRemembered = 'true';
  priceFact.dataset.editorialPriceValue = priceFact.querySelector('b')?.textContent || '';
  priceFact.dataset.editorialPriceLabel = priceFact.querySelector('span')?.textContent || '';
}

function restoreEditorialPrice(priceFact) {
  const value = priceFact.querySelector('b');
  const label = priceFact.querySelector('span');
  if (value && priceFact.dataset.editorialPriceValue != null) value.textContent = priceFact.dataset.editorialPriceValue;
  if (label && priceFact.dataset.editorialPriceLabel != null) label.textContent = priceFact.dataset.editorialPriceLabel;
  priceFact.querySelector('.catalog-live-price-link')?.remove();
  priceFact.querySelector('.catalog-live-price-meta')?.remove();
}

function selectedVariant(data) {
  const variants = data?.variants || [];
  let selected = variants.find(row => row.variant_key === selectedVariantKey);
  if (!selected) {
    selectedVariantKey = data?.default_variant_key || variants[0]?.variant_key || null;
    selected = variants.find(row => row.variant_key === selectedVariantKey) || variants[0] || null;
  }
  return selected;
}

function renderPriceFact(priceFact, variant) {
  rememberEditorialPrice(priceFact);
  restoreEditorialPrice(priceFact);
  const cheapest = variant?.cheapest;
  if (!cheapest) return;

  const value = priceFact.querySelector('b');
  if (value) value.textContent = euro.format(cheapest.total_eur);
  const label = priceFact.querySelector('span');
  if (label) label.textContent = 'Günstigster Variantenpreis';

  const meta = document.createElement('small');
  meta.className = 'catalog-live-price-meta';
  const parts = [variantLabel(variant), cheapest.retailer?.name];
  if (cheapest.shipping_eur > 0) parts.push(`inkl. ${euro.format(cheapest.shipping_eur)} Versand`);
  if (cheapest.price_per_100ml_eur != null) parts.push(`${euro.format(cheapest.price_per_100ml_eur)} / 100 ml`);
  meta.textContent = parts.filter(Boolean).join(' · ');
  priceFact.appendChild(meta);

  const link = document.createElement('a');
  link.className = 'catalog-live-price-link';
  link.href = cheapest.product_url;
  link.target = '_blank';
  link.rel = 'noreferrer';
  link.textContent = `Bei ${cheapest.retailer?.name || 'Händler'} ansehen ↗`;
  priceFact.appendChild(link);
}

function chartSvg(points) {
  if (!points?.length) {
    return '<div class="catalog-price-chart-empty">Für diesen Zeitraum liegen noch keine lieferbaren Preisbeobachtungen vor.</div>';
  }

  const width = 760;
  const height = 250;
  const left = 66;
  const right = 18;
  const top = 18;
  const bottom = 38;
  const values = points.map(row => numberValue(row.total_eur)).filter(value => value != null);
  if (!values.length) return '<div class="catalog-price-chart-empty">Die vorhandenen Preiswerte konnten nicht dargestellt werden.</div>';

  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const rawSpread = Math.max(rawMax - rawMin, rawMax * .04, 1);
  const minValue = Math.max(0, rawMin - rawSpread * .2);
  const maxValue = rawMax + rawSpread * .2;
  const valueSpread = Math.max(maxValue - minValue, 1);
  const timestamps = points.map(row => new Date(`${row.date}T12:00:00`).getTime());
  const minTime = Math.min(...timestamps);
  const maxTime = Math.max(...timestamps);
  const timeSpread = Math.max(maxTime - minTime, 1);

  const positioned = points.map((row, index) => {
    const timestamp = timestamps[index];
    const x = points.length === 1
      ? (left + width - right) / 2
      : left + ((timestamp - minTime) / timeSpread) * (width - left - right);
    const y = top + ((maxValue - Number(row.total_eur)) / valueSpread) * (height - top - bottom);
    return {...row, x, y};
  });
  const line = positioned.map((row, index) => `${index ? 'L' : 'M'} ${row.x.toFixed(2)} ${row.y.toFixed(2)}`).join(' ');
  const area = `${line} L ${positioned[positioned.length - 1].x.toFixed(2)} ${(height - bottom).toFixed(2)} L ${positioned[0].x.toFixed(2)} ${(height - bottom).toFixed(2)} Z`;
  const grid = [0, 1, 2, 3].map(index => {
    const ratio = index / 3;
    const value = maxValue - ratio * valueSpread;
    const y = top + ratio * (height - top - bottom);
    return `<line class="catalog-price-chart-grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"></line><text class="catalog-price-chart-label" x="${left - 8}" y="${y + 4}" text-anchor="end">${escapeHtml(euro.format(value))}</text>`;
  }).join('');
  const pointMarkup = positioned.map(row => `<circle class="catalog-price-chart-point" cx="${row.x}" cy="${row.y}" r="4"><title>${escapeHtml(`${formattedDate(row.date)} · ${euro.format(row.total_eur)} · ${row.retailer}`)}</title></circle>`).join('');
  const firstDate = formattedDate(points[0].date);
  const lastDate = formattedDate(points[points.length - 1].date);

  return `<svg class="catalog-price-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Preisverlauf von ${escapeHtml(firstDate)} bis ${escapeHtml(lastDate)}">
    ${grid}
    <path class="catalog-price-chart-area" d="${area}"></path>
    <path class="catalog-price-chart-line" d="${line}"></path>
    ${pointMarkup}
    <text class="catalog-price-chart-label" x="${left}" y="${height - 10}">${escapeHtml(firstDate)}</text>
    <text class="catalog-price-chart-label" x="${width - right}" y="${height - 10}" text-anchor="end">${escapeHtml(lastDate)}</text>
  </svg>`;
}

function differenceText(variant) {
  const difference = numberValue(variant?.difference_from_low_eur);
  if (difference == null) return {value: 'Noch offen', note: 'Kein historischer Vergleich'};
  if (Math.abs(difference) < .01) return {value: 'Am Tiefpreis', note: 'Aktuell historisch günstig'};
  const percent = numberValue(variant.difference_from_low_percent);
  return {
    value: `+${euro.format(difference)}`,
    note: percent == null ? 'über dem Tiefpreis' : `${percent.toLocaleString('de-DE')} % über dem Tiefpreis`,
  };
}

function offersMarkup(variant) {
  const offers = variant?.offers || [];
  if (!offers.length) return '<div class="catalog-price-chart-empty">Für diese Variante sind noch keine Händlerangebote vorhanden.</div>';
  return `<div class="catalog-live-offer-list">${offers.map(row => {
    const details = [
      row.shipping_eur > 0 ? `${euro.format(row.shipping_eur)} Versand` : 'versandkostenfrei',
      row.price_per_100ml_eur != null ? `${euro.format(row.price_per_100ml_eur)} / 100 ml` : null,
      row.product_variant || null,
      row.in_stock ? 'lieferbar' : 'aktuell nicht lieferbar',
      row.checked_at ? `geprüft ${formattedDate(row.checked_at, true)}` : null,
    ].filter(Boolean).join(' · ');
    return `<article class="catalog-live-offer ${row.in_stock ? '' : 'out-of-stock'}"><div><small>${escapeHtml(row.retailer?.name)}</small><b>${euro.format(row.total_eur)}</b><span>${escapeHtml(details)}</span></div><a href="${escapeHtml(row.product_url)}" target="_blank" rel="noreferrer">Zum Angebot ↗</a></article>`;
  }).join('')}</div>`;
}

function renderMonitoring(detail, data, variant) {
  detail.querySelector('.catalog-price-monitoring')?.remove();
  if (!variant) return;

  const difference = differenceText(variant);
  const variantButtons = (data.variants || []).map(row => `<button type="button" data-variant-key="${escapeHtml(row.variant_key)}" class="${row.variant_key === variant.variant_key ? 'active' : ''}">${escapeHtml(variantLabel(row))}${row.available_offers ? ` · ${row.available_offers}` : ''}</button>`).join('');
  const periodButtons = [30, 90, 365].map(days => `<button type="button" data-history-days="${days}" class="${selectedHistoryDays === days ? 'active' : ''}">${days} Tage</button>`).join('');
  const missing = variant.missing_variant_fields || [];
  const warning = missing.length
    ? `<div class="catalog-price-warning"><b>Variante noch nicht vollständig bestimmt.</b> ${missing.includes('size_ml') ? 'Die Größe fehlt. ' : ''}${missing.includes('concentration') ? 'Die Konzentration fehlt. ' : ''}Diese Gruppe wird deshalb nicht mit vollständig bestimmten Varianten vermischt.</div>`
    : '';

  const section = document.createElement('section');
  section.className = 'catalog-price-monitoring';
  section.innerHTML = `
    <div class="catalog-price-head">
      <div><h3>Preisvergleich & Verlauf</h3><p>${escapeHtml(variantLabel(variant))} · nur direkt vergleichbare Angebote</p></div>
      <div class="catalog-price-periods" aria-label="Zeitraum wählen">${periodButtons}</div>
    </div>
    <div class="catalog-price-variants" aria-label="Produktvariante wählen">${variantButtons}</div>
    ${warning}
    <div class="catalog-price-summary">
      <article><small>Aktuell günstigster Preis</small><b>${variant.cheapest ? euro.format(variant.cheapest.total_eur) : 'Nicht lieferbar'}</b><span>${variant.cheapest ? escapeHtml(variant.cheapest.retailer?.name) : 'Kein verfügbares Angebot'}</span></article>
      <article><small>Historisches Tief</small><b>${variant.historic_low_total_eur != null ? euro.format(variant.historic_low_total_eur) : 'Noch offen'}</b><span>für genau diese Variante</span></article>
      <article><small>Abstand zum Tief</small><b>${escapeHtml(difference.value)}</b><span>${escapeHtml(difference.note)}</span></article>
      <article><small>Zuletzt geprüft</small><b>${variant.last_checked_at ? escapeHtml(formattedDate(variant.last_checked_at, true)) : 'Noch nie'}</b><span>${variant.available_offers} von ${variant.checked_offers} Angeboten lieferbar</span></article>
    </div>
    <div class="catalog-price-chart-wrap">${chartSvg(variant.daily_best_history || [])}</div>
    <div class="catalog-price-offer-head"><h4>Händlerangebote</h4><span>sortiert nach Gesamtpreis inklusive Versand</span></div>
    ${offersMarkup(variant)}
  `;
  detail.appendChild(section);

  section.querySelectorAll('[data-variant-key]').forEach(button => button.addEventListener('click', () => {
    selectedVariantKey = button.dataset.variantKey;
    renderPrice(currentPriceData, currentFragranceId());
  }));
  section.querySelectorAll('[data-history-days]').forEach(button => button.addEventListener('click', () => {
    const days = Number(button.dataset.historyDays);
    if (!Number.isFinite(days) || days === selectedHistoryDays) return;
    selectedHistoryDays = days;
    loadLivePrice(currentFragranceId(), true);
  }));
}

function renderPrice(data, fragranceId) {
  if (currentFragranceId() !== fragranceId) return;
  const detail = document.querySelector('.catalog-detail');
  const facts = detail?.querySelector('.detail-facts');
  const priceFact = facts?.firstElementChild;
  if (!detail || !facts || !priceFact) return;

  currentPriceData = data;
  const variant = selectedVariant(data);
  renderPriceFact(priceFact, variant);
  renderMonitoring(detail, data, variant);
}

async function loadLivePrice(fragranceId, force = false) {
  ensureStyles();
  if (!fragranceId) return;
  const detail = document.querySelector('.catalog-detail');
  if (!detail) return;
  if (!force && activeFragranceId === fragranceId && detail.dataset.livePricesLoaded === 'true') return;

  activeFragranceId = fragranceId;
  detail.dataset.livePricesLoaded = 'true';
  const token = ++requestToken;
  try {
    const response = await fetch(`/api/prices/fragrances/${encodeURIComponent(fragranceId)}?days=${selectedHistoryDays}`);
    if (!response.ok) throw new Error(`Fehler ${response.status}`);
    const data = await response.json();
    if (token === requestToken) renderPrice(data, fragranceId);
  } catch (error) {
    console.warn('DGD Händlerpreise konnten nicht geladen werden:', error);
  }
}

function enhanceLivePrice() {
  ensureStyles();
  const fragranceId = currentFragranceId();
  if (!fragranceId) {
    activeFragranceId = null;
    selectedVariantKey = null;
    currentPriceData = null;
    return;
  }
  if (activeFragranceId !== fragranceId) {
    selectedVariantKey = null;
    selectedHistoryDays = 90;
    currentPriceData = null;
  }
  loadLivePrice(fragranceId);
}

const observer = new MutationObserver(enhanceLivePrice);
observer.observe(document.documentElement, {childList:true, subtree:true});
window.addEventListener('popstate', enhanceLivePrice);
const originalPushState = history.pushState.bind(history);
history.pushState = (...args) => { originalPushState(...args); queueMicrotask(enhanceLivePrice); };
const originalReplaceState = history.replaceState.bind(history);
history.replaceState = (...args) => { originalReplaceState(...args); queueMicrotask(enhanceLivePrice); };
enhanceLivePrice();
