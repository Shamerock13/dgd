async function overviewRequest(url){const response=await fetch(url);if(!response.ok)throw new Error(`Fehler ${response.status}`);return response.json()}
function overviewEscape(value){return String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
async function overviewSafe(url,fallback=[]){try{return await overviewRequest(url)}catch{return fallback}}
function adminButtonByText(label){return [...document.querySelectorAll('.admin-tabs button')].find(button=>button.textContent.trim().startsWith(label))}
function restoreAdminContent(){
  document.querySelector('[data-admin-overview-host]')?.remove();
  document.querySelectorAll('.admin-main > [data-admin-overview-hidden="true"]').forEach(child=>{
    child.style.removeProperty('display');
    delete child.dataset.adminOverviewHidden;
  });
}
function openAdminTarget(target){
  restoreAdminContent();
  const external=document.querySelector(target);
  if(external){external.click();return}
  adminButtonByText(target)?.click();
}
function dashboardCard({tone,label,value,copy,target}){return `<button type="button" class="admin-overview-card ${tone}" data-admin-overview-target="${overviewEscape(target)}"><span>${overviewEscape(label)}</span><strong>${value}</strong><p>${overviewEscape(copy)}</p><b>Arbeitsbereich öffnen →</b></button>`}
async function renderAdminOverview(container){
  container.innerHTML='<div class="empty">Admin-Übersicht wird geladen …</div>';
  const [fragrances,findings,tasks,dna,performance,twins]=await Promise.all([
    overviewSafe('/api/fragrances'),overviewSafe('/api/enrichment/findings?status=PENDING'),overviewSafe('/api/enrichment/tasks?status=PENDING'),overviewSafe('/api/fragrance-dna/proposals?status=OPEN'),overviewSafe('/api/performance-research/proposals?status=OPEN'),overviewSafe('/api/enrichment/twin-suggestions?status=PENDING')
  ]);
  const missingImages=fragrances.filter(item=>!item.image_url||item.image_status==='BROKEN').length;
  const missingPerformance=fragrances.filter(item=>item.performance_status==='OPEN'&&item.performance_score==null&&item.longevity_score==null).length;
  const missingDna=fragrances.filter(item=>!item.fragrance_dna||!Object.keys(item.fragrance_dna).length).length;
  const cards=[
    {tone:'research',label:'Offene Datenlücken',value:tasks.length,copy:'Stammdaten, Quellen, Noten oder Akkorde fehlen noch.','target':'Quellen & Prüfung'},
    {tone:'review',label:'Gefundene Daten prüfen',value:findings.length,copy:'Gemini-Funde warten auf Übernahme, Konflikt oder Ablehnung.','target':'Quellen & Prüfung'},
    {tone:'dna',label:'Offene DNA-Vorschläge',value:dna.length,copy:`${missingDna} Düfte besitzen noch keine veröffentlichte Duft-DNA.`,'target':'[data-dna-proposal-tab]'},
    {tone:'performance',label:'Offene Performance-Vorschläge',value:performance.length,copy:`${missingPerformance} Düfte benötigen noch Performance-Recherche.`,'target':'[data-performance-research-tab]'},
    {tone:'twins',label:'Duftzwillingsuche',value:twins.length,copy:'Duftzwillinge bleiben getrennt von der normalen Datenrecherche.','target':'Recherche'},
    {tone:'images',label:'Fehlende oder defekte Bilder',value:missingImages,copy:'Diese Düfte brauchen Bildrecherche oder eine neue Bilddatei.','target':'Düfte'}
  ];
  const totalOpen=tasks.length+findings.length+dna.length+performance.length+twins.length+missingImages;
  container.innerHTML=`<section class="admin-overview"><div class="admin-overview-hero"><div><span class="kicker">Arbeitszentrale</span><h2>Was braucht heute Aufmerksamkeit?</h2><p>Datenrecherche, KI-Vorschläge, Duftzwillinge und Bilder bleiben bewusst getrennt.</p></div><div class="admin-overview-total"><strong>${totalOpen}</strong><span>offene Hinweise</span></div></div><div class="admin-overview-grid">${cards.map(dashboardCard).join('')}</div><section class="admin-overview-inventory"><article><strong>${fragrances.length}</strong><span>Düfte insgesamt</span></article><article><strong>${missingDna}</strong><span>ohne Duft-DNA</span></article><article><strong>${missingPerformance}</strong><span>ohne Performance</span></article><article><strong>${missingImages}</strong><span>ohne brauchbares Bild</span></article></section></section>`;
  container.querySelectorAll('[data-admin-overview-target]').forEach(button=>button.addEventListener('click',()=>openAdminTarget(button.dataset.adminOverviewTarget)));
}
function showAdminOverview(){
  const tabs=document.querySelector('.admin-tabs');const admin=document.querySelector('.admin-main');if(!tabs||!admin)return;
  restoreAdminContent();
  tabs.querySelectorAll('button').forEach(item=>item.classList.remove('active'));
  const button=tabs.querySelector('[data-admin-overview-tab]');button?.classList.add('active');
  [...admin.children].forEach(child=>{
    if(!child.classList.contains('admin-head')&&!child.classList.contains('admin-tabs')){
      child.dataset.adminOverviewHidden='true';
      child.style.display='none';
    }
  });
  const host=document.createElement('div');host.dataset.adminOverviewHost='true';admin.appendChild(host);renderAdminOverview(host);
}
function bindNativeTabRestore(tabs){
  tabs.querySelectorAll('button:not([data-admin-overview-tab])').forEach(button=>{
    if(button.dataset.adminOverviewRestoreBound)return;
    button.dataset.adminOverviewRestoreBound='true';
    button.addEventListener('click',restoreAdminContent,{capture:true});
  });
}
function injectAdminOverview(){
  const tabs=document.querySelector('.admin-tabs');if(!tabs)return;
  bindNativeTabRestore(tabs);
  if(tabs.querySelector('[data-admin-overview-tab]'))return;
  const button=document.createElement('button');button.type='button';button.dataset.adminOverviewTab='true';button.textContent='Übersicht';button.addEventListener('click',showAdminOverview);tabs.prepend(button);showAdminOverview();
}
const adminOverviewObserver=new MutationObserver(injectAdminOverview);adminOverviewObserver.observe(document.documentElement,{childList:true,subtree:true});injectAdminOverview();