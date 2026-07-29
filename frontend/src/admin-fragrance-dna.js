const DIMENSIONS = [
  ['fresh','Frisch'],['citrus','Zitrisch'],['green','Grün'],['aquatic','Aquatisch'],
  ['floral','Floral'],['fruity','Fruchtig'],['sweet','Süß'],['gourmand','Gourmandig'],
  ['spicy','Würzig'],['woody','Holzig'],['smoky','Rauchig'],['earthy','Erdig'],
  ['resinous','Harzig'],['leathery','Ledrig'],['powdery','Pudrig'],['animalic','Animalisch'],
];

const emptyValues = () => Object.fromEntries(DIMENSIONS.map(([key]) => [key, '']));
let activeFragranceId = '';
let renderToken = 0;

function toast(message) {
  let node = document.querySelector('.dna-admin-toast');
  if (!node) {
    node = document.createElement('div');
    node.className = 'dna-admin-toast';
    document.body.appendChild(node);
  }
  node.textContent = message;
  node.classList.add('show');
  clearTimeout(node._timer);
  node._timer = setTimeout(() => node.classList.remove('show'), 3200);
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: {'Content-Type':'application/json', ...(options.headers || {})},
    ...options,
  });
  if (!response.ok) {
    let message = `Fehler ${response.status}`;
    try { message = (await response.json()).detail || message; } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function getEditingFragranceId() {
  const title = [...document.querySelectorAll('.editor-title')].find(node => node.textContent.includes('Duft bearbeiten'));
  if (!title) return '';
  const form = title.closest('form');
  if (!form) return '';
  const cancel = title.querySelector('button');
  if (!cancel) return '';
  const list = form.parentElement?.querySelector('.admin-list');
  if (!list) return '';
  const name = form.querySelector('input[required]')?.value?.trim();
  const brand = form.querySelector('select[required] option:checked')?.textContent?.trim();
  const rows = [...list.querySelectorAll('.admin-row')];
  const row = rows.find(item => item.querySelector('b')?.textContent?.trim() === name && item.querySelector('small')?.textContent?.trim() === brand);
  const editButton = row?.querySelector('button');
  return editButton?.dataset?.fragranceId || row?.dataset?.fragranceId || '';
}

async function resolveFragranceId() {
  const direct = getEditingFragranceId();
  if (direct) return direct;
  const form = [...document.querySelectorAll('form.editor')].find(node => node.querySelector('.editor-title')?.textContent.includes('Duft bearbeiten'));
  if (!form) return '';
  const name = form.querySelector('input[required]')?.value?.trim();
  const brand = form.querySelector('select[required] option:checked')?.textContent?.trim();
  if (!name || !brand) return '';
  try {
    const rows = await request('/api/fragrances');
    return rows.find(item => item.name === name && item.brand?.name === brand)?.id || '';
  } catch {
    return '';
  }
}

function sliderMarkup(prefix, values) {
  return DIMENSIONS.map(([key,label]) => {
    const value = values[key] ?? '';
    return `<label class="dna-admin-slider">
      <span><b>${label}</b><output data-output-for="${prefix}-${key}">${value === '' ? 'offen' : Number(value).toFixed(1)}</output></span>
      <input data-dna-input="${prefix}" data-dimension="${key}" type="range" min="0" max="10" step="0.1" value="${value === '' ? 0 : value}">
      <button type="button" data-clear-dna="${prefix}-${key}">Wert leeren</button>
    </label>`;
  }).join('');
}

function editorMarkup(data) {
  const values = {...emptyValues(), ...(data.values || {})};
  const personal = {...emptyValues(), ...(data.personal_values || {})};
  const metadata = data.metadata || {};
  const count = Object.values(values).filter(value => value !== '' && value != null).length;
  const personalCount = Object.values(personal).filter(value => value !== '' && value != null).length;
  const date = metadata.researched_at ? String(metadata.researched_at).slice(0,16) : '';
  return `<section class="dna-admin-card" data-dna-admin-card>
    <div class="dna-admin-head"><div><span>Duft-DNA</span><h3>Charakterprofil pflegen</h3><p>Nur belegte Werte setzen. Leer bleibt wirklich unbekannt.</p></div><b>✦</b></div>
    <div class="dna-admin-meta">
      <label>Herkunft<select data-dna-meta="source"><option value="MANUAL">Manuell</option><option value="RESEARCH">Recherche</option><option value="RULE_BASED">Regelbasiert</option></select></label>
      <label>Prüfstatus<select data-dna-meta="status"><option value="OPEN">Offen</option><option value="REVIEW_REQUIRED">Prüfung nötig</option><option value="VERIFIED">Geprüft</option></select></label>
      <label>Quellenanzahl<input data-dna-meta="source_count" type="number" min="0" value="${metadata.source_count ?? ''}"></label>
      <label>Vertrauen 0–1<input data-dna-meta="confidence" type="number" min="0" max="1" step="0.01" value="${metadata.confidence ?? ''}"></label>
      <label>Abweichung 0–1<input data-dna-meta="disagreement" type="number" min="0" max="1" step="0.01" value="${metadata.disagreement ?? ''}"></label>
      <label>Recherchedatum<input data-dna-meta="researched_at" type="datetime-local" value="${date}"></label>
    </div>
    <div class="dna-admin-section-head"><div><span>Aggregierte Werte</span></div><b data-dna-count="research">${count} von 16 gesetzt</b></div>
    <div class="dna-admin-grid">${sliderMarkup('research', values)}</div>
    <button type="button" class="primary dna-admin-save" data-save-dna="research">Aggregierte DNA speichern</button>
    <div class="dna-admin-personal">
      <div class="dna-admin-section-head"><div><span>Meine persönliche DNA</span></div><b data-dna-count="personal">${personalCount} von 16 gesetzt</b></div>
      <p>Diese Werte bleiben fachlich getrennt von Recherche- und Community-Daten.</p>
      <div class="dna-admin-grid">${sliderMarkup('personal', personal)}</div>
      <button type="button" class="primary dna-admin-save" data-save-dna="personal">Persönliche DNA speichern</button>
    </div>
  </section>`;
}

function collectValues(card, prefix) {
  const values = {};
  card.querySelectorAll(`[data-dna-input="${prefix}"]`).forEach(input => {
    if (input.dataset.empty === 'true') return;
    values[input.dataset.dimension] = Number(input.value);
  });
  return values;
}

function wireEditor(card, fragranceId, metadata) {
  card.querySelector('[data-dna-meta="source"]').value = metadata.source || 'MANUAL';
  card.querySelector('[data-dna-meta="status"]').value = metadata.status || 'OPEN';

  card.querySelectorAll('[data-dna-input]').forEach(input => {
    const output = card.querySelector(`[data-output-for="${input.dataset.dnaInput}-${input.dataset.dimension}"]`);
    const initial = output.textContent === 'offen';
    input.dataset.empty = initial ? 'true' : 'false';
    input.addEventListener('input', () => {
      input.dataset.empty = 'false';
      output.textContent = Number(input.value).toFixed(1);
      const prefix = input.dataset.dnaInput;
      const count = collectValues(card, prefix);
      card.querySelector(`[data-dna-count="${prefix}"]`).textContent = `${Object.keys(count).length} von 16 gesetzt`;
    });
  });

  card.querySelectorAll('[data-clear-dna]').forEach(button => button.addEventListener('click', () => {
    const [prefix, dimension] = button.dataset.clearDna.split('-');
    const input = card.querySelector(`[data-dna-input="${prefix}"][data-dimension="${dimension}"]`);
    input.dataset.empty = 'true';
    input.value = 0;
    card.querySelector(`[data-output-for="${prefix}-${dimension}"]`).textContent = 'offen';
    const count = collectValues(card, prefix);
    card.querySelector(`[data-dna-count="${prefix}"]`).textContent = `${Object.keys(count).length} von 16 gesetzt`;
  }));

  card.querySelector('[data-save-dna="research"]').addEventListener('click', async () => {
    const values = collectValues(card, 'research');
    if (!Object.keys(values).length) return toast('Mindestens eine aggregierte DNA-Dimension muss gesetzt sein.');
    const meta = key => card.querySelector(`[data-dna-meta="${key}"]`).value;
    try {
      await request(`/api/fragrances/${fragranceId}/dna`, {method:'PUT', body:JSON.stringify({
        values,
        metadata:{
          source:meta('source'), status:meta('status'),
          source_count:meta('source_count') === '' ? null : Number(meta('source_count')),
          confidence:meta('confidence') === '' ? null : Number(meta('confidence')),
          disagreement:meta('disagreement') === '' ? null : Number(meta('disagreement')),
          researched_at:meta('researched_at') || null,
        }
      })});
      toast('Aggregierte Duft-DNA gespeichert.');
    } catch (error) { toast(error.message); }
  });

  card.querySelector('[data-save-dna="personal"]').addEventListener('click', async () => {
    const values = collectValues(card, 'personal');
    if (!Object.keys(values).length) return toast('Mindestens eine persönliche DNA-Dimension muss gesetzt sein.');
    try {
      await request(`/api/fragrances/${fragranceId}/dna/personal`, {method:'PUT', body:JSON.stringify(values)});
      toast('Persönliche Duft-DNA gespeichert.');
    } catch (error) { toast(error.message); }
  });
}

async function syncDNAEditor() {
  const form = [...document.querySelectorAll('form.editor')].find(node => node.querySelector('.editor-title')?.textContent.includes('Duft bearbeiten'));
  if (!form) {
    activeFragranceId = '';
    document.querySelectorAll('[data-dna-admin-card]').forEach(node => node.remove());
    return;
  }
  if (form.querySelector('[data-dna-admin-card]')) return;
  const fragranceId = await resolveFragranceId();
  if (!fragranceId) return;
  if (activeFragranceId === fragranceId && form.querySelector('[data-dna-admin-card]')) return;
  const token = ++renderToken;
  try {
    const data = await request(`/api/fragrances/${fragranceId}/dna`);
    if (token !== renderToken) return;
    form.querySelectorAll('[data-dna-admin-card]').forEach(node => node.remove());
    const submit = form.querySelector('button[type="submit"]');
    submit.insertAdjacentHTML('beforebegin', editorMarkup(data));
    const card = form.querySelector('[data-dna-admin-card]');
    wireEditor(card, fragranceId, data.metadata || {});
    activeFragranceId = fragranceId;
  } catch (error) {
    toast(`Duft-DNA konnte nicht geladen werden: ${error.message}`);
  }
}

const observer = new MutationObserver(syncDNAEditor);
observer.observe(document.documentElement, {childList:true, subtree:true});
window.addEventListener('popstate', syncDNAEditor);
syncDNAEditor();
