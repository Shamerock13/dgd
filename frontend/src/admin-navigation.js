const NAV_GROUPS=[
  {label:'Start',items:['Übersicht']},
  {label:'Stammdaten',items:['Düfte','Marken','Duftnoten','Parfümeure','Import']},
  {label:'Recherche',items:['Recherche','DNA-Vorschläge','Performance-KI','KI-Export','Quellen & Prüfung']},
  {label:'Qualität',items:['Arbeitsliste','Preisquellen prüfen']},
  {label:'Medien',items:['Bilder','Preise']},
  {label:'System',items:['System & Updates']},
];

const PENDING_ENDPOINTS={
  'Recherche':['/api/enrichment/tasks?status=PENDING','/api/enrichment/twin-suggestions?status=PENDING'],
  'Quellen & Prüfung':['/api/enrichment/findings?status=PENDING'],
  'DNA-Vorschläge':['/api/fragrance-dna/proposals?status=OPEN'],
  'Performance-KI':['/api/performance-research/proposals?status=OPEN'],
  'Preisquellen prüfen':['/api/prices/review/offers?status=PENDING_REVIEW&limit=1'],
};

function nativeTabLabel(button){return button.textContent.replace(/\s+\d+\s*$/,'').trim()}
function nativeTabs(){return [...document.querySelectorAll('.admin-tabs button')]}
function findNativeTab(label){return nativeTabs().find(button=>nativeTabLabel(button)===label)}
async function navCount(url){try{const response=await fetch(url);if(!response.ok)return 0;const data=await response.json();if(Array.isArray(data))return data.length;if(Number.isFinite(Number(data?.count)))return Number(data.count);if(Number.isFinite(Number(data?.summary?.pending)))return Number(data.summary.pending);return 0}catch{return 0}}
async function loadPendingCounts(){const result={};await Promise.all(Object.entries(PENDING_ENDPOINTS).map(async([label,urls])=>{const values=await Promise.all(urls.map(navCount));result[label]=values.reduce((sum,value)=>sum+value,0)}));return result}
function copiedCount(button){return button?.querySelector('b')?.textContent?.trim()||''}
function syncActiveState(){const shell=document.querySelector('[data-admin-navigation]');if(!shell)return;shell.querySelectorAll('[data-admin-nav-target]').forEach(button=>{const active=Boolean(findNativeTab(button.dataset.adminNavTarget)?.classList.contains('active'));button.classList.toggle('active',active);button.setAttribute('aria-current',active?'page':'false')})}
let rendering=false;
async function renderNavigation(){const shell=document.querySelector('[data-admin-navigation]');if(!shell||rendering)return;rendering=true;try{const pending=await loadPendingCounts();shell.innerHTML=NAV_GROUPS.map(group=>{const items=group.items.map(label=>{const source=findNativeTab(label);if(!source)return '';const count=pending[label]??copiedCount(source);return `<button type="button" data-admin-nav-target="${label}"><span>${label}</span>${count!==''?`<b>${count}</b>`:''}</button>`}).join('');return items?`<section class="admin-nav-group"><small>${group.label}</small><div>${items}</div></section>`:''}).join('');shell.querySelectorAll('[data-admin-nav-target]').forEach(button=>{button.addEventListener('click',()=>{const target=findNativeTab(button.dataset.adminNavTarget);if(!target)return;target.click();requestAnimationFrame(syncActiveState)})});syncActiveState()}finally{rendering=false}}
let observedTabs=null;let tabsObserver=null;
function bindNativeTabs(tabs){if(observedTabs===tabs)return;tabsObserver?.disconnect();observedTabs=tabs;tabsObserver=new MutationObserver(()=>renderNavigation());tabsObserver.observe(tabs,{childList:true});tabs.addEventListener('click',()=>requestAnimationFrame(syncActiveState))}
function ensureNavigation(){const tabs=document.querySelector('.admin-tabs');if(!tabs)return;let shell=document.querySelector('[data-admin-navigation]');if(!shell){shell=document.createElement('nav');shell.dataset.adminNavigation='true';shell.className='admin-navigation';shell.setAttribute('aria-label','Admin-Bereiche');tabs.insertAdjacentElement('afterend',shell)}tabs.classList.add('admin-tabs-native');bindNativeTabs(tabs);renderNavigation()}
const rootObserver=new MutationObserver(()=>{if(!document.querySelector('[data-admin-navigation]')||document.querySelector('.admin-tabs')!==observedTabs)ensureNavigation()});rootObserver.observe(document.documentElement,{childList:true,subtree:true});ensureNavigation();setInterval(()=>renderNavigation(),30000);
