const DNA_LABELS = {
  fresh:'Frisch', citrus:'Zitrisch', green:'Grün', aquatic:'Aquatisch', floral:'Floral', fruity:'Fruchtig',
  sweet:'Süß', gourmand:'Gourmandig', spicy:'Würzig', woody:'Holzig', smoky:'Rauchig', earthy:'Erdig',
  resinous:'Harzig', leathery:'Ledrig', powdery:'Pudrig', animalic:'Animalisch',
};

async function dnaProposalRequest(url, options = {}) {
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

function dnaProposalToast(message) {
  let node = document.querySelector('.dna-proposal-toast');
  if (!node) {
    node = document.createElement('div');
    node.className = 'dna-proposal-toast';
    document.body.appendChild(node);
  }
  node.textContent = message;
  node.classList.add('show');
  clearTimeout(node._timer);
  node._timer = setTimeout(() => node.classList.remove('show'), 3400);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
}

function proposalSourceLabel(source) {
  return ({RESEARCH:'Recherche', AI_ASSISTED:'KI-unterstützt', RULE_BASED:'Regelbasiert', MANUAL:'Manuell'})[source] || source;
}

function proposalCard(proposal, fragrances) {
  const fragrance = fragrances.find(item => item.id === proposal.fragrance_id);
  const title = fragrance ? `${fragrance.brand?.name || ''} ${fragrance.name}`.trim() : proposal.fragrance_id;
  const values = Object.entries(proposal.values || {});
  const date = proposal.created_at ? new Date(proposal.created_at).toLocaleString('de-DE') : '–';
  return `<article class="dna-proposal-card" data-proposal-id="${proposal.id}">
    <header>
      <div><small>${escapeHtml(proposalSourceLabel(proposal.source))} · ${escapeHtml(date)}</small><h3>${escapeHtml(title)}</h3></div>
      <span class="dna-proposal-confidence">${proposal.confidence == null ? 'Vertrauen offen' : `${Math.round(proposal.confidence * 100)} % Vertrauen`}</span>
    </header>
    <div class="dna-proposal-source">
      <b>${escapeHtml(proposal.source_label || 'Quelle ohne Bezeichnung')}</b>
      ${proposal.source_url ? `<a href="${escapeHtml(proposal.source_url)}" target="_blank" rel="noopener noreferrer">Quelle öffnen</a>` : ''}
    </div>
    ${proposal.rationale ? `<p class="dna-proposal-rationale">${escapeHtml(proposal.rationale)}</p>` : ''}
    <div class="dna-proposal-values">
      ${values.map(([key,value]) => `<label><input type="checkbox" checked data-proposal-dimension="${key}"><span>${escapeHtml(DNA_LABELS[key] || key)}</span><b>${Number(value).toFixed(1)}</b></label>`).join('')}
    </div>
    <label class="dna-proposal-note">Prüfnotiz<textarea rows="2" data-proposal-note placeholder="Warum wurde freigegeben oder abgelehnt?"></textarea></label>
    <div class="dna-proposal-actions">
      <button type="button" class="clear" data-proposal-reject>Ablehnen</button>
      <button type="button" class="primary" data-proposal-approve>Ausgewählte Werte freigeben</button>
    </div>
  </article>`;
}

async function renderDNAProposalWorklist(container) {
  container.innerHTML = '<div class="empty">Offene Duft-DNA-Vorschläge werden geladen …</div>';
  try {
    const [proposals, fragrances] = await Promise.all([
      dnaProposalRequest('/api/fragrance-dna/proposals?status=OPEN'),
      dnaProposalRequest('/api/fragrances'),
    ]);
    container.innerHTML = `<section class="dna-proposal-worklist">
      <div class="section-head"><div><span class="kicker">Duft-DNA-Prüfung</span><h2>${proposals.length} offene Vorschlag${proposals.length === 1 ? '' : 'e'}</h2><p>Nur ausdrücklich ausgewählte Dimensionen werden veröffentlicht.</p></div><button type="button" class="clear" data-proposal-refresh>Neu laden</button></div>
      ${proposals.length ? `<div class="dna-proposal-list">${proposals.map(item => proposalCard(item, fragrances)).join('')}</div>` : '<div class="empty">Keine offenen Duft-DNA-Vorschläge vorhanden.</div>'}
    </section>`;

    container.querySelector('[data-proposal-refresh]')?.addEventListener('click', () => renderDNAProposalWorklist(container));
    container.querySelectorAll('.dna-proposal-card').forEach(card => {
      const proposal = proposals.find(item => item.id === card.dataset.proposalId);
      card.querySelector('[data-proposal-approve]').addEventListener('click', async () => {
        const accepted = {};
        card.querySelectorAll('[data-proposal-dimension]:checked').forEach(input => {
          accepted[input.dataset.proposalDimension] = Number(proposal.values[input.dataset.proposalDimension]);
        });
        if (!Object.keys(accepted).length) return dnaProposalToast('Bitte mindestens eine Dimension zur Freigabe auswählen.');
        try {
          await dnaProposalRequest(`/api/fragrance-dna/proposals/${proposal.id}/review`, {
            method:'POST',
            body:JSON.stringify({decision:'APPROVE', accepted_values:accepted, review_note:card.querySelector('[data-proposal-note]').value || null}),
          });
          dnaProposalToast('Ausgewählte Duft-DNA-Werte wurden freigegeben.');
          await renderDNAProposalWorklist(container);
        } catch (error) { dnaProposalToast(error.message); }
      });
      card.querySelector('[data-proposal-reject]').addEventListener('click', async () => {
        if (!confirm('Diesen Duft-DNA-Vorschlag wirklich ablehnen?')) return;
        try {
          await dnaProposalRequest(`/api/fragrance-dna/proposals/${proposal.id}/review`, {
            method:'POST',
            body:JSON.stringify({decision:'REJECT', accepted_values:null, review_note:card.querySelector('[data-proposal-note]').value || null}),
          });
          dnaProposalToast('Duft-DNA-Vorschlag wurde abgelehnt.');
          await renderDNAProposalWorklist(container);
        } catch (error) { dnaProposalToast(error.message); }
      });
    });
  } catch (error) {
    container.innerHTML = `<div class="empty">Vorschläge konnten nicht geladen werden: ${escapeHtml(error.message)}</div>`;
  }
}

function injectDNAProposalTab() {
  const tabs = document.querySelector('.admin-tabs');
  if (!tabs || tabs.querySelector('[data-dna-proposal-tab]')) return;
  const button = document.createElement('button');
  button.type = 'button';
  button.dataset.dnaProposalTab = 'true';
  button.textContent = 'DNA-Vorschläge';
  tabs.appendChild(button);
  button.addEventListener('click', () => {
    tabs.querySelectorAll('button').forEach(item => item.classList.remove('active'));
    button.classList.add('active');
    const admin = document.querySelector('.admin-main');
    [...admin.children].forEach(child => {
      if (!child.classList.contains('admin-head') && !child.classList.contains('admin-tabs')) child.remove();
    });
    const host = document.createElement('div');
    host.dataset.dnaProposalHost = 'true';
    admin.appendChild(host);
    renderDNAProposalWorklist(host);
  });
}

const proposalObserver = new MutationObserver(injectDNAProposalTab);
proposalObserver.observe(document.documentElement, {childList:true, subtree:true});
injectDNAProposalTab();
