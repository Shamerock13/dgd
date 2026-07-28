import './catalog-performance.css';

const STATUS_LABELS = {
  OPEN: 'Noch offen',
  VERIFIED: 'Geprüft',
  REVIEW_REQUIRED: 'Prüfung nötig',
};

const STATUS_COPY = {
  OPEN: 'Für diesen Duft liegen noch keine ausreichend geprüften Performance-Daten vor.',
  VERIFIED: 'Die Angaben wurden geprüft und als belastbar markiert.',
  REVIEW_REQUIRED: 'Die Quellen weichen merklich voneinander ab und sollten noch geprüft werden.',
};

const number = value => value == null || value === '' ? null : Number(value);
const scoreText = value => number(value) == null ? 'Noch offen' : `${number(value).toFixed(1)} / 10`;
const percentText = value => number(value) == null ? 'Noch offen' : `${Math.round(number(value) * 100)} %`;
const hoursText = fragrance => {
  const min = number(fragrance.longevity_min_hours);
  const max = number(fragrance.longevity_max_hours);
  if (min == null && max == null) return 'Noch offen';
  if (min != null && max != null) return min === max ? `${min.toFixed(1)} Std.` : `${min.toFixed(1)}–${max.toFixed(1)} Std.`;
  return `${(min ?? max).toFixed(1)} Std.`;
};

function strengthLabel(value) {
  const numeric = number(value);
  if (numeric == null) return 'Noch offen';
  if (numeric >= 8) return 'Sehr stark';
  if (numeric >= 6) return 'Stark';
  if (numeric >= 4) return 'Mittel';
  if (numeric >= 2) return 'Hautnah';
  return 'Sehr dezent';
}

function performanceBadge(value) {
  const numeric = number(value);
  if (numeric == null) return {label:'Noch offen', className:'open'};
  if (numeric >= 8) return {label:'Sehr stark', className:'very-strong'};
  if (numeric >= 6) return {label:'Stark', className:'strong'};
  if (numeric >= 4) return {label:'Durchschnittlich', className:'average'};
  return {label:'Eher dezent', className:'soft'};
}

function metric(label, value, hint) {
  const numeric = number(value);
  return `<article class="performance-metric">
    <div><span>${label}</span><strong>${scoreText(value)}</strong></div>
    <div class="performance-track" aria-hidden="true"><i style="width:${numeric == null ? 0 : Math.max(0, Math.min(100, numeric * 10))}%"></i></div>
    ${hint ? `<small>${hint}</small>` : ''}
  </article>`;
}

function timelinePhase(label, time, value, copy) {
  const numeric = number(value);
  const width = numeric == null ? 0 : Math.max(4, Math.min(100, numeric * 10));
  return `<article class="performance-phase ${numeric == null ? 'is-empty' : ''}">
    <div class="performance-phase-head"><div><span>${time}</span><h3>${label}</h3></div><strong>${strengthLabel(value)}</strong></div>
    <div class="performance-phase-track" aria-hidden="true"><i style="width:${width}%"></i></div>
    <div class="performance-phase-foot"><small>${copy}</small><b>${scoreText(value)}</b></div>
  </article>`;
}

function timelineSummary(fragrance) {
  const first = number(fragrance.projection_first_hour);
  const later = number(fragrance.projection_after_three_hours);
  const drydown = number(fragrance.drydown_strength);
  if ([first, later, drydown].every(value => value == null)) {
    return 'Für den zeitlichen Verlauf sind noch keine Werte hinterlegt.';
  }
  const parts = [];
  if (first != null) parts.push(`Der Start ist ${strengthLabel(first).toLowerCase()}`);
  if (first != null && later != null) {
    if (later <= first - 2) parts.push('nach drei Stunden wird der Duft deutlich ruhiger');
    else if (later >= first + 1) parts.push('nach drei Stunden gewinnt die Ausstrahlung noch an Stärke');
    else parts.push('nach drei Stunden bleibt die Ausstrahlung vergleichsweise stabil');
  } else if (later != null) parts.push(`nach drei Stunden wirkt er ${strengthLabel(later).toLowerCase()}`);
  if (drydown != null) parts.push(`der Drydown ist ${strengthLabel(drydown).toLowerCase()}`);
  return `${parts.join(', ')}.`.replace(/^./, char => char.toUpperCase());
}

function renderCard(fragrance) {
  const status = fragrance.performance_status || 'OPEN';
  const sourceCount = number(fragrance.performance_source_count);
  const researchedAt = fragrance.performance_researched_at
    ? new Intl.DateTimeFormat('de-DE', {dateStyle:'medium'}).format(new Date(fragrance.performance_researched_at))
    : 'Noch nicht recherchiert';
  const version = [fragrance.performance_version, fragrance.performance_production_period].filter(Boolean).join(' · ') || 'Keine Version angegeben';
  const personalAvailable = [fragrance.personal_longevity_hours, fragrance.personal_projection, fragrance.personal_sillage, fragrance.personal_performance_score].some(value => number(value) != null);
  const badge = performanceBadge(fragrance.performance_score);

  return `<section class="performance-card" data-performance-fragrance="${fragrance.id}">
    <div class="performance-head">
      <div><span class="performance-kicker">Performance</span><h2>So stark tritt der Duft auf</h2><p>Community-Werte und persönliche Eindrücke bleiben bewusst getrennt.</p></div>
      <div class="performance-badges"><span class="performance-strength performance-strength-${badge.className}">${badge.label}</span><span class="performance-status performance-status-${status.toLowerCase().replaceAll('_','-')}">${STATUS_LABELS[status] || status}</span></div>
    </div>

    <div class="performance-summary">
      <article><span>Haltbarkeit</span><strong>${hoursText(fragrance)}</strong><small>${scoreText(fragrance.longevity_score)}</small></article>
      <article><span>Gesamtleistung</span><strong>${scoreText(fragrance.performance_score)}</strong><small>normalisierter Vergleichswert</small></article>
      <article><span>Vertrauen</span><strong>${percentText(fragrance.performance_confidence)}</strong><small>${sourceCount == null ? 'Quellen offen' : `${sourceCount} ${sourceCount === 1 ? 'Quelle' : 'Quellen'}`}</small></article>
    </div>

    <section class="performance-timeline">
      <div class="performance-timeline-head"><div><span>Zeitlicher Duftverlauf</span><h3>Von der ersten Stunde bis zum Drydown</h3></div><small>${hoursText(fragrance)} Haltbarkeit</small></div>
      <div class="performance-phase-grid">
        ${timelinePhase('Opening', '0–1 Stunde', fragrance.projection_first_hour, 'Ausstrahlung direkt nach dem Auftragen')}
        ${timelinePhase('Herzphase', 'nach 3 Stunden', fragrance.projection_after_three_hours, 'Ausstrahlung während der späteren Entwicklung')}
        ${timelinePhase('Drydown', 'Basisphase', fragrance.drydown_strength, 'Stärke der verbleibenden Basisnoten')}
      </div>
      <p class="performance-timeline-summary">${timelineSummary(fragrance)}</p>
    </section>

    <div class="performance-grid">
      ${metric('Projektion', fragrance.projection, 'allgemeiner Eindruck')}
      ${metric('Sillage', fragrance.sillage, 'Duftspur im Raum')}
      ${metric('Erste Stunde', fragrance.projection_first_hour, 'direkt nach dem Auftragen')}
      ${metric('Nach drei Stunden', fragrance.projection_after_three_hours, 'spätere Ausstrahlung')}
      ${metric('Drydown', fragrance.drydown_strength, 'Stärke der Basisphase')}
      ${metric('Quellenabweichung', fragrance.performance_disagreement, 'je niedriger, desto einheitlicher')}
    </div>

    <div class="performance-evidence">
      <div><span>Datenstand</span><b>${researchedAt}</b></div>
      <div><span>Version / Zeitraum</span><b>${version}</b></div>
      <p>${STATUS_COPY[status] || STATUS_COPY.OPEN}</p>
    </div>

    <div class="personal-performance ${personalAvailable ? '' : 'is-empty'}">
      <div><span>Meine Bewertung</span><h3>${personalAvailable ? 'Persönlicher Hauttest' : 'Noch kein persönlicher Test'}</h3></div>
      <div class="personal-performance-values">
        <span><small>Haltbarkeit</small><b>${number(fragrance.personal_longevity_hours) == null ? '–' : `${number(fragrance.personal_longevity_hours).toFixed(1)} Std.`}</b></span>
        <span><small>Projektion</small><b>${scoreText(fragrance.personal_projection)}</b></span>
        <span><small>Sillage</small><b>${scoreText(fragrance.personal_sillage)}</b></span>
        <span><small>Gesamt</small><b>${scoreText(fragrance.personal_performance_score)}</b></span>
      </div>
    </div>
  </section>`;
}

let activeId = '';
let requestToken = 0;

async function syncPerformanceCard() {
  const id = new URLSearchParams(window.location.search).get('fragrance') || '';
  const detailContent = document.querySelector('.catalog-detail .detail-content');
  if (!id || !detailContent) return;
  if (activeId === id && detailContent.querySelector(`[data-performance-fragrance="${id}"]`)) return;

  const token = ++requestToken;
  try {
    const response = await fetch(`/api/fragrances/${encodeURIComponent(id)}`);
    if (!response.ok) return;
    const fragrance = await response.json();
    if (token !== requestToken) return;

    detailContent.querySelectorAll('.performance-card').forEach(node => node.remove());
    const anchor = detailContent.querySelector('.detail-facts');
    if (!anchor) return;
    anchor.insertAdjacentHTML('afterend', renderCard(fragrance));
    activeId = id;
  } catch {
    // Das Duftprofil bleibt auch dann vollständig nutzbar, wenn die Zusatzkarte nicht geladen werden kann.
  }
}

const observer = new MutationObserver(syncPerformanceCard);
observer.observe(document.documentElement, {childList:true, subtree:true});
window.addEventListener('popstate', () => { activeId = ''; syncPerformanceCard(); });
syncPerformanceCard();
