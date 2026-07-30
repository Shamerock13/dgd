const PERFORMANCE_LABELS = {
  longevity_min_hours:'Haltbarkeit mindestens', longevity_max_hours:'Haltbarkeit höchstens',
  longevity_score:'Haltbarkeit', projection:'Projektion', projection_first_hour:'Erste Stunde',
  projection_after_three_hours:'Nach drei Stunden', sillage:'Sillage', drydown_strength:'Drydown',
  performance_score:'Gesamtleistung', performance_source_count:'Quellenanzahl',
  performance_confidence:'Vertrauen', performance_disagreement:'Quellenabweichung',
  performance_version:'Version / Reformulierung', performance_production_period:'Produktionszeitraum',
};

async function performanceRequest(url, options={}) {
  const response=await fetch(url,{headers:{'Content-Type':'application/json',...(options.headers||{})},...options});
  if(!response.ok){let message=`Fehler ${response.status}`;try{message=(await response.json()).detail||message}catch{}throw new Error(message)}
  return response.status===204?null:response.json();
}

function perfEscape(value){return String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function perfTitle(item){return `${item.brand?.name||''} ${item.name||''}`.trim()}
function perfValue(key,value){
  if(value==null)return '–';
  if(key.includes('confidence')||key.includes('disagreement'))return `${Math.round(Number(value)*100)} %`;
  if(key.includes('hours'))return `${Number(value).toFixed(1)} h`;
  if(typeof value==='number')return Number(value).toFixed(1);
  return String(value);
}
function perfToast(message){let node=document.querySelector('.performance-research-toast');if(!node){node=document.createElement('div');node.className='performance-research-toast';document.body.appendChild(node)}node.textContent=message;node.classList.add('show');clearTimeout(node._timer);node._timer=setTimeout(()=>node.classList.remove('show'),3400)}

function perfCard(proposal){
  const values=Object.entries(proposal.values||{});
  return `<article class="performance-proposal-card" data-performance-proposal="${proposal.id}">
    <header><div><small>${perfEscape(proposal.brand_name)} · Performance-Vorschlag</small><h3>${perfEscape(proposal.fragrance_name)}</h3></div><strong>${proposal.confidence==null?'Vertrauen offen':`${Math.round(proposal.confidence*100)} %`}</strong></header>
    ${proposal.rationale?`<p>${perfEscape(proposal.rationale)}</p>`:''}
    ${proposal.source_url?`<a href="${perfEscape(proposal.source_url)}" target="_blank" rel="noopener noreferrer">${perfEscape(proposal.source_label||'Quelle öffnen')}</a>`:''}
    <div class="performance-proposal-values">${values.map(([key,value])=>`<label><input type="checkbox" checked data-performance-field="${key}"><span>${perfEscape(PERFORMANCE_LABELS[key]||key)}</span><b>${perfEscape(perfValue(key,value))}</b></label>`).join('')}</div>
    <label class="performance-review-note">Prüfnotiz<textarea rows="2" data-performance-note></textarea></label>
    <footer><button type="button" class="clear" data-performance-reject>Ablehnen</button><button type="button" class="primary" data-performance-approve>Ausgewählte Werte freigeben</button></footer>
  </article>`;
}

async function renderPerformanceResearch(container){
  container.innerHTML='<div class="empty">Performance-Recherche wird geladen …</div>';
  try{
    const [proposals,fragrances]=await Promise.all([performanceRequest('/api/performance-research/proposals?status=OPEN'),performanceRequest('/api/fragrances')]);
    const sorted=[...fragrances].sort((a,b)=>perfTitle(a).localeCompare(perfTitle(b),'de'));
    container.innerHTML=`<section class="performance-research-worklist">
      <div class="section-head"><div><span class="kicker">Performance-Recherche</span><h2>${proposals.length} offene Vorschlag${proposals.length===1?'':'e'}</h2><p>Haltbarkeit, Projektion, Sillage und zeitlicher Verlauf werden getrennt geprüft.</p></div><button class="clear" data-performance-refresh>Neu laden</button></div>
      <section class="performance-research-start"><div><span class="kicker">Gemini mit Google Search</span><h3>Performance eines Duftes recherchieren</h3><p>Nicht belegbare Werte bleiben leer. Persönliche Bewertungen werden niemals verändert.</p></div><div><select data-performance-fragrance><option value="">Duft auswählen …</option>${sorted.map(item=>`<option value="${item.id}">${perfEscape(perfTitle(item))}</option>`).join('')}</select><button class="primary" data-performance-start>Performance recherchieren</button></div></section>
      ${proposals.length?`<div class="performance-proposal-list">${proposals.map(perfCard).join('')}</div>`:'<div class="empty">Keine offenen Performance-Vorschläge.</div>'}
    </section>`;
    container.querySelector('[data-performance-refresh]')?.addEventListener('click',()=>renderPerformanceResearch(container));
    container.querySelector('[data-performance-start]')?.addEventListener('click',async event=>{const select=container.querySelector('[data-performance-fragrance]');if(!select.value)return perfToast('Bitte zuerst einen Duft auswählen.');event.currentTarget.disabled=true;event.currentTarget.textContent='Recherche läuft …';try{await performanceRequest(`/api/performance-research/research/${select.value}`,{method:'POST'});perfToast('Performance-Vorschlag wurde erstellt.');await renderPerformanceResearch(container)}catch(error){perfToast(error.message);event.currentTarget.disabled=false;event.currentTarget.textContent='Performance recherchieren'}});
    container.querySelectorAll('[data-performance-proposal]').forEach(card=>{const proposal=proposals.find(item=>item.id===card.dataset.performanceProposal);card.querySelector('[data-performance-approve]').addEventListener('click',async()=>{const accepted={};card.querySelectorAll('[data-performance-field]:checked').forEach(input=>accepted[input.dataset.performanceField]=proposal.values[input.dataset.performanceField]);if(!Object.keys(accepted).length)return perfToast('Bitte mindestens einen Wert auswählen.');try{await performanceRequest(`/api/performance-research/proposals/${proposal.id}/review`,{method:'POST',body:JSON.stringify({decision:'APPROVE',accepted_values:accepted,review_note:card.querySelector('[data-performance-note]').value||null})});perfToast('Performance-Werte wurden freigegeben.');await renderPerformanceResearch(container)}catch(error){perfToast(error.message)}});card.querySelector('[data-performance-reject]').addEventListener('click',async()=>{if(!confirm('Diesen Performance-Vorschlag wirklich ablehnen?'))return;try{await performanceRequest(`/api/performance-research/proposals/${proposal.id}/review`,{method:'POST',body:JSON.stringify({decision:'REJECT',accepted_values:null,review_note:card.querySelector('[data-performance-note]').value||null})});perfToast('Performance-Vorschlag wurde abgelehnt.');await renderPerformanceResearch(container)}catch(error){perfToast(error.message)}})});
  }catch(error){container.innerHTML=`<div class="empty">Performance-Recherche konnte nicht geladen werden: ${perfEscape(error.message)}</div>`}
}

function injectPerformanceTab(){
  const tabs=document.querySelector('.admin-tabs');
  if(!tabs||tabs.querySelector('[data-performance-research-tab]'))return;
  const button=document.createElement('button');button.type='button';button.dataset.performanceResearchTab='true';button.textContent='Performance-KI';tabs.appendChild(button);
  button.addEventListener('click',()=>{tabs.querySelectorAll('button').forEach(item=>item.classList.remove('active'));button.classList.add('active');const admin=document.querySelector('.admin-main');[...admin.children].forEach(child=>{if(!child.classList.contains('admin-head')&&!child.classList.contains('admin-tabs'))child.remove()});const host=document.createElement('div');host.dataset.performanceResearchHost='true';admin.appendChild(host);renderPerformanceResearch(host)});
}
const performanceObserver=new MutationObserver(injectPerformanceTab);performanceObserver.observe(document.documentElement,{childList:true,subtree:true});injectPerformanceTab();
