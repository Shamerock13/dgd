import React, {useEffect, useMemo, useState} from 'react';
import {AlertTriangle, Check, Eraser, ExternalLink, Pencil, Plus, RefreshCw, Save, ShieldCheck, Sparkles, Trash2, X} from 'lucide-react';
import './verification.css';

const emptySource={name:'',object_type:'FRAGRANCE',object_id:'',source_type:'OFFICIAL',file_or_url:'',source_date:'',usage_status:'OPEN',trust_status:'OPEN',note:''};
const fieldLabels={year:'Erscheinungsjahr',concentration:'Konzentration',perfumer:'Parfümeur',description:'Beschreibung',image:'Bild',image_url:'Bild',source:'Quelle',notes:'Duftpyramide',top_notes:'Kopfnote',heart_notes:'Herznote',base_notes:'Basisnote',accords:'Akkorde'};
const displayValue=value=>value===null||value===undefined||value===''?'Noch leer':typeof value==='object'?JSON.stringify(value):String(value);
const formatRunTime=value=>value?new Intl.DateTimeFormat('de-DE',{dateStyle:'short',timeStyle:'short'}).format(new Date(value)):'–';
const isRecentRun=run=>run?.status==='SUCCESS'&&Date.now()-new Date(run.created_at).getTime()<15*60*1000;

export default function VerificationAdmin({api,flash,brands=[],items=[],twins=[]}){
  const [sources,setSources]=useState([]);
  const [summary,setSummary]=useState(null);
  const [profiles,setProfiles]=useState([]);
  const [tasks,setTasks]=useState([]);
  const [findings,setFindings]=useState([]);
  const [researchHistory,setResearchHistory]=useState({});
  const [form,setForm]=useState(emptySource);
  const [editing,setEditing]=useState(null);
  const [filter,setFilter]=useState('ALL');
  const [loading,setLoading]=useState(false);
  const [researchingTask,setResearchingTask]=useState(null);
  const [brandId,setBrandId]=useState('');
  const [researchingBrand,setResearchingBrand]=useState(false);
  const [cleanup,setCleanup]=useState(null);
  const [cleaning,setCleaning]=useState(false);

  const load=async()=>{
    setLoading(true);
    try{
      const [rows,stats,profileRows,taskRows,findingRows,historyRows]=await Promise.all([
        api('/api/sources'),
        api('/api/verification/summary'),
        api('/api/enrichment/source-profiles'),
        api('/api/enrichment/tasks?status=PENDING'),
        api('/api/enrichment/findings?status=PENDING'),
        api('/api/enrichment/research-history?limit=500'),
      ]);
      setSources(Array.isArray(rows)?rows:[]);
      setSummary(stats);
      setProfiles(Array.isArray(profileRows)?profileRows:[]);
      setTasks(Array.isArray(taskRows)?taskRows:[]);
      setFindings(Array.isArray(findingRows)?findingRows:[]);
      setResearchHistory(Object.fromEntries((Array.isArray(historyRows)?historyRows:[]).map(row=>[row.fragrance_id,row])));
    }catch(e){flash(e.message)}finally{setLoading(false)}
  };

  useEffect(()=>{load()},[]);
  useEffect(()=>setForm(editing?{...emptySource,...editing,source_date:editing.source_date?.slice(0,10)||''}:emptySource),[editing]);

  const targets=useMemo(()=>{
    const brandRows=Array.isArray(brands)?brands:[];
    const fragranceRows=Array.isArray(items)?items:[];
    const twinRows=Array.isArray(twins)?twins:[];
    if(form.object_type==='BRAND')return brandRows.filter(x=>x?.id).map(x=>({id:x.id,label:x.name||'Unbenannte Marke'}));
    if(form.object_type==='TWIN')return twinRows.filter(x=>x?.id).map(x=>({id:x.id,label:`${x.original?.name||x.original_name||'Unbekannt'} → ${x.alternative?.name||x.alternative_name||'Unbekannt'}`}));
    return fragranceRows.filter(x=>x?.id).map(x=>({id:x.id,label:`${x.brand?.name||x.brand_name||'Unbekannte Marke'} – ${x.name||'Unbenannter Duft'}`}));
  },[form.object_type,brands,items,twins]);

  const visible=filter==='ALL'?sources:sources.filter(source=>source.trust_status===filter);
  const installProfiles=async()=>{try{const result=await api('/api/enrichment/source-profiles/install-defaults',{method:'POST'});flash(`${result.installed} Quellenprofile installiert oder aktualisiert.`);await load()}catch(e){flash(e.message)}};
  const refreshGaps=async()=>{try{const result=await api('/api/enrichment/scan-gaps',{method:'POST'});flash(`${result.created+result.updated} Datenaufträge aktualisiert.`);await load()}catch(e){flash(e.message)}};

  const researchTask=async task=>{
    const recent=isRecentRun(researchHistory[task.fragrance_id]);
    if(recent&&!confirm('Dieser Duft wurde vor weniger als 15 Minuten recherchiert. Trotzdem erneut Tokens verbrauchen?'))return;
    setResearchingTask(task.fragrance_id);
    try{
      const result=await api(`/api/enrichment/tasks/${task.fragrance_id}/research?force=${recent?'true':'false'}`,{method:'POST'});
      flash(`${result.findings_created||0} Ergänzungen, ${result.twins_created||0} Twin-Hinweise, ${result.sources_found||0} Quellen; ${result.total_tokens||0} Tokens.`);
      await load();
    }catch(e){flash(e.message)}finally{setResearchingTask(null)}
  };

  const researchBrand=async()=>{
    if(!brandId)return;
    setResearchingBrand(true);
    try{
      const result=await api(`/api/enrichment/brands/${brandId}/research-fragrances?limit=15`,{method:'POST'});
      flash(`${result.created||0} neue Düfte vorgeschlagen, ${result.skipped_existing||0} bereits bekannte übersprungen.`);
      await load();
    }catch(e){flash(e.message)}finally{setResearchingBrand(false)}
  };

  const runCleanup=async apply=>{
    if(apply&&!confirm(`${cleanup?.total_changes||0} Bereinigungen jetzt dauerhaft anwenden?`))return;
    setCleaning(true);
    try{
      const result=await api(`/api/enrichment/cleanup-existing-values?dry_run=${apply?'false':'true'}`,{method:'POST'});
      setCleanup(result);
      flash(apply?`${result.total_changes||0} Bereinigungen angewendet.`:`${result.total_changes||0} mögliche Bereinigungen gefunden.`);
      if(apply)await load();
    }catch(e){flash(e.message)}finally{setCleaning(false)}
  };

  const decideFinding=async(id,action)=>{try{await api(`/api/enrichment/findings/${id}/${action}`,{method:'POST',body:JSON.stringify({note:null})});flash(action==='approve'?'Gefundenen Wert übernommen.':action==='conflict'?'Als Konflikt markiert.':'Fund abgelehnt.');await load()}catch(e){flash(e.message)}};
  const save=async e=>{e.preventDefault();const payload={...form,object_id:form.object_id||null,source_type:form.source_type||null,file_or_url:form.file_or_url||null,source_date:form.source_date?`${form.source_date}T00:00:00`:null,note:form.note||null};try{await api(editing?`/api/sources/${editing.id}`:'/api/sources',{method:editing?'PUT':'POST',body:JSON.stringify(payload)});flash(editing?'Quelle aktualisiert.':'Quelle angelegt.');setEditing(null);setForm(emptySource);await load()}catch(e){flash(e.message)}};
  const remove=async source=>{if(!confirm(`Quelle „${source.name}“ wirklich löschen?`))return;try{await api(`/api/sources/${source.id}`,{method:'DELETE'});flash('Quelle gelöscht.');await load()}catch(e){flash(e.message)}};

  return <div className="verification-admin">
    <section className="verification-summary"><article><strong>{summary?.sources??'–'}</strong><span>Quellen</span></article><article className="trusted"><strong>{summary?.trusted??'–'}</strong><span>Vertrauenswürdig</span></article><article><strong>{findings.length}</strong><span>Datenfunde in Prüfung</span></article><article><strong>{tasks.length}</strong><span>Düfte mit Datenlücken</span></article></section>

    {!!findings.length&&<section className="verification-review-block"><div className="verification-section-head"><div><span className="kicker">Feldvergleich</span><h3>Gefundene Ergänzungen prüfen</h3><p>Bestehender Wert, gefundener Wert und Quelle direkt nebeneinander.</p></div><button type="button" onClick={load} disabled={loading}><RefreshCw size={15}/> Aktualisieren</button></div><div className="verification-finding-list">{findings.map(row=><article key={row.id}><header><div><small>{row.brand_name} · {row.fragrance_name}</small><h4>{fieldLabels[row.field_name]||row.field_name}</h4></div><strong>{Math.round(row.confidence||0)}%</strong></header><div className="finding-compare"><div><span>Aktuell</span><b>{displayValue(row.current_value)}</b></div><div><span>Gefunden</span><b>{displayValue(row.proposed_value)}</b></div></div><p>{row.source_excerpt||'Kein Textausschnitt gespeichert.'}</p><a href={row.source_url} target="_blank" rel="noreferrer">{row.source_name} öffnen <ExternalLink size={13}/></a><footer><button type="button" className="approve" onClick={()=>decideFinding(row.id,'approve')}><Check size={15}/> Übernehmen</button><button type="button" onClick={()=>decideFinding(row.id,'conflict')}><AlertTriangle size={15}/> Konflikt</button><button type="button" className="danger" onClick={()=>decideFinding(row.id,'reject')}><Trash2 size={15}/> Ablehnen</button></footer></article>)}</div></section>}

    <section className="verification-review-block"><div className="verification-section-head"><div><span className="kicker">Datenpflege</span><h3>Duftnoten und Akkorde bereinigen</h3><p>Entfernt Klammern, Anführungszeichen, JSON-Reste, Feldbezeichnungen und doppelte Einträge. Der Prüflauf verändert noch nichts.</p></div><div><button type="button" onClick={()=>runCleanup(false)} disabled={cleaning}><Eraser size={15}/>{cleaning?'Prüfung läuft …':'Prüflauf starten'}</button>{cleanup?.total_changes>0&&<button type="button" className="approve" onClick={()=>runCleanup(true)} disabled={cleaning}><Check size={15}/> {cleanup.total_changes} Änderungen anwenden</button>}</div></div>{cleanup&&<div className="verification-gap-list"><article><div><b>{cleanup.total_changes||0} Änderungen gefunden</b><span>{cleanup.fragrances?.checked||0} Düfte, {cleanup.findings?.checked||0} Recherchefunde und {cleanup.notes?.checked||0} Duftnoten geprüft</span></div><strong>{cleanup.applied?'Angewendet':'Nur Vorschau'}</strong></article>{(cleanup.sample_changes||[]).slice(0,12).map((change,index)=><article key={`${change.storage}-${change.id}-${change.field}-${index}`}><div><b>{change.fragrance||change.storage} · {fieldLabels[change.field]||change.field}</b><span>{displayValue(change.before)} → {displayValue(change.after)}</span></div><strong>{change.action==='merge'?'Zusammenführen':'Bereinigen'}</strong></article>)}</div>}</section>

    <section className="verification-review-block"><div className="verification-section-head"><div><span className="kicker">Recherche-Regeln</span><h3>Quellenprofile</h3><p>Diese Profile steuern, welche Webquellen bevorzugt, eingeschränkt oder gar nicht automatisiert verwendet werden.</p></div><div><button type="button" onClick={installProfiles}>Empfohlene Quellen hinzufügen</button><button type="button" onClick={load} disabled={loading}><RefreshCw size={15}/> Aktualisieren</button></div></div><div className="verification-profile-list">{profiles.map(profile=><article key={profile.id} className={profile.blocked?'blocked':''}><div><b>{profile.name}</b><span>{profile.domain}</span></div><strong>{profile.blocked?'Gesperrt':`Priorität ${profile.priority}`}</strong><small>{profile.category}</small><p>{profile.note}</p></article>)}</div></section>

    <section className="verification-review-block"><div className="verification-section-head"><div><span className="kicker">Datenprüfung</span><h3>Fehlende Duftdaten</h3><p>Jeder Lauf speichert Ergebnis, Quellen und Tokenverbrauch. Innerhalb von 15 Minuten ist eine bewusste Bestätigung nötig.</p></div><button type="button" onClick={refreshGaps} disabled={loading||!!researchingTask}>Datenlücken neu prüfen</button></div><div className="verification-gap-list">{tasks.map(task=>{const run=researchHistory[task.fragrance_id];const recent=isRecentRun(run);return <article key={task.id}><div><b>{task.brand_name} – {task.fragrance_name}</b><span>{(task.missing_fields||[]).map(field=>fieldLabels[field]||field).join(' · ')}</span>{run&&<small>Letzter Lauf: {formatRunTime(run.created_at)} · {(run.prompt_tokens||0)+(run.output_tokens||0)} Tokens · {run.sources_found||0} Quellen · {run.findings_created||0} Funde · {run.twins_created||0} Twins</small>}</div><strong>{(task.missing_fields||[]).length} offen</strong><button type="button" className={recent?'':'approve'} disabled={!!researchingTask} onClick={()=>researchTask(task)}><Sparkles size={15}/>{researchingTask===task.fragrance_id?'Gemini sucht …':recent?'Trotzdem erneut suchen':'Mit Gemini ergänzen'}</button></article>})}</div>{!tasks.length&&<div className="verification-empty">Aktuell sind keine offenen Datenlücken erfasst.</div>}</section>

    <section className="verification-review-block"><div className="verification-section-head"><div><span className="kicker">Markenrecherche</span><h3>Weitere Düfte einer Marke suchen</h3><p>Vorhandene und bereits vorgeschlagene Düfte werden vor der Anfrage ausgeschlossen. Neue Treffer landen in der Recherche-Warteschlange.</p></div></div><div className="research-brand-action"><select value={brandId} onChange={e=>setBrandId(e.target.value)}><option value="">Marke auswählen</option>{brands.map(brand=><option key={brand.id} value={brand.id}>{brand.name}</option>)}</select><button type="button" className="approve" disabled={!brandId||researchingBrand} onClick={researchBrand}><Sparkles size={15}/>{researchingBrand?'Gemini sucht …':'Weitere Düfte suchen'}</button></div></section>

    <div className="admin-grid"><form className="editor compact" onSubmit={save}><div className="editor-title"><div>{editing?<><Pencil/> Quelle bearbeiten</>:<><Plus/> Neue Quelle</>}</div>{editing&&<button type="button" onClick={()=>setEditing(null)}><X/> Abbrechen</button>}</div><label className="field"><span>Quellenname *</span><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label><label className="field"><span>Zuordnung</span><select value={form.object_type} onChange={e=>setForm({...form,object_type:e.target.value,object_id:''})}><option value="FRAGRANCE">Duft</option><option value="BRAND">Marke</option><option value="TWIN">Duftzwilling</option><option value="GENERAL">Allgemein</option></select></label>{form.object_type!=='GENERAL'&&<label className="field"><span>Objekt</span><select value={form.object_id||''} onChange={e=>setForm({...form,object_id:e.target.value})}><option value="">Bitte wählen</option>{targets.map(target=><option key={target.id} value={target.id}>{target.label}</option>)}</select></label>}<label className="field"><span>Quellentyp</span><select value={form.source_type} onChange={e=>setForm({...form,source_type:e.target.value})}><option value="OFFICIAL">Offizielle Quelle</option><option value="DATABASE">Datenbank</option><option value="RETAILER">Händler</option><option value="EDITORIAL">Redaktionell</option><option value="COMMUNITY">Community</option><option value="INTERNAL">Intern</option></select></label><label className="field"><span>URL oder Datei</span><input value={form.file_or_url||''} onChange={e=>setForm({...form,file_or_url:e.target.value})} placeholder="https://… oder Dateiname"/></label><label className="field"><span>Stand der Quelle</span><input type="date" value={form.source_date||''} onChange={e=>setForm({...form,source_date:e.target.value})}/></label><label className="field"><span>Vertrauensstatus</span><select value={form.trust_status} onChange={e=>setForm({...form,trust_status:e.target.value})}><option value="OPEN">Offen</option><option value="REVIEW">In Prüfung</option><option value="TRUSTED">Vertrauenswürdig</option><option value="REJECTED">Verworfen</option></select></label><label className="field"><span>Nutzungsstatus</span><select value={form.usage_status} onChange={e=>setForm({...form,usage_status:e.target.value})}><option value="OPEN">Offen</option><option value="ALLOWED">Nutzbar</option><option value="RESTRICTED">Eingeschränkt</option><option value="INTERNAL">Nur intern</option></select></label><label className="field"><span>Prüfnotiz</span><textarea rows="4" value={form.note||''} onChange={e=>setForm({...form,note:e.target.value})}/></label><button className="primary"><Save/> Quelle speichern</button></form><div className="admin-list source-list"><div className="source-list-head"><h3>Quellenregister</h3><select value={filter} onChange={e=>setFilter(e.target.value)}><option value="ALL">Alle</option><option value="OPEN">Offen</option><option value="REVIEW">In Prüfung</option><option value="TRUSTED">Vertrauenswürdig</option><option value="REJECTED">Verworfen</option></select></div>{visible.map(source=><article className="source-row" key={source.id}><div className={`source-trust trust-${String(source.trust_status||'OPEN').toLowerCase()}`}><ShieldCheck/></div><div><small>{source.object_type||'ALLGEMEIN'} · {source.source_type||'Quelle'}</small><b>{source.name}</b><span>{source.note||'Keine Prüfnotiz'}</span>{source.file_or_url?.startsWith('http')&&<a href={source.file_or_url} target="_blank" rel="noreferrer">Quelle öffnen <ExternalLink size={13}/></a>}</div><div><button type="button" onClick={()=>setEditing(source)}><Pencil/></button><button type="button" className="danger" onClick={()=>remove(source)}><Trash2/></button></div></article>)}</div></div>
  </div>;
}
