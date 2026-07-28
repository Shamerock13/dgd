const euro = new Intl.NumberFormat('de-DE', {style: 'currency', currency: 'EUR'});
let panel;
let retailers = [];
let fragrances = [];

function esc(value) {
  return String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: {'Content-Type': 'application/json', ...(options.headers || {})},
    ...options,
  });
  if (!response.ok) {
    let message = `Fehler ${response.status}`;
    try { const body = await response.json(); message = body.detail || message; } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function field(label, input) {
  return `<label class="price-field"><span>${label}</span>${input}</label>`;
}

function render() {
  if (!panel) return;
  panel.innerHTML = `
    <section class="price-admin-head">
      <div><span>Preisbeobachtung 1.0</span><h2>Händler & Testangebote</h2><p>Die Standardhändler werden automatisch angelegt. Hier kannst du weitere Händler ergänzen und erste Preisbeobachtungen erfassen.</p></div>
      <button type="button" class="price-refresh">Aktualisieren</button>
    </section>
    <div class="price-admin-grid">
      <section class="price-card">
        <h3>Händler</h3>
        <form class="price-retailer-form">
          ${field('Name', '<input name="name" required minlength="2" placeholder="z. B. Händlername">')}
          ${field('Basis-URL', '<input name="base_url" type="url" placeholder="https://…">')}
          <button class="primary" type="submit">Händler anlegen</button>
        </form>
        <div class="price-retailer-list">
          ${retailers.length ? retailers.map(row => `<article><div><b>${esc(row.name)}</b><span>${esc(row.base_url || 'Keine URL')}</span></div><em class="${row.active ? 'active' : ''}">${row.active ? 'Aktiv' : 'Inaktiv'}</em></article>`).join('') : '<p>Noch keine Händler vorhanden.</p>'}
        </div>
      </section>
      <section class="price-card">
        <h3>Preisprüfung erfassen</h3>
        <form class="price-offer-form">
          ${field('Duft', `<select name="fragrance_id" required><option value="">Bitte wählen</option>${fragrances.map(row => `<option value="${row.id}">${esc(row.brand?.name)} – ${esc(row.name)}</option>`).join('')}</select>`)}
          ${field('Händler', `<select name="retailer_id" required><option value="">Bitte wählen</option>${retailers.filter(row => row.active).map(row => `<option value="${row.id}">${esc(row.name)}</option>`).join('')}</select>`)}
          ${field('Produkt-URL', '<input name="product_url" type="url" required placeholder="https://…">')}
          <div class="price-two">${field('Größe in ml', '<input name="size_ml" type="number" min="0.1" max="5000" step="0.1">')}${field('Produktart', '<select name="product_type"><option value="bottle">Flakon</option><option value="tester">Tester</option><option value="set">Set</option><option value="sample">Probe</option><option value="refill">Refill</option></select>')}</div>
          <div class="price-two">${field('Preis', '<input name="price_eur" type="number" min="0.01" step="0.01" required>')}${field('Versand', '<input name="shipping_eur" type="number" min="0" step="0.01" value="0">')}</div>
          ${field('Produktname', '<input name="product_name" placeholder="optional">')}
          <label class="price-check"><input name="in_stock" type="checkbox" checked> Aktuell lieferbar</label>
          <button class="primary" type="submit">Preis speichern</button>
        </form>
        <div class="price-result"></div>
      </section>
    </div>`;

  panel.querySelector('.price-refresh').addEventListener('click', load);
  panel.querySelector('.price-retailer-form').addEventListener('submit', createRetailer);
  panel.querySelector('.price-offer-form').addEventListener('submit', saveOffer);
}

async function load() {
  try {
    [retailers, fragrances] = await Promise.all([
      request('/api/prices/retailers'),
      request('/api/fragrances'),
    ]);
    render();
  } catch (error) {
    panel.innerHTML = `<div class="price-error">${esc(error.message)}</div>`;
  }
}

async function createRetailer(event) {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget));
  try {
    await request('/api/prices/retailers', {method: 'POST', body: JSON.stringify({name: data.name, base_url: data.base_url || null, active: true})});
    await load();
  } catch (error) { window.alert(error.message); }
}

async function saveOffer(event) {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget));
  const payload = {
    fragrance_id: data.fragrance_id,
    retailer_id: data.retailer_id,
    product_url: data.product_url,
    product_name: data.product_name || null,
    size_ml: data.size_ml ? Number(data.size_ml) : null,
    product_type: data.product_type,
    price_eur: Number(data.price_eur),
    shipping_eur: Number(data.shipping_eur || 0),
    in_stock: event.currentTarget.elements.in_stock.checked,
  };
  try {
    const result = await request('/api/prices/offers/check', {method: 'POST', body: JSON.stringify(payload)});
    const target = panel.querySelector('.price-result');
    target.innerHTML = `<b>Gespeichert</b><span>${esc(result.offer.retailer.name)} · ${euro.format(result.offer.total_eur)}${result.offer.price_per_100ml_eur != null ? ` · ${euro.format(result.offer.price_per_100ml_eur)} / 100 ml` : ''}</span>`;
    event.currentTarget.reset();
    event.currentTarget.elements.shipping_eur.value = '0';
    event.currentTarget.elements.in_stock.checked = true;
  } catch (error) { window.alert(error.message); }
}

function enhance() {
  const tabs = document.querySelector('.admin-tabs');
  if (!tabs || tabs.dataset.pricesEnhanced === 'true') return;
  tabs.dataset.pricesEnhanced = 'true';
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'price-admin-tab';
  button.textContent = 'Preise & Händler';
  tabs.appendChild(button);

  button.addEventListener('click', () => {
    tabs.querySelectorAll('button').forEach(item => item.classList.remove('active'));
    button.classList.add('active');
    const main = tabs.closest('.admin-main');
    [...main.children].forEach(child => {
      if (child !== tabs && !child.classList.contains('admin-head') && !child.classList.contains('price-admin-panel')) child.hidden = true;
    });
    panel = main.querySelector('.price-admin-panel');
    if (!panel) {
      panel = document.createElement('section');
      panel.className = 'price-admin-panel';
      main.appendChild(panel);
    }
    panel.hidden = false;
    panel.innerHTML = '<div class="price-loading">Preisdaten werden geladen …</div>';
    load();
  });

  tabs.addEventListener('click', event => {
    if (event.target === button || event.target.closest('.price-admin-tab')) return;
    if (panel) panel.hidden = true;
    const main = tabs.closest('.admin-main');
    [...main.children].forEach(child => {
      if (child !== tabs && !child.classList.contains('admin-head') && !child.classList.contains('price-admin-panel')) child.hidden = false;
    });
  }, true);
}

enhance();
new MutationObserver(enhance).observe(document.documentElement, {childList: true, subtree: true});
