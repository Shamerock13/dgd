const SECTION_MARKERS=[
  {before:'Name *',title:'Stammdaten',copy:'Name, Marke, Jahr, Zielgruppe, Konzentration, Parfümeur und Preis.'},
  {before:'Bild-URL',title:'Bild & Herkunft',copy:'Bilddatei, Quelle, Status und Rechtehinweise.'},
  {before:'Beschreibung',title:'Beschreibung',copy:'Öffentlicher Beschreibungstext des Duftes.'},
  {before:'Kopfnoten',title:'Duftpyramide',copy:'Kopf-, Herz- und Basisnoten strukturiert zuordnen.'},
  {before:'Akkorde, kommagetrennt',title:'Akkorde & Charakter',copy:'Akkorde und die sichtbaren Charakterwerte pflegen.'},
];
const RESEARCH_FIELDS=[
  ['Jahr','Erscheinungsjahr'],['Konzentration','Konzentration'],['Parfümeur','Parfümeur'],
  ['Bild-URL','Produktbild'],['Bildquelle','Bildquelle'],['Beschreibung','Beschreibung'],
  ['Akkorde, kommagetrennt','Akkorde'],['Kopfnoten','Kopfnoten'],['Herznoten','Herznoten'],['Basisnoten','Basisnoten']
];
function editorLabel(node){return node?.querySelector(':scope > span, :scope > label')?.textContent?.trim()||node?.textContent?.trim().split('\n')[0]||''}
function fieldByLabel(form,label){return [...form.querySelectorAll('.field, label')].find(node=>editorLabel(node)===label)}
function fieldValue(field){const input=field?.querySelector('input,textarea,select');if(input)return String(input.value||'').trim();return field?.querySelector('.note-picker-selection,.chips')?.textContent?.trim()||''}
function removeEnhancements(form){form.querySelectorAll('[data-editor-section],[data-editor-research],[data-editor-save-state]').forEach(node=>node.remove())}
function insertSection(form,marker){const field=fieldByLabel(form,marker.before);if(!field)return;const section=document.createElement('div');section.dataset.editorSection='true';section.className='fragrance-editor-section';section.innerHTML=`<div><span>Duftbearbeitung</span><h3>${marker.title}</h3><p>${marker.copy}</p></div>`;field.parentElement?.insertBefore(section,field)}
function missingResearch(form){return RESEARCH_FIELDS.filter(([label])=>!fieldValue(fieldByLabel(form,label))).map(([,name])=>name)}
function updateResearchPanel(form,panel){const missing=missingResearch(form);panel.innerHTML=`<div><span>KI-Recherchebedarf</span><h3>${missing.length?`${missing.length} Bereiche noch offen`:'Keine offensichtlichen Datenlücken'}</h3><p>${missing.length?'Diese Angaben können durch die Daten- oder Bildrecherche ergänzt werden. Persönliche Bewertungen bleiben manuell.':'Die sichtbaren Kernfelder sind befüllt.'}</p></div>${missing.length?`<div class="research-field-chips">${missing.map(name=>`<span>${name}</span>`).join('')}</div>`:''}`}
function enhanceEditor(){
  const form=document.querySelector('.admin-grid form.editor');if(!form||form.dataset.fragranceEditorEnhanced==='true')return;
  form.dataset.fragranceEditorEnhanced='true';removeEnhancements(form);
  SECTION_MARKERS.forEach(marker=>insertSection(form,marker));
  const title=form.querySelector('.editor-title');
  const panel=document.createElement('section');panel.dataset.editorResearch='true';panel.className='fragrance-editor-research';title?.insertAdjacentElement('afterend',panel);updateResearchPanel(form,panel);
  const state=document.createElement('span');state.dataset.editorSaveState='true';state.className='fragrance-editor-save-state';state.textContent='Keine ungespeicherten Änderungen';title?.appendChild(state);
  let dirty=false;
  const markDirty=()=>{dirty=true;state.textContent='Ungespeicherte Änderungen';state.classList.add('dirty');updateResearchPanel(form,panel)};
  form.addEventListener('input',markDirty);form.addEventListener('change',markDirty);
  form.addEventListener('submit',()=>{dirty=false;state.textContent='Wird gespeichert …';state.classList.remove('dirty')});
  window.addEventListener('beforeunload',event=>{if(!dirty)return;event.preventDefault();event.returnValue=''});
}
let timer=null;
const observer=new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(()=>{const form=document.querySelector('.admin-grid form.editor');if(form&&!form.dataset.fragranceEditorEnhanced)enhanceEditor()},60)});
observer.observe(document.documentElement,{childList:true,subtree:true});enhanceEditor();