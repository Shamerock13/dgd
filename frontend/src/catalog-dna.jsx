import './catalog-dna.css';

const DIMENSIONS = {
  fresh: 'Frisch', citrus: 'Zitrisch', green: 'Grün', aquatic: 'Aquatisch',
  floral: 'Floral', fruity: 'Fruchtig', sweet: 'Süß', gourmand: 'Gourmandig',
  spicy: 'Würzig', woody: 'Holzig', smoky: 'Rauchig', earthy: 'Erdig',
  resinous: 'Harzig', leathery: 'Ledrig', powdery: 'Pudrig', animalic: 'Animalisch',
};

const STATUS_LABELS = {OPEN:'Noch offen', VERIFIED:'Geprüft', REVIEW_REQUIRED:'Prüfung nötig'};
const SOURCE_LABELS = {MANUAL:'Manuell', RESEARCH:'Recherche', RULE_BASED:'Regelbasiert'};
const number = value => value == null || value === '' ? null : Number(value);
const scoreText = value => number(value) == null ? '–' : `${number(value).toFixed(1)} / 10`;
const percentText = value => number(value) == null ? 'Noch offen' : `${Math.round(number(value) * 100)} %`;

function availableValues(values) {
  return Object.entries(values || {})
    .filter(([key, value]) => DIMENSIONS[key] && number(value) != null)
    .sort((a, b) => number(b[1]) - number(a[1]));
}

function bars(values, personal = false) {
  const rows = availableValues(values);
  if (!rows.length) return `<div class="dna-empty">${personal ? 'Noch keine persönliche Duft-DNA hinterlegt.' : 'Für diesen Duft liegt noch kein strukturiertes DNA-Profil vor.'}</div>`;
  return `<div class="dna-bars">${rows.map(([key, value]) => {
    const numeric = Math.max(0, Math.min(10, number(value)));
    return `<div class="dna-row"><div class="dna-row-head"><span>${DIMENSIONS[key]}</span><b>${scoreText(value)}</b></div><div class="dna-track" aria-hidden="true"><i style="width:${numeric * 10}%"></i></div></div>`;
  }).join('')}</div>`;
}

function renderCard(data, fragranceId) {
  const metadata = data?.metadata || {};
  const status = metadata.status || 'OPEN';
  const sourceCount = number(metadata.source_count);
  const researchedAt = metadata.researched_at
    ? new Intl.DateTimeFormat('de-DE', {dateStyle:'medium'}).format(new Date(metadata.researched_at))
    : 'Noch nicht recherchiert';
  const values = data?.values || null;
  const strongest = availableValues(values).slice(0, 3).map(([key]) => DIMENSIONS[key]).join(' · ');

  return `<section class="dna-card" data-dna-fragrance="${fragranceId}">
    <div class="dna-head">
      <div><span class="dna-kicker">Duft-DNA</span><h2>So ist der Duft charakterlich aufgebaut</h2><p>Strukturierte Charakterwerte ergänzen Noten und Akkorde, ohne fehlende Angaben zu erfinden.</p></div>
      <div class="dna-badges"><span>${SOURCE_LABELS[metadata.source] || 'Herkunft offen'}</span><span class="dna-status dna-status-${status.toLowerCase().replaceAll('_','-')}">${STATUS_LABELS[status] || status}</span></div>
    </div>

    ${strongest ? `<p class="dna-signature"><span>Prägende DNA</span><strong>${strongest}</strong></p>` : ''}
    ${bars(values)}

    <div class="dna-evidence">
      <div><span>Vertrauen</span><b>${percentText(metadata.confidence)}</b></div>
      <div><span>Quellen</span><b>${sourceCount == null ? 'Noch offen' : `${sourceCount} ${sourceCount === 1 ? 'Quelle' : 'Quellen'}`}</b></div>
      <div><span>Abweichung</span><b>${percentText(metadata.disagreement)}</b></div>
      <div><span>Datenstand</span><b>${researchedAt}</b></div>
    </div>

    <div class="personal-dna ${availableValues(data?.personal_values).length ? '' : 'is-empty'}">
      <div><span>Meine Duft-DNA</span><h3>Persönliche Wahrnehmung</h3><p>Bleibt vollständig von Recherche- und Community-Werten getrennt.</p></div>
      ${bars(data?.personal_values, true)}
    </div>
  </section>`;
}

let activeId = '';
let requestToken = 0;

async function syncDnaCard() {
  const id = new URLSearchParams(window.location.search).get('fragrance') || '';
  const detailContent = document.querySelector('.catalog-detail .detail-content');
  if (!id || !detailContent) return;
  if (activeId === id && detailContent.querySelector(`[data-dna-fragrance="${id}"]`)) return;

  const token = ++requestToken;
  try {
    const response = await fetch(`/api/fragrances/${encodeURIComponent(id)}/dna`);
    if (!response.ok) return;
    const data = await response.json();
    if (token !== requestToken) return;

    detailContent.querySelectorAll('.dna-card').forEach(node => node.remove());
    const anchor = detailContent.querySelector('.performance-card') || detailContent.querySelector('.detail-facts');
    if (!anchor) return;
    anchor.insertAdjacentHTML('afterend', renderCard(data, id));
    activeId = id;
  } catch {
    // Das Duftprofil bleibt nutzbar, wenn die Zusatzkarte nicht geladen werden kann.
  }
}

const observer = new MutationObserver(syncDnaCard);
observer.observe(document.documentElement, {childList:true, subtree:true});
window.addEventListener('popstate', () => { activeId = ''; syncDnaCard(); });
syncDnaCard();
