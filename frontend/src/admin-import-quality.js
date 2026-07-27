const ACTION_LABELS = {
  CREATE: 'Neu anlegen',
  DUPLICATE: 'Dublette',
  REVIEW: 'Prüfen',
  BLOCK: 'Blockiert',
};

const qualityState = new WeakMap();

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function candidateText(candidate) {
  if (!candidate) return '';
  const percent = Math.round(Number(candidate.score || 0) * 100);
  return `${candidate.brand} – ${candidate.name} (${percent} %, ${candidate.match_type})`;
}

function rowIdentity(row, importType) {
  if (importType === 'fragrances') return `${row.brand || '–'} – ${row.name || '–'}`;
  return `${row.original || '–'} → ${row.alternative || '–'}`;
}

function fileKey(file, importType) {
  return file ? `${file.name}:${file.size}:${file.lastModified}:${importType}` : '';
}

function renderQuality(panel, data, importType) {
  const counts = data.counts || {};
  const rows = data.rows || [];
  panel.innerHTML = `
    <div class="quality-preview-head">
      <div><span>Qualitätsprüfung 2.0</span><h2>${data.total_rows || 0} Zeilen bewertet</h2></div>
      <strong class="quality-safe ${data.safe_to_commit ? 'safe' : 'unsafe'}">${data.safe_to_commit ? 'Import freigegeben' : 'Import gesperrt'}</strong>
    </div>
    <div class="quality-counts">
      ${['CREATE','DUPLICATE','REVIEW','BLOCK'].map(action => `<div class="quality-count quality-${action.toLowerCase()}"><b>${counts[action] || 0}</b><span>${ACTION_LABELS[action]}</span></div>`).join('')}
    </div>
    <p class="quality-explainer">Der Admin-Import verwendet dieselbe Prüfung erneut unmittelbar vor dem Schreiben. Offene Prüfhinweise oder blockierte Zeilen stoppen den Import vollständig.</p>
    <div class="quality-table-wrap"><table class="quality-table"><thead><tr><th>Zeile</th><th>Datensatz</th><th>Entscheidung</th><th>Begründung</th><th>Kandidaten / Fehler</th></tr></thead><tbody>
      ${rows.map(row => {
        const candidates = importType === 'fragrances'
          ? (row.candidates || [])
          : [...(row.original_candidates || []), ...(row.alternative_candidates || [])];
        const notes = [...(row.errors || []), ...candidates.map(candidateText)].filter(Boolean);
        return `<tr class="quality-row-${String(row.action || '').toLowerCase()}"><td>${escapeHtml(row.row)}</td><td>${escapeHtml(rowIdentity(row, importType))}</td><td><span class="quality-badge quality-${String(row.action || '').toLowerCase()}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span></td><td>${escapeHtml(row.reason || '–')}</td><td>${notes.length ? notes.map(note => `<div>${escapeHtml(note)}</div>`).join('') : '–'}</td></tr>`;
      }).join('')}
    </tbody></table></div>
    ${data.rows_truncated ? '<p class="quality-note">Die Anzeige wurde gekürzt; die Bewertung enthält weitere Zeilen.</p>' : ''}
  `;
}

async function postForm(url, form) {
  const response = await fetch(url, {method: 'POST', body: form});
  if (!response.ok) {
    let message = `Fehler ${response.status}`;
    try {
      const body = await response.json();
      message = typeof body.detail === 'string' ? body.detail : (body.detail?.message || message);
    } catch {}
    throw new Error(message);
  }
  return response.json();
}

async function runQualityCheck(container, button) {
  const fileInput = container.querySelector('input[type="file"]');
  const selects = container.querySelectorAll('select');
  const importType = selects[0]?.value || 'fragrances';
  const file = fileInput?.files?.[0];
  if (!file) {
    window.alert('Bitte zuerst eine CSV- oder XLSX-Datei auswählen.');
    return null;
  }

  let panel = container.querySelector('.quality-preview-panel');
  if (!panel) {
    panel = document.createElement('section');
    panel.className = 'quality-preview-panel';
    container.appendChild(panel);
  }
  panel.innerHTML = '<div class="quality-loading">Qualitätsprüfung läuft …</div>';
  button.disabled = true;

  try {
    const form = new FormData();
    form.append('file', file);
    form.append('import_type', importType);
    const data = await postForm('/api/import/quality/preview', form);
    qualityState.set(container, {key: fileKey(file, importType), data});
    renderQuality(panel, data, importType);
    return data;
  } catch (error) {
    qualityState.delete(container);
    panel.innerHTML = `<div class="quality-error">${escapeHtml(error.message)}</div>`;
    return null;
  } finally {
    button.disabled = false;
  }
}

async function guardedCommit(container, commitButton, qualityButton) {
  const fileInput = container.querySelector('input[type="file"]');
  const selects = container.querySelectorAll('select');
  const importType = selects[0]?.value || 'fragrances';
  const duplicateMode = selects[1]?.value || 'skip';
  const file = fileInput?.files?.[0];
  if (!file) return;

  let state = qualityState.get(container);
  if (!state || state.key !== fileKey(file, importType)) {
    const data = await runQualityCheck(container, qualityButton);
    state = data ? qualityState.get(container) : null;
  }
  if (!state) return;
  const counts = state.data.counts || {};
  if (!state.data.safe_to_commit) {
    window.alert(`Import gesperrt: ${counts.REVIEW || 0} Prüfhinweis(e) und ${counts.BLOCK || 0} blockierte Zeile(n).`);
    return;
  }
  if (!window.confirm('Die Qualitätsprüfung ist ohne offene Konflikte. Import jetzt ausführen?')) return;

  commitButton.disabled = true;
  const originalText = commitButton.textContent;
  commitButton.textContent = 'Sicherer Import läuft …';
  try {
    const form = new FormData();
    form.append('file', file);
    form.append('import_type', importType);
    form.append('duplicate_mode', duplicateMode);
    const result = await postForm('/api/import/quality/commit', form);
    window.alert(`Import abgeschlossen: ${result.created} neu, ${result.updated} aktualisiert, ${result.skipped} übersprungen, ${result.failed} fehlerhaft.`);
    window.location.reload();
  } catch (error) {
    window.alert(error.message);
    commitButton.disabled = false;
    commitButton.textContent = originalText;
  }
}

function enhanceImportCenter() {
  const container = document.querySelector('.import-center');
  if (!container || container.dataset.qualityEnhanced === 'true') return;
  const actions = container.querySelector('.import-actions');
  if (!actions) return;

  container.dataset.qualityEnhanced = 'true';
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'quality-check-button';
  button.textContent = 'Qualität & Dubletten prüfen';
  button.addEventListener('click', () => runQualityCheck(container, button));
  actions.insertBefore(button, actions.querySelector('.primary'));

  const resetQuality = () => {
    qualityState.delete(container);
    container.querySelector('.quality-preview-panel')?.remove();
  };
  container.querySelector('input[type="file"]')?.addEventListener('change', resetQuality);
  container.querySelectorAll('select')[0]?.addEventListener('change', resetQuality);

  container.addEventListener('click', event => {
    const commitButton = event.target.closest('.commit-bar .primary');
    if (!commitButton || !container.contains(commitButton)) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    guardedCommit(container, commitButton, button);
  }, true);
}

enhanceImportCenter();
new MutationObserver(enhanceImportCenter).observe(document.documentElement, {childList: true, subtree: true});
