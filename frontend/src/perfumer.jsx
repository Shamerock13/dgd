import React, {useMemo, useState} from 'react';
import {ArrowLeft, ExternalLink, Pencil, Plus, Save, Search, ShieldCheck, Trash2, UserRound} from 'lucide-react';
import './perfumer.css';

const empty={name:'',birth_year:'',nationality:'',profile:'',style:'',notable_works:'',article_status:'OPEN',primary_source:'',note:''};

export function PerfumerAdmin({api,flash,perfumers,reload}) {
  const [form,setForm]=useState(empty);
  const [editing,setEditing]=useState(null);
  const edit=item=>{setEditing(item);setForm({...empty,...item,birth_year:item.birth_year||''})};
  const reset=()=>{setEditing(null);setForm(empty)};
  const save=async e=>{
    e.preventDefault();
    const payload={...form,birth_year:form.birth_year===''?null:Number(form.birth_year),nationality:form.nationality||null,profile:form.profile||null,style:form.style||null,notable_works:form.notable_works||null,primary_source:form.primary_source||null,note:form.note||null};
    try{await api(editing?`/api/perfumers/${editing.id}`:'/api/perfumers',{method:editing?'PUT':'POST',body:JSON.stringify(payload)});flash(editing?'Parfümeurprofil aktualisiert.':'Parfümeurprofil angelegt.');reset();await reload()}catch(err){flash(err.message)}
  };
  const remove=async item=>{if(!confirm(`Profil von „${item.name}“ wirklich löschen?`))return;try{await api(`/api/perfumers/${item.id}`,{method:'DELETE'});flash('Parfümeurprofil gelöscht.');await reload()}catch(err){flash(err.message)}};
  return <div className="admin-grid perfumer-admin">
    <form className="editor" onSubmit={save}>
      <div className="editor-title"><div>{editing?<><Pencil/> Profil bearbeiten</>:<><Plus/> Neues Parfümeurprofil</>}</div>{editing&&<button type="button" onClick={reset}>Abbrechen</button>}</div>
      <div className="form-grid">
        <label className="field"><span>Name *</span><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label>
        <label className="field"><span>Geburtsjahr</span><input type="number" min="1800" max="2200" value={form.birth_year} onChange={e=>setForm({...form,birth_year:e.target.value})}/></label>
        <label className="field"><span>Nationalität</span><input value={form.nationality} onChange={e=>setForm({...form,nationality:e.target.value})}/></label>
        <label className="field"><span>Artikelstatus</span><select value={form.article_status} onChange={e=>setForm({...form,article_status:e.target.value})}><option value="OPEN">Offen</option><option value="REVIEW">In Prüfung</option><option value="VERIFIED">Verifiziert</option></select></label>
      </div>
      <label className="field"><span>Biografie / Profil</span><textarea rows="6" value={form.profile} onChange={e=>setForm({...form,profile:e.target.value})}/></label>
      <label className="field"><span>Stil und Handschrift</span><textarea rows="4" value={form.style} onChange={e=>setForm({...form,style:e.target.value})}/></label>
      <label className="field"><span>Bekannte Werke</span><textarea rows="4" value={form.notable_works} onChange={e=>setForm({...form,notable_works:e.target.value})}/></label>
      <label className="field"><span>Primärquelle</span><input value={form.primary_source} onChange={e=>setForm({...form,primary_source:e.target.value})} placeholder="https://… oder Quellen-ID"/></label>
      <label className="field"><span>Redaktionelle Notiz</span><textarea rows="3" value={form.note} onChange={e=>setForm({...form,note:e.target.value})}/></label>
      <button className="primary"><Save/> Speichern</button>
    </form>
    <div className="admin-list"><h3>Parfümeure</h3>{perfumers.map(item=><div className="admin-row" key={item.id}><div><small>{item.article_status==='VERIFIED'?'Verifiziert':item.article_status==='REVIEW'?'In Prüfung':'Offen'}</small><b>{item.name}</b><span>{item.nationality||'Nationalität offen'}{item.birth_year?` · ${item.birth_year}`:''}</span></div><div><button onClick={()=>edit(item)}><Pencil/></button><button className="danger" onClick={()=>remove(item)}><Trash2/></button></div></div>)}</div>
  </div>;
}

export function PerfumerProfile({perfumer,items,onBack,onOpen}) {
  const [query,setQuery]=useState('');
  const works=useMemo(()=>items.filter(item=>(item.perfumer||'').trim().toLowerCase()===perfumer.name.trim().toLowerCase()).filter(item=>`${item.name} ${item.brand.name} ${item.accords||''}`.toLowerCase().includes(query.toLowerCase())),[items,perfumer.name,query]);
  const verified=perfumer.article_status==='VERIFIED';
  return <main className="perfumer-profile">
    <div className="perfumer-toolbar"><button onClick={onBack}><ArrowLeft size={18}/> Zurück</button><span>DGD Parfümeurprofil</span></div>
    <section className="perfumer-hero"><div className="perfumer-avatar"><UserRound/></div><div><span className="kicker">Die Nase hinter dem Duft</span><h1>{perfumer.name}</h1><div className="perfumer-meta"><span>{perfumer.nationality||'Nationalität offen'}</span><span>{perfumer.birth_year?`Geboren ${perfumer.birth_year}`:'Geburtsjahr offen'}</span><span className={verified?'verified':''}><ShieldCheck size={15}/>{verified?'Verifiziert':perfumer.article_status==='REVIEW'?'In Prüfung':'Noch offen'}</span></div><p>{perfumer.profile||'Für dieses Profil ist noch keine Biografie hinterlegt.'}</p>{perfumer.primary_source&&perfumer.primary_source.startsWith('http')&&<a href={perfumer.primary_source} target="_blank" rel="noreferrer">Primärquelle öffnen <ExternalLink size={15}/></a>}</div></section>
    <section className="perfumer-facts"><article><small>Stil und Handschrift</small><p>{perfumer.style||'Noch nicht beschrieben.'}</p></article><article><small>Bekannte Werke</small><p>{perfumer.notable_works||'Noch nicht dokumentiert.'}</p></article></section>
    <section className="perfumer-works"><div className="section-head"><div><span className="kicker">Werkverzeichnis</span><h2>{works.length} zugeordnete {works.length===1?'Kreation':'Kreationen'}</h2></div><div className="perfumer-search"><Search size={17}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="In den Werken suchen …"/></div></div>{works.length?<div className="card-grid">{works.map(item=><article className="perfumer-work" key={item.id} onClick={()=>onOpen(item)}><small>{item.brand.name}</small><h3>{item.name}</h3><span>{item.year||'Jahr offen'} · {item.concentration||'Konzentration offen'}</span></article>)}</div>:<div className="empty">Noch keine passenden Düfte zugeordnet.</div>}</section>
  </main>;
}
