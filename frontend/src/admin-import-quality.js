const ACTION_LABELS = {
  CREATE: 'Neu anlegen',
  DUPLICATE: 'Dublette',
  REVIEW: 'Prüfen',
  BLOCK: 'Blockiert',
};

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

function renderQuality(panel, data, importType) {
  const counts = data.counts || {};
  const rows = data.rows || [];
  panel.innerHTML = `
    <div class="quality-preview-head">
      <div><span>Qualitätsprüfung 2.0</span><h2>${data.total_rows || 0} Zeilen bewertet</h2></div>
      <strong class="quality-safe ${data.safe_to_commit ? 'safe' : 'unsafe'}">${data.safe_to_commit ? 'Ohne Prüfkonflikte' : 'Manuelle Prüfung nötig'}</strong>
    </div>
    <div class="quality-counts">
      ${['CREATE','DUPLICATE','REVIEW','BLOCK'].map(action => `<div class="quality-count quality-${action.toLowerCase()}"><b>${counts[action] || 0}</b><span>${ACTION_LABELS[action]}</span></div>`).join('')}
    </div>
    <p class="quality-explainer">Diese Prüfung schreibt nichts in die Datenbank. Ähnliche Schreibweisen werden nur vorgeschlagen und niemals automatisch zusammengeführt.</p>
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

async function runQualityCheck(container, button) {
  const fileInput = container.querySelector('input[type="file"]');
  const selects = container.querySelectorAll('select');
  const importType = selects[0]?.value || 'fragrances';
  const file = fileInput?.files?.[0];
  if (!file) {
    window.alert('Bitte zuerst eine CSV- oder XLSX-Datei auswählen.');
    return;
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
    const response = await fetch('/api/import/quality/preview', {method: 'POST', body: form});
    if (!response.ok) {
      let message = `Fehler ${response.status}`;
      try { const body = await response.json(); message = body.detail || message; } catch {}
      throw new Error(message);
    }
    renderQuality(panel, await response.json(), importType);
  } catch (error) {
    panel.innerHTML = `<div class="quality-error">${escapeHtml(error.message)}</div>`;
  } finally {
    button.disabled = false;
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

  container.querySelector('input[type="file"]')?.addEventListener('change', () => container.querySelector('.quality-preview-panel')?.remove());
  container.querySelectorAll('select')[0]?.addEventListener('change', () => container.querySelector('.quality-preview-panel')?.remove());
}

enhanceImportCenter();
new MutationObserver(enhanceImportCenter).observe(document.documentElement, {childList: true, subtree: true});
