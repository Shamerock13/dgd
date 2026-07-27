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

function candidateOptions(candidates, selectedId = '') {
  return [
    '<option value="">Bitte wählen</option>',
    ...(candidates || []).map(candidate => `<option value="${escapeHtml(candidate.id)}" ${candidate.id === selectedId ? 'selected' : ''}>${escapeHtml(candidateText(candidate))}</option>`),
  ].join('');
}

function exactCandidateId(candidates) {
  return (candidates || []).find(candidate => ['exact', 'normalized'].includes(candidate.match_type))?.id || '';
}

function reviewControls(row, importType) {
  if (row.action !== 'REVIEW') return '–';
  if (importType === 'fragrances') {
    return `<label class="quality-review-field">Entscheidung
      <select data-fragrance-decision>
        <option value="">Bitte entscheiden</option>
        <option value="create">Als neuen Duft anlegen</option>
        ${(row.candidates || []).map(candidate => `<option value="use_existing:${escapeHtml(candidate.id)}">Vorhandenen verwenden: ${escapeHtml(candidateText(candidate))}</option>`).join('')}
        <option value="exclude">Zeile ausschließen</option>
      </select>
    </label>`;
  }
  const originalSelected = exactCandidateId(row.original_candidates);
  const alternativeSelected = exactCandidateId(row.alternative_candidates);
  return `<div class="quality-review-fields">
    <label class="quality-review-field">Entscheidung
      <select data-twin-decision>
        <option value="">Bitte entscheiden</option>
        <option value="use_candidates">Gewählte Zuordnung verwenden</option>
        <option value="exclude">Zeile ausschließen</option>
      </select>
    </label>
    <label class="quality-review-field">Original
      <select data-original-candidate>${candidateOptions(row.original_candidates, originalSelected)}</select>
    </label>
    <label class="quality-review-field">Alternative
      <select data-alternative-candidate>${candidateOptions(row.alternative_candidates, alternativeSelected)}</select>
    </label>
  </div>`;
}

function qualityStatus(data) {
  const counts = data.counts || {};
  if (counts.BLOCK) return {label: 'Import gesperrt', className: 'unsafe'};
  if (counts.REVIEW) return {label: 'Entscheidungen nötig', className: 'review'};
  return {label: 'Import freigegeben', className: 'safe'};
}

function renderQuality(panel, data, importType) {
  const counts = data.counts || {};
  const rows = data.rows || [];
  const status = qualityStatus(data);
  panel.innerHTML = `
    <div class="quality-preview-head">
      <div><span>Qualitätsprüfung 2.0</span><h2>${data.total_rows || 0} Zeilen bewertet</h2></div>
      <strong class="quality-safe ${status.className}">${status.label}</strong>
    </div>
    <div class="quality-counts">
      ${['CREATE','DUPLICATE','REVIEW','BLOCK'].map(action => `<div class="quality-count quality-${action.toLowerCase()}"><b>${counts[action] || 0}</b><span>${ACTION_LABELS[action]}</span></div>`).join('')}
    </div>
    <p class="quality-explainer">Blockierte Zeilen bleiben unveränderbar gesperrt. Für Prüfhinweise kannst du bewusst einen neuen Datensatz anlegen, einen vorhandenen Kandidaten verwenden oder die Zeile ausschließen.</p>
    <div class="quality-table-wrap"><table class="quality-table"><thead><tr><th>Zeile</th><th>Datensatz</th><th>Status</th><th>Begründung</th><th>Kandidaten / Fehler</th><th>Manuelle Auflösung</th></tr></thead><tbody>
      ${rows.map(row => {
        const candidates = importType === 'fragrances'
          ? (row.candidates || [])
          : [...(row.original_candidates || []), ...(row.alternative_candidates || [])];
        const notes = [...(row.errors || []), ...candidates.map(candidateText)].filter(Boolean);
        return `<tr data-review-row="${escapeHtml(row.row)}" class="quality-row-${String(row.action || '').toLowerCase()}"><td>${escapeHtml(row.row)}</td><td>${escapeHtml(rowIdentity(row, importType))}</td><td><span class="quality-badge quality-${String(row.action || '').toLowerCase()}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span></td><td>${escapeHtml(row.reason || '–')}</td><td>${notes.length ? notes.map(note => `<div>${escapeHtml(note)}</div>`).join('') : '–'}</td><td>${reviewControls(row, importType)}</td></tr>`;
      }).join('')}
    </tbody></table></div>
    ${data.rows_truncated ? '<p class="quality-note">Die Anzeige wurde gekürzt. REVIEW-Zeilen außerhalb der Anzeige können nicht über diese Ansicht freigegeben werden.</p>' : ''}
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

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Fehler ${response.status}`);
  return response.json();
}

async function runQualityCheck(container, button) {
  const fileInput = container.querySelector('input[type="file"]');
  const selects = container.querySelectorAll('.import-panel select');
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
    qualityState.set(container, {key: fileKey(file, importType), data, panel});
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

function collectReviewDecisions(state, importType) {
  const decisions = [];
  const reviewRows = (state.data.rows || []).filter(row => row.action === 'REVIEW');
  if (state.data.rows_truncated && Number(state.data.counts?.REVIEW || 0) > reviewRows.length) {
    throw new Error('Die Datei enthält mehr REVIEW-Zeilen als angezeigt werden können. Bitte die Datei in kleinere Importe aufteilen.');
  }

  reviewRows.forEach(row => {
    const tableRow = state.panel.querySelector(`[data-review-row="${row.row}"]`);
    if (!tableRow) throw new Error(`Die Entscheidung für Zeile ${row.row} ist nicht sichtbar.`);
    if (importType === 'fragrances') {
      const value = tableRow.querySelector('[data-fragrance-decision]')?.value || '';
      if (!value) throw new Error(`Bitte für Zeile ${row.row} eine Entscheidung wählen.`);
      if (value === 'create' || value === 'exclude') {
        decisions.push({row: row.row, choice: value});
      } else if (value.startsWith('use_existing:')) {
        decisions.push({row: row.row, choice: 'use_existing', candidate_id: value.slice('use_existing:'.length)});
      } else {
        throw new Error(`Die Entscheidung für Zeile ${row.row} ist ungültig.`);
      }
      return;
    }

    const choice = tableRow.querySelector('[data-twin-decision]')?.value || '';
    if (!choice) throw new Error(`Bitte für Zeile ${row.row} eine Entscheidung wählen.`);
    if (choice === 'exclude') {
      decisions.push({row: row.row, choice});
      return;
    }
    const originalId = tableRow.querySelector('[data-original-candidate]')?.value || '';
    const alternativeId = tableRow.querySelector('[data-alternative-candidate]')?.value || '';
    if (!originalId || !alternativeId) {
      throw new Error(`Bitte für Zeile ${row.row} Original und Alternative auswählen.`);
    }
    decisions.push({row: row.row, choice: 'use_candidates', original_id: originalId, alternative_id: alternativeId});
  });
  return decisions;
}

async function guardedCommit(container, commitButton, qualityButton) {
  const fileInput = container.querySelector('input[type="file"]');
  const selects = container.querySelectorAll('.import-panel select');
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
  if (counts.BLOCK) {
    window.alert(`Import gesperrt: ${counts.BLOCK} blockierte Zeile(n).`);
    return;
  }

  let decisions;
  try {
    decisions = collectReviewDecisions(state, importType);
  } catch (error) {
    window.alert(error.message);
    return;
  }

  const reviewText = decisions.length ? ` ${decisions.length} manuelle Entscheidung(en) werden serverseitig erneut geprüft.` : '';
  if (!window.confirm(`Import jetzt ausführen?${reviewText}`)) return;

  commitButton.disabled = true;
  const originalText = commitButton.textContent;
  commitButton.textContent = 'Sicherer Import läuft …';
  try {
    const form = new FormData();
    form.append('file', file);
    form.append('import_type', importType);
    form.append('duplicate_mode', duplicateMode);
    form.append('review_decisions', JSON.stringify(decisions));
    const result = await postForm('/api/import/quality/commit', form);
    window.alert(`Import abgeschlossen: ${result.created} neu, ${result.updated} aktualisiert, ${result.skipped} übersprungen, ${result.excluded || 0} ausgeschlossen, ${result.failed} fehlerhaft.`);
    window.location.reload();
  } catch (error) {
    window.alert(error.message);
    commitButton.disabled = false;
    commitButton.textContent = originalText;
    loadRunHistory(container);
  }
}

function runSummary(run) {
  const report = run.report || {};
  const result = report.result || {};
  const decisions = report.decisions || [];
  if (run.status === 'SUCCESS') {
    return `${result.created || 0} neu · ${result.updated || 0} aktualisiert · ${result.skipped || 0} übersprungen · ${report.excluded || 0} ausgeschlossen · ${decisions.length} Entscheidung(en)`;
  }
  return report.message || 'Import wurde nicht ausgeführt.';
}

function renderRunHistory(panel, runs) {
  panel.innerHTML = `<div class="quality-preview-head"><div><span>Nachvollziehbarkeit</span><h2>Letzte Importberichte</h2></div></div>
    ${runs.length ? `<div class="quality-run-list">${runs.map(run => `<details class="quality-run quality-run-${String(run.status || '').toLowerCase()}"><summary><span><b>${escapeHtml(run.filename)}</b><small>${escapeHtml(run.import_type)} · ${new Date(run.created_at).toLocaleString('de-DE')}</small></span><strong>${escapeHtml(run.status)}</strong></summary><p>${escapeHtml(runSummary(run))}</p>${(run.report?.decisions || []).length ? `<ul>${run.report.decisions.map(decision => `<li>Zeile ${escapeHtml(decision.row)}: ${escapeHtml(decision.summary || decision.choice)}</li>`).join('')}</ul>` : ''}</details>`).join('')}</div>` : '<p class="quality-note">Noch keine abgesicherten Importläufe gespeichert.</p>'}`;
}

async function loadRunHistory(container) {
  let panel = container.querySelector('.quality-run-history');
  if (!panel) {
    panel = document.createElement('section');
    panel.className = 'quality-preview-panel quality-run-history';
    container.appendChild(panel);
  }
  panel.innerHTML = '<div class="quality-loading">Importberichte werden geladen …</div>';
  try {
    renderRunHistory(panel, await getJson('/api/import/quality/runs?limit=10'));
  } catch (error) {
    panel.innerHTML = `<div class="quality-error">Importberichte konnten nicht geladen werden: ${escapeHtml(error.message)}</div>`;
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
    container.querySelector('.quality-preview-panel:not(.quality-run-history)')?.remove();
  };
  container.querySelector('input[type="file"]')?.addEventListener('change', resetQuality);
  container.querySelectorAll('.import-panel select')[0]?.addEventListener('change', resetQuality);

  container.addEventListener('click', event => {
    const commitButton = event.target.closest('.commit-bar .primary');
    if (!commitButton || !container.contains(commitButton)) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    guardedCommit(container, commitButton, button);
  }, true);

  loadRunHistory(container);
}

enhanceImportCenter();
new MutationObserver(enhanceImportCenter).observe(document.documentElement, {childList: true, subtree: true});
