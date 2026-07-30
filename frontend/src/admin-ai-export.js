function aiExportToast(message){let node=document.querySelector('.ai-export-toast');if(!node){node=document.createElement('div');node.className='ai-export-toast';document.body.appendChild(node)}node.textContent=message;node.classList.add('show');clearTimeout(node._timer);node._timer=setTimeout(()=>node.classList.remove('show'),3200)}

function renderAiExport(host){
  host.innerHTML=`<section class="ai-export-panel">
    <div class="section-head"><div><span class="kicker">Paket 16.7.1</span><h2>KI-Recherche exportieren</h2><p>Erzeugt eine Excel-Datei mit allen recherchierbaren Duftdaten. Persönliche Bewertungen bleiben ausgeschlossen.</p></div></div>
    <div class="ai-export-options">
      <label><span>Umfang</span><select data-ai-export-scope><option value="missing">Nur Düfte mit Datenlücken</option><option value="all">Alle Düfte</option></select></label>
      <label><span>Marke optional</span><select data-ai-export-brand><option value="">Alle Marken</option></select></label>
    </div>
    <div class="ai-export-summary">
      <b>Enthaltene Tabellenblätter</b>
      <p>Düfte · Noten · Performance · Duft-DNA · Bilder_Quellen · Preisquellen · Quellen · Anleitung · Metadaten</p>
    </div>
    <div class="ai-export-actions"><button type="button" class="primary" data-ai-export-download>Excel-Datei erstellen</button></div>
    <p class="ai-export-note">Der Rückimport ist noch nicht aktiv. Diese Stufe dient zuerst dazu, Struktur und Feldumfang der Exportdatei zu prüfen.</p>
  </section>`;
  fetch('/api/brands').then(r=>r.ok?r.json():[]).then(brands=>{const select=host.querySelector('[data-ai-export-brand]');brands.sort((a,b)=>a.name.localeCompare(b.name,'de')).forEach(brand=>{const option=document.createElement('option');option.value=brand.id;option.textContent=brand.name;select.appendChild(option)})}).catch(()=>{});
  host.querySelector('[data-ai-export-download]').addEventListener('click',event=>{const scope=host.querySelector('[data-ai-export-scope]').value;const brand=host.querySelector('[data-ai-export-brand]').value;const params=new URLSearchParams({scope});if(brand)params.set('brand_id',brand);event.currentTarget.disabled=true;event.currentTarget.textContent='Export wird erstellt …';window.location.href=`/api/ai-research-export/xlsx?${params}`;setTimeout(()=>{event.currentTarget.disabled=false;event.currentTarget.textContent='Excel-Datei erstellen';aiExportToast('Export wurde angefordert.')},1200)});
}

function injectAiExportTab(){
  const tabs=document.querySelector('.admin-tabs');
  if(!tabs||tabs.querySelector('[data-ai-export-tab]'))return;
  const button=document.createElement('button');button.type='button';button.dataset.aiExportTab='true';button.textContent='KI-Export';tabs.appendChild(button);
  button.addEventListener('click',()=>{tabs.querySelectorAll('button').forEach(item=>item.classList.remove('active'));button.classList.add('active');const admin=document.querySelector('.admin-main');if(!admin)return;[...admin.children].forEach(child=>{if(!child.classList.contains('admin-head')&&!child.classList.contains('admin-tabs')&&!child.matches('[data-admin-navigation]'))child.remove()});const host=document.createElement('div');host.dataset.aiExportHost='true';admin.appendChild(host);renderAiExport(host)});
}
const aiExportObserver=new MutationObserver(injectAiExportTab);aiExportObserver.observe(document.documentElement,{childList:true,subtree:true});injectAiExportTab();
