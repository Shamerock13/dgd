const PAGE_SIZE = 20;
const SUPPORTED_HEADINGS = new Map([
  ['Vorhandene Düfte', 'fragrances'],
  ['Vorhandene Marken', 'brands'],
]);

const stateByKey = new Map();
let mutationQueued = false;
let observerPaused = false;

function readState(key) {
  if (stateByKey.has(key)) return stateByKey.get(key);
  let saved = {};
  try { saved = JSON.parse(sessionStorage.getItem(`dgd-admin-list:${key}`) || '{}'); } catch {}
  const state = {
    query: typeof saved.query === 'string' ? saved.query : '',
    page: Number.isInteger(saved.page) && saved.page > 0 ? saved.page : 1,
    returnText: typeof saved.returnText === 'string' ? saved.returnText : '',
  };
  stateByKey.set(key, state);
  return state;
}

function saveState(key, state) {
  stateByKey.set(key, state);
  try { sessionStorage.setItem(`dgd-admin-list:${key}`, JSON.stringify(state)); } catch {}
}

function normalize(value) {
  return String(value || '').trim().toLocaleLowerCase('de-DE');
}

function createButton(label, onClick, disabled = false, current = false) {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = label;
  button.disabled = disabled;
  if (current) button.classList.add('current');
  button.addEventListener('click', onClick);
  return button;
}

function enhanceList(list) {
  if (list.dataset.adminListEnhanced === 'true') return;
  const heading = list.querySelector(':scope > h3');
  const key = SUPPORTED_HEADINGS.get(heading?.textContent?.trim());
  if (!key) return;

  list.dataset.adminListEnhanced = 'true';
  const state = readState(key);
  const rows = Array.from(list.querySelectorAll(':scope > .admin-row'));
  const originalHeading = heading.textContent.trim();

  const tools = document.createElement('div');
  tools.className = 'admin-list-tools';

  const searchWrap = document.createElement('label');
  searchWrap.className = 'admin-list-search';
  const searchLabel = document.createElement('span');
  searchLabel.textContent = key === 'fragrances' ? 'Düfte durchsuchen' : 'Marken durchsuchen';
  const input = document.createElement('input');
  input.type = 'search';
  input.value = state.query;
  input.placeholder = key === 'fragrances' ? 'Duft oder Marke …' : 'Marke oder Land …';
  input.autocomplete = 'off';
  searchWrap.append(searchLabel, input);

  const count = document.createElement('span');
  count.className = 'admin-list-count';
  tools.append(searchWrap, count);
  heading.after(tools);

  const pagination = document.createElement('nav');
  pagination.className = 'admin-list-pagination';
  pagination.setAttribute('aria-label', `${originalHeading} Seiten`);
  list.append(pagination);

  function render({scroll = false} = {}) {
    const current = readState(key);
    const needle = normalize(current.query);
    const matches = rows.filter(row => !needle || normalize(row.textContent).includes(needle));
    const pages = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
    current.page = Math.min(Math.max(1, current.page), pages);
    saveState(key, current);

    rows.forEach(row => { row.hidden = true; });
    const start = (current.page - 1) * PAGE_SIZE;
    const visible = matches.slice(start, start + PAGE_SIZE);
    visible.forEach(row => { row.hidden = false; });

    count.textContent = `${matches.length} von ${rows.length}`;
    pagination.replaceChildren();
    if (pages > 1) {
      pagination.append(
        createButton('Zurück', () => { current.page -= 1; saveState(key, current); render({scroll:true}); }, current.page === 1),
      );
      const first = Math.max(1, Math.min(current.page - 2, pages - 4));
      const last = Math.min(pages, first + 4);
      for (let page = first; page <= last; page += 1) {
        pagination.append(createButton(String(page), () => { current.page = page; saveState(key, current); render({scroll:true}); }, false, page === current.page));
      }
      pagination.append(
        createButton('Weiter', () => { current.page += 1; saveState(key, current); render({scroll:true}); }, current.page === pages),
      );
    }

    if (scroll) tools.scrollIntoView({behavior:'smooth', block:'start'});

    if (current.returnText) {
      const target = visible.find(row => normalize(row.textContent).includes(normalize(current.returnText)));
      if (target) {
        current.returnText = '';
        saveState(key, current);
        window.setTimeout(() => target.scrollIntoView({behavior:'smooth', block:'center'}), 80);
      }
    }
  }

  input.addEventListener('input', () => {
    const current = readState(key);
    current.query = input.value;
    current.page = 1;
    saveState(key, current);
    render();
  });

  rows.forEach(row => {
    const buttons = row.querySelectorAll(':scope > div:last-child button');
    const editButton = Array.from(buttons).find(button => !button.classList.contains('danger'));
    if (!editButton) return;
    editButton.addEventListener('click', () => {
      const current = readState(key);
      const title = row.querySelector('b')?.textContent?.trim() || row.textContent.trim();
      current.returnText = title;
      saveState(key, current);
    });
  });

  render();
}

function scan() {
  if (observerPaused) return;
  observerPaused = true;
  document.querySelectorAll('.admin-list').forEach(enhanceList);
  observerPaused = false;
}

const observer = new MutationObserver(() => {
  if (observerPaused || mutationQueued) return;
  mutationQueued = true;
  requestAnimationFrame(() => {
    mutationQueued = false;
    scan();
  });
});

function start() {
  scan();
  observer.observe(document.body, {childList:true, subtree:true});
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start, {once:true});
} else {
  start();
}
