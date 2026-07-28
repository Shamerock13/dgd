const euro = new Intl.NumberFormat('de-DE', {style:'currency', currency:'EUR'});

let activeFragranceId = null;
let requestToken = 0;

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

function ensureStyles() {
  if (document.getElementById('catalog-live-price-styles')) return;
  const style = document.createElement('style');
  style.id = 'catalog-live-price-styles';
  style.textContent = `
    .catalog-live-price-link{display:inline-flex;align-items:center;gap:.35rem;margin-top:.45rem;color:#d9a85f;text-decoration:none;font-weight:700}
    .catalog-live-price-link:hover{text-decoration:underline}
    .catalog-live-price-meta{display:block;margin-top:.3rem;color:#aaa;font-size:.82rem;line-height:1.35}
    .catalog-live-offers{grid-column:1/-1;margin-top:1.25rem;padding:1rem 1.1rem;border:1px solid rgba(255,255,255,.12);border-radius:14px;background:rgba(255,255,255,.025)}
    .catalog-live-offers h3{margin:0 0 .75rem;font-size:1rem}
    .catalog-live-offer-list{display:grid;gap:.65rem}
    .catalog-live-offer{display:flex;justify-content:space-between;gap:1rem;align-items:center;padding:.75rem;border:1px solid rgba(255,255,255,.09);border-radius:11px}
    .catalog-live-offer div{display:grid;gap:.2rem}.catalog-live-offer small{color:#aaa}.catalog-live-offer b{font-size:1rem}
    .catalog-live-offer a{color:#d9a85f;text-decoration:none;font-weight:700;white-space:nowrap}
    @media(max-width:700px){.catalog-live-offer{align-items:flex-start;flex-direction:column}}
  `;
  document.head.appendChild(style);
}

function renderPrice(data, fragranceId) {
  if (currentFragranceId() !== fragranceId) return;
  const detail = document.querySelector('.catalog-detail');
  const facts = detail?.querySelector('.detail-facts');
  const priceFact = facts?.firstElementChild;
  if (!detail || !facts || !priceFact) return;

  detail.querySelector('.catalog-live-offers')?.remove();
  priceFact.querySelector('.catalog-live-price-link')?.remove();
  priceFact.querySelector('.catalog-live-price-meta')?.remove();

  const cheapest = data?.cheapest;
  if (!cheapest) return;

  const value = priceFact.querySelector('b');
  if (value) value.textContent = euro.format(cheapest.total_eur);
  const label = priceFact.querySelector('span');
  if (label) label.textContent = 'Günstigster Händlerpreis';

  const meta = document.createElement('small');
  meta.className = 'catalog-live-price-meta';
  const parts = [cheapest.retailer?.name];
  if (cheapest.size_ml) parts.push(`${cheapest.size_ml} ml`);
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

  const offers = (data.offers || []).filter(row => row.in_stock);
  if (!offers.length) return;
  const section = document.createElement('section');
  section.className = 'catalog-live-offers';
  section.innerHTML = `<h3>Aktuelle Händlerangebote</h3><div class="catalog-live-offer-list">${offers.map(row => {
    const details = [row.size_ml ? `${row.size_ml} ml` : null, row.shipping_eur > 0 ? `${euro.format(row.shipping_eur)} Versand` : 'versandkostenfrei', row.price_per_100ml_eur != null ? `${euro.format(row.price_per_100ml_eur)} / 100 ml` : null].filter(Boolean).join(' · ');
    return `<article class="catalog-live-offer"><div><small>${escapeHtml(row.retailer?.name)}</small><b>${euro.format(row.total_eur)}</b><span>${escapeHtml(details)}</span></div><a href="${escapeHtml(row.product_url)}" target="_blank" rel="noreferrer">Zum Angebot ↗</a></article>`;
  }).join('')}</div>`;
  detail.appendChild(section);
}

async function enhanceLivePrice() {
  ensureStyles();
  const fragranceId = currentFragranceId();
  if (!fragranceId) {
    activeFragranceId = null;
    return;
  }
  const detail = document.querySelector('.catalog-detail');
  if (!detail) return;
  if (activeFragranceId === fragranceId && detail.dataset.livePricesLoaded === 'true') return;

  activeFragranceId = fragranceId;
  detail.dataset.livePricesLoaded = 'true';
  const token = ++requestToken;
  try {
    const response = await fetch(`/api/prices/fragrances/${encodeURIComponent(fragranceId)}?days=90`);
    if (!response.ok) throw new Error(`Fehler ${response.status}`);
    const data = await response.json();
    if (token === requestToken) renderPrice(data, fragranceId);
  } catch (error) {
    console.warn('DGD Händlerpreise konnten nicht geladen werden:', error);
  }
}

const observer = new MutationObserver(enhanceLivePrice);
observer.observe(document.documentElement, {childList:true, subtree:true});
window.addEventListener('popstate', enhanceLivePrice);
const originalPushState = history.pushState.bind(history);
history.pushState = (...args) => { originalPushState(...args); queueMicrotask(enhanceLivePrice); };
const originalReplaceState = history.replaceState.bind(history);
history.replaceState = (...args) => { originalReplaceState(...args); queueMicrotask(enhanceLivePrice); };
enhanceLivePrice();
