const euro = new Intl.NumberFormat('de-DE', {style: 'currency', currency: 'EUR'});
let panel;
let retailers = [];
let fragrances = [];
let discovery = null;

function esc(value) {
  return String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');
}

async function request(url, options = {}) {
  const response = await fetch(url, {headers: {'Content-Type': 'application/json', ...(options.headers || {})}, ...options});
  if (!response.ok) {
    let message = `Fehler ${response.status}`;
    try { const body = await response.json(); message = body.detail || message; } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function field(label, input) { return `<label class="price-field"><span>${label}</span>${input}</label>`; }

function discoveryHtml() {
  if (!discovery) return '<p class="price-discovery-empty">Wähle einen Duft und starte die Händlersuche.</p>';
  const rows = discovery.results.flatMap(group => group.candidates.map(candidate => ({...candidate, retailer: group.retailer, retailer_id: group.retailer_id})));
  if (!rows.length) return `<div class="price-error">Keine ausreichend sicheren Treffer gefunden. Einzelne Händler können Suchseiten technisch blockieren.</div>`;
  return `<div class="price-discovery-list">${rows.map((row,index)=>`
    <article>
      <div><small>${esc(row.retailer)} · Trefferwert ${row.score}%</small><b>${esc(row.title)}</b><a href="${esc(row.product_url)}" target="_blank" rel="noreferrer">Produktseite prüfen</a></div>
      <button type="button" class="primary price-accept" data-index="${index}">Übernehmen</button>
    </article>`).join('')}</div>`;
}

function render() {
  if (!panel) return;
  panel.innerHTML = `
    <section class="price-admin-head"><div><span>Preisbeobachtung 1.1</span><h2>Händler, Suche & Angebote</h2><p>DGD kann Händlerseiten nach passenden Produkten durchsuchen. Treffer werden erst nach deiner Bestätigung übernommen.</p></div><button type="button" class="price-refresh">Aktualisieren</button></section>
    <section class="price-card price-discovery-card">
      <h3>Händler automatisch durchsuchen</h3>
      <form class="price-discovery-form">
        ${field('Duft', `<select name="fragrance_id" required><option value="">Bitte wählen</option>${fragrances.map(row => `<option value="${row.id}">${esc(row.brand?.name)} – ${esc(row.name)}</option>`).join('')}</select>`)}
        <button class="primary" type="submit">Bei allen Händlern suchen</button>
      </form>
      <div class="price-discovery-results">${discoveryHtml()}</div>
    </section>
    <div class="price-admin-grid">
      <section class="price-card"><h3>Händler</h3><form class="price-retailer-form">${field('Name', '<input name="name" required minlength="2" placeholder="z. B. Händlername">')}${field('Basis-URL', '<input name="base_url" type="url" placeholder="https://…">')}<button class="primary" type="submit">Händler anlegen</button></form><div class="price-retailer-list">${retailers.length ? retailers.map(row => `<article><div><b>${esc(row.name)}</b><span>${esc(row.base_url || 'Keine URL')}</span></div><em class="${row.active ? 'active' : ''}">${row.active ? 'Aktiv' : 'Inaktiv'}</em></article>`).join('') : '<p>Noch keine Händler vorhanden.</p>'}</div></section>
      <section class="price-card"><h3>Preisprüfung manuell erfassen</h3><form class="price-offer-form">${field('Duft', `<select name="fragrance_id" required><option value="">Bitte wählen</option>${fragrances.map(row => `<option value="${row.id}">${esc(row.brand?.name)} – ${esc(row.name)}</option>`).join('')}</select>`)}${field('Händler', `<select name="retailer_id" required><option value="">Bitte wählen</option>${retailers.filter(row => row.active).map(row => `<option value="${row.id}">${esc(row.name)}</option>`).join('')}</select>`)}${field('Produkt-URL', '<input name="product_url" type="url" required placeholder="https://…">')}<div class="price-two">${field('Größe in ml', '<input name="size_ml" type="number" min="0.1" max="5000" step="0.1">')}${field('Produktart', '<select name="product_type"><option value="bottle">Flakon</option><option value="tester">Tester</option><option value="set">Set</option><option value="sample">Probe</option><option value="refill">Refill</option></select>')}</div><div class="price-two">${field('Preis', '<input name="price_eur" type="number" min="0.01" step="0.01" required>')}${field('Versand', '<input name="shipping_eur" type="number" min="0" step="0.01" value="0">')}</div>${field('Produktname', '<input name="product_name" placeholder="optional">')}<label class="price-check"><input name="in_stock" type="checkbox" checked> Aktuell lieferbar</label><button class="primary" type="submit">Preis speichern</button></form><div class="price-result"></div></section>
    </div>`;

  panel.querySelector('.price-refresh').addEventListener('click', load);
  panel.querySelector('.price-retailer-form').addEventListener('submit', createRetailer);
  panel.querySelector('.price-offer-form').addEventListener('submit', saveOffer);
  panel.querySelector('.price-discovery-form').addEventListener('submit', runDiscovery);
  panel.querySelectorAll('.price-accept').forEach(button => button.addEventListener('click', acceptCandidate));
}

async function load() {
  try {
    [retailers, fragrances] = await Promise.all([request('/api/prices/retailers'), request('/api/fragrances')]);
    render();
  } catch (error) { panel.innerHTML = `<div class="price-error">${esc(error.message)}</div>`; }
}

async function runDiscovery(event) {
  event.preventDefault();
  const fragrance_id = new FormData(event.currentTarget).get('fragrance_id');
  const results = panel.querySelector('.price-discovery-results');
  results.innerHTML = '<div class="price-loading">Händler werden durchsucht …</div>';
  try { discovery = await request('/api/prices/discovery/search', {method:'POST', body:JSON.stringify({fragrance_id})}); render(); }
  catch(error) { results.innerHTML = `<div class="price-error">${esc(error.message)}</div>`; }
}

async function acceptCandidate(event) {
  const rows = discovery.results.flatMap(group => group.candidates.map(candidate => ({...candidate, retailer_id:group.retailer_id})));
  const row = rows[Number(event.currentTarget.dataset.index)];
  const fragrance_id = panel.querySelector('.price-discovery-form [name="fragrance_id"]').value;
  const size = prompt('Größe in ml (optional):', '100');
  if (size === null) return;
  event.currentTarget.disabled = true;
  event.currentTarget.textContent = 'Prüfe …';
  try {
    const result = await request('/api/prices/discovery/accept', {method:'POST', body:JSON.stringify({fragrance_id, retailer_id:row.retailer_id, product_url:row.product_url, size_ml:size?Number(size):null, product_type:'bottle', shipping_eur:0})});
    alert(`${result.retailer}: ${euro.format(result.total_eur)} wurde übernommen.`);
    event.currentTarget.textContent = 'Übernommen';
  } catch(error) { alert(error.message); event.currentTarget.disabled = false; event.currentTarget.textContent = 'Übernehmen'; }
}

async function createRetailer(event) {
  event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget));
  try { await request('/api/prices/retailers', {method:'POST', body:JSON.stringify({name:data.name, base_url:data.base_url||null, active:true})}); await load(); }
  catch(error) { alert(error.message); }
}

async function saveOffer(event) {
  event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget));
  const payload = {fragrance_id:data.fragrance_id, retailer_id:data.retailer_id, product_url:data.product_url, product_name:data.product_name||null, size_ml:data.size_ml?Number(data.size_ml):null, product_type:data.product_type, price_eur:Number(data.price_eur), shipping_eur:Number(data.shipping_eur||0), in_stock:event.currentTarget.elements.in_stock.checked};
  try { const result=await request('/api/prices/offers/check',{method:'POST',body:JSON.stringify(payload)}); panel.querySelector('.price-result').innerHTML=`<b>Gespeichert</b><span>${esc(result.offer.retailer.name)} · ${euro.format(result.offer.total_eur)}</span>`; event.currentTarget.reset(); }
  catch(error) { alert(error.message); }
}

function enhance() {
  const tabs=document.querySelector('.admin-tabs'); if(!tabs||tabs.dataset.pricesEnhanced==='true')return; tabs.dataset.pricesEnhanced='true';
  const button=document.createElement('button'); button.type='button'; button.className='price-admin-tab'; button.textContent='Preise & Händler'; tabs.appendChild(button);
  button.addEventListener('click',()=>{tabs.querySelectorAll('button').forEach(item=>item.classList.remove('active'));button.classList.add('active');const main=tabs.closest('.admin-main');[...main.children].forEach(child=>{if(child!==tabs&&!child.classList.contains('admin-head')&&!child.classList.contains('price-admin-panel'))child.hidden=true});panel=main.querySelector('.price-admin-panel');if(!panel){panel=document.createElement('section');panel.className='price-admin-panel';main.appendChild(panel)}panel.hidden=false;panel.innerHTML='<div class="price-loading">Preisdaten werden geladen …</div>';load()});
  tabs.addEventListener('click',event=>{if(event.target===button||event.target.closest('.price-admin-tab'))return;if(panel)panel.hidden=true;const main=tabs.closest('.admin-main');[...main.children].forEach(child=>{if(child!==tabs&&!child.classList.contains('admin-head')&&!child.classList.contains('price-admin-panel'))child.hidden=false})},true);
}

enhance();
new MutationObserver(enhance).observe(document.documentElement,{childList:true,subtree:true});
