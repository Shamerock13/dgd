const NAV_GROUPS=[
  {label:'Start',items:['Übersicht']},
  {label:'Stammdaten',items:['Düfte','Marken','Duftnoten','Parfümeure','Import']},
  {label:'Recherche',items:['Recherche','DNA-Vorschläge','Performance-KI','Quellen & Prüfung']},
  {label:'Qualität',items:['Arbeitsliste']},
  {label:'Medien',items:['Bilder','Preise']},
  {label:'System',items:['System & Updates']},
];

const PENDING_ENDPOINTS={
  'Recherche':['/api/enrichment/tasks?status=PENDING','/api/enrichment/twin-suggestions?status=PENDING'],
  'Quellen & Prüfung':['/api/enrichment/findings?status=PENDING'],
  'DNA-Vorschläge':['/api/fragrance-dna/proposals?status=OPEN'],
  'Performance-KI':['/api/performance-research/proposals?status=OPEN'],
};

function nativeTabLabel(button){
  return button.textContent.replace(/\s+\d+\s*$/,'').trim();
}

function findNativeTab(label){
  return [...document.querySelectorAll('.admin-tabs button')].find(button=>nativeTabLabel(button)===label);
}

async function navCount(url){
  try{const response=await fetch(url);if(!response.ok)return 0;const data=await response.json();return Array.isArray(data)?data.length:Number(data?.count||0)}catch{return 0}
}

async function loadPendingCounts(){
  const result={};
  await Promise.all(Object.entries(PENDING_ENDPOINTS).map(async([label,urls])=>{
    const values=await Promise.all(urls.map(navCount));
    result[label]=values.reduce((sum,value)=>sum+value,0);
  }));
  return result;
}

function copiedCount(button){
  const badge=button?.querySelector('b');
  return badge?.textContent?.trim()||'';
}

function syncActiveState(shell){
  shell.querySelectorAll('[data-admin-nav-target]').forEach(button=>{
    const source=findNativeTab(button.dataset.adminNavTarget);
    button.classList.toggle('active',Boolean(source?.classList.contains('active')));
    button.setAttribute('aria-current',source?.classList.contains('active')?'page':'false');
  });
}

async function renderNavigation(shell){
  const pending=await loadPendingCounts();
  shell.innerHTML=NAV_GROUPS.map(group=>{
    const items=group.items.map(label=>{
      const source=findNativeTab(label);
      if(!source)return '';
      const count=pending[label]??copiedCount(source);
      return `<button type="button" data-admin-nav-target="${label}" class="${source.classList.contains('active')?'active':''}"><span>${label}</span>${count!==''?`<b>${count}</b>`:''}</button>`;
    }).join('');
    return items?`<section class="admin-nav-group"><small>${group.label}</small><div>${items}</div></section>`:'';
  }).join('');
  shell.querySelectorAll('[data-admin-nav-target]').forEach(button=>button.addEventListener('click',()=>findNativeTab(button.dataset.adminNavTarget)?.click()));
  syncActiveState(shell);
}

function ensureNavigation(){
  const tabs=document.querySelector('.admin-tabs');
  if(!tabs)return;
  let shell=document.querySelector('[data-admin-navigation]');
  if(!shell){
    shell=document.createElement('nav');
    shell.dataset.adminNavigation='true';
    shell.className='admin-navigation';
    shell.setAttribute('aria-label','Admin-Bereiche');
    tabs.insertAdjacentElement('afterend',shell);
  }
  tabs.classList.add('admin-tabs-native');
  renderNavigation(shell);
}

let scheduled=false;
const observer=new MutationObserver(()=>{
  if(scheduled)return;
  scheduled=true;
  requestAnimationFrame(()=>{scheduled=false;ensureNavigation();const shell=document.querySelector('[data-admin-navigation]');if(shell)syncActiveState(shell)});
});
observer.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
ensureNavigation();
setInterval(()=>{const shell=document.querySelector('[data-admin-navigation]');if(shell)renderNavigation(shell)},30000);
