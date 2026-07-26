import React, {useEffect, useMemo, useState} from 'react';
import {ExternalLink, Pencil, Plus, Save, ShieldCheck, Trash2, X} from 'lucide-react';
import './verification.css';

const emptySource={name:'',object_type:'FRAGRANCE',object_id:'',source_type:'OFFICIAL',file_or_url:'',source_date:'',usage_status:'OPEN',trust_status:'OPEN',note:''};

export default function VerificationAdmin({api,flash,brands,items,twins}){
  const [sources,setSources]=useState([]);
  const [summary,setSummary]=useState(null);
  const [form,setForm]=useState(emptySource);
  const [editing,setEditing]=useState(null);
  const [filter,setFilter]=useState('ALL');
  const load=async()=>{
    try{const [rows,stats]=await Promise.all([api('/api/sources'),api('/api/verification/summary')]);setSources(rows);setSummary(stats)}catch(e){flash(e.message)}
  };
  useEffect(()=>{load()},[]);
  useEffect(()=>setForm(editing?{...emptySource,...editing,source_date:editing.source_date?.slice(0,10)||''}:emptySource),[editing]);
  const targets=useMemo(()=>form.object_type==='BRAND'?brands.map(x=>({id:x.id,label:x.name})):form.object_type==='TWIN'?twins.map(x=>({id:x.id,label:`${x.original.name} → ${x.alternative.name}`})):items.map(x=>({id:x.id,label:`${x.brand.name} – ${x.name}`})),[form.object_type,brands,items,twins]);
  const visible=filter==='ALL'?sources:sources.filter(source=>source.trust_status===filter);
  const save=async e=>{e.preventDefault();const payload={...form,object_id:form.object_id||null,source_type:form.source_type||null,file_or_url:form.file_or_url||null,source_date:form.source_date?`${form.source_date}T00:00:00`:null,note:form.note||null};try{await api(editing?`/api/sources/${editing.id}`:'/api/sources',{method:editing?'PUT':'POST',body:JSON.stringify(payload)});flash(editing?'Quelle aktualisiert.':'Quelle angelegt.');setEditing(null);setForm(emptySource);await load()}catch(e){flash(e.message)}};
  const remove=async source=>{if(!confirm(`Quelle „${source.name}“ wirklich löschen?`))return;try{await api(`/api/sources/${source.id}`,{method:'DELETE'});flash('Quelle gelöscht.');await load()}catch(e){flash(e.message)}};
  return <div className="verification-admin">
    <section className="verification-summary">
      <article><strong>{summary?.sources??'–'}</strong><span>Quellen</span></article><article className="trusted"><strong>{summary?.trusted??'–'}</strong><span>Vertrauenswürdig</span></article><article><strong>{summary?.review??'–'}</strong><span>In Prüfung</span></article><article><strong>{summary?.fragrances_without_source??'–'}</strong><span>Düfte ohne Quelle</span></article>
    </section>
    <div className="admin-grid">
      <form className="editor compact" onSubmit={save}>
        <div className="editor-title"><div>{editing?<><Pencil/> Quelle bearbeiten</>:<><Plus/> Neue Quelle</>}</div>{editing&&<button type="button" onClick={()=>setEditing(null)}><X/> Abbrechen</button>}</div>
        <label className="field"><span>Quellenname *</span><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label>
        <label className="field"><span>Zuordnung</span><select value={form.object_type} onChange={e=>setForm({...form,object_type:e.target.value,object_id:''})}><option value="FRAGRANCE">Duft</option><option value="BRAND">Marke</option><option value="TWIN">Duftzwilling</option><option value="GENERAL">Allgemein</option></select></label>
        {form.object_type!=='GENERAL'&&<label className="field"><span>Objekt</span><select value={form.object_id||''} onChange={e=>setForm({...form,object_id:e.target.value})}><option value="">Bitte wählen</option>{targets.map(target=><option key={target.id} value={target.id}>{target.label}</option>)}</select></label>}
        <label className="field"><span>Quellentyp</span><select value={form.source_type} onChange={e=>setForm({...form,source_type:e.target.value})}><option value="OFFICIAL">Offizielle Quelle</option><option value="DATABASE">Datenbank</option><option value="RETAILER">Händler</option><option value="EDITORIAL">Redaktionell</option><option value="COMMUNITY">Community</option><option value="INTERNAL">Intern</option></select></label>
        <label className="field"><span>URL oder Datei</span><input value={form.file_or_url||''} onChange={e=>setForm({...form,file_or_url:e.target.value})} placeholder="https://… oder Dateiname"/></label>
        <label className="field"><span>Stand der Quelle</span><input type="date" value={form.source_date||''} onChange={e=>setForm({...form,source_date:e.target.value})}/></label>
        <label className="field"><span>Vertrauensstatus</span><select value={form.trust_status} onChange={e=>setForm({...form,trust_status:e.target.value})}><option value="OPEN">Offen</option><option value="REVIEW">In Prüfung</option><option value="TRUSTED">Vertrauenswürdig</option><option value="REJECTED">Verworfen</option></select></label>
        <label className="field"><span>Nutzungsstatus</span><select value={form.usage_status} onChange={e=>setForm({...form,usage_status:e.target.value})}><option value="OPEN">Offen</option><option value="ALLOWED">Nutzbar</option><option value="RESTRICTED">Eingeschränkt</option><option value="INTERNAL">Nur intern</option></select></label>
        <label className="field"><span>Prüfnotiz</span><textarea rows="4" value={form.note||''} onChange={e=>setForm({...form,note:e.target.value})}/></label>
        <button className="primary"><Save/> Quelle speichern</button>
      </form>
      <div className="admin-list source-list"><div className="source-list-head"><h3>Quellenregister</h3><select value={filter} onChange={e=>setFilter(e.target.value)}><option value="ALL">Alle</option><option value="OPEN">Offen</option><option value="REVIEW">In Prüfung</option><option value="TRUSTED">Vertrauenswürdig</option><option value="REJECTED">Verworfen</option></select></div>{visible.map(source=><article className="source-row" key={source.id}><div className={`source-trust trust-${source.trust_status.toLowerCase()}`}><ShieldCheck/></div><div><small>{source.object_type||'ALLGEMEIN'} · {source.source_type||'Quelle'}</small><b>{source.name}</b><span>{source.note||'Keine Prüfnotiz'}</span>{source.file_or_url?.startsWith('http')&&<a href={source.file_or_url} target="_blank" rel="noreferrer">Quelle öffnen <ExternalLink size={13}/></a>}</div><div><button onClick={()=>setEditing(source)}><Pencil/></button><button className="danger" onClick={()=>remove(source)}><Trash2/></button></div></article>)}</div>
    </div>
  </div>;
}
