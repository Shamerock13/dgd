import React, {useEffect, useMemo, useState} from 'react';
import {AlertTriangle, CheckCircle2, RefreshCw, Search, SlidersHorizontal, Wrench} from 'lucide-react';
import MediaUpload from './media-upload.jsx';
import './quality.css';

const labels={HIGH:'Hoch',MEDIUM:'Mittel',LOW:'Niedrig'};

function MediaManager({api,flash}) {
  const [items,setItems]=useState([]);
  const [selectedId,setSelectedId]=useState('');
  const load=async()=>{try{setItems(await api('/api/fragrances'))}catch(e){flash(e.message)}};
  useEffect(()=>{load()},[]);
  const selected=items.find(item=>item.id===selectedId)||null;
  const changed=patch=>setItems(rows=>rows.map(row=>row.id===selectedId?{...row,...patch}:row));
  return <section className="editor compact">
    <div className="editor-title"><div>Lokaler Bildupload</div></div>
    <label className="field"><span>Duft auswählen</span><select value={selectedId} onChange={e=>setSelectedId(e.target.value)}><option value="">Bitte wählen</option>{items.map(item=><option key={item.id} value={item.id}>{item.brand.name} – {item.name}</option>)}</select></label>
    {selected&&<><div className="image-admin-preview"><div className="managed-image managed-image-admin">{selected.image_url?<img src={selected.image_url} alt={`${selected.brand.name} ${selected.name}`}/>:<div className="managed-image-fallback"><span>{selected.brand.name.slice(0,2).toUpperCase()}</span><small>Bild folgt</small></div>}</div><div><small>Aktuelles Bild</small><b>{selected.image_source_name||'Keine Bildquelle'}</b><span>{selected.image_url||'Noch kein Bild hinterlegt.'}</span></div></div><MediaUpload item={selected} flash={flash} onChanged={changed}/></>}
  </section>;
}

export default function QualityWorklist({api,flash,onOpenSection}) {
  const [data,setData]=useState({summary:{},categories:{},issues:[]});
  const [loading,setLoading]=useState(true);
  const [priority,setPriority]=useState('ALL');
  const [kind,setKind]=useState('ALL');
  const [query,setQuery]=useState('');

  const load=async()=>{
    setLoading(true);
    try{setData(await api('/api/quality/worklist'))}catch(e){flash(e.message)}finally{setLoading(false)}
  };
  useEffect(()=>{load()},[]);

  const kinds=useMemo(()=>[...new Set(data.issues.map(row=>row.kind))].sort(),[data.issues]);
  const rows=useMemo(()=>data.issues.filter(row=>{
    if(priority!=='ALL'&&row.priority!==priority)return false;
    if(kind!=='ALL'&&row.kind!==kind)return false;
    const needle=query.trim().toLowerCase();
    return !needle||`${row.title} ${row.detail} ${row.entity_type}`.toLowerCase().includes(needle);
  }),[data.issues,priority,kind,query]);

  return <section className="quality-worklist">
    <div className="quality-head">
      <div><span className="kicker">Redaktion</span><h2>Datenqualität & Arbeitsliste</h2><p>Alle offenen Baustellen aus Marken, Düften, Quellen, Duftzwillingen und Parfümeuren an einem Ort.</p></div>
      <button className="quality-refresh" onClick={load} disabled={loading}><RefreshCw size={17}/>{loading?'Prüfe …':'Neu prüfen'}</button>
    </div>

    <MediaManager api={api} flash={flash}/>

    <div className="quality-summary">
      <article className="quality-score"><strong>{data.summary.quality_score??0}%</strong><span>Qualitätswert</span></article>
      <article><strong>{data.summary.issues??0}</strong><span>Offene Aufgaben</span></article>
      <article className="quality-high"><strong>{data.summary.high??0}</strong><span>Hohe Priorität</span></article>
      <article><strong>{data.summary.audited_entities??0}</strong><span>Geprüfte Datensätze</span></article>
    </div>

    <div className="quality-toolbar">
      <div className="quality-search"><Search size={17}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Arbeitsliste durchsuchen …"/></div>
      <label><SlidersHorizontal size={15}/><select value={priority} onChange={e=>setPriority(e.target.value)}><option value="ALL">Alle Prioritäten</option><option value="HIGH">Hoch</option><option value="MEDIUM">Mittel</option><option value="LOW">Niedrig</option></select></label>
      <select value={kind} onChange={e=>setKind(e.target.value)}><option value="ALL">Alle Kategorien</option>{kinds.map(value=><option key={value} value={value}>{value.replaceAll('-',' ')}</option>)}</select>
      <span>{rows.length} sichtbar</span>
    </div>

    {loading?<div className="quality-empty">Datenqualität wird geprüft …</div>:rows.length?<div className="quality-list">{rows.map(row=><article className={`quality-row priority-${row.priority.toLowerCase()}`} key={row.id}>
      <div className="quality-icon">{row.priority==='HIGH'?<AlertTriangle/>:<CheckCircle2/>}</div>
      <div className="quality-copy"><div><span>{row.entity_type}</span><b>{labels[row.priority]}</b></div><h3>{row.title}</h3><p>{row.detail}</p></div>
      <button onClick={()=>onOpenSection(row.section)}><Wrench size={16}/> Bearbeiten</button>
    </article>)}</div>:<div className="quality-empty"><CheckCircle2/><h3>Für diesen Filter ist alles erledigt.</h3><p>Ein erstaunlich seltener und schöner Anblick.</p></div>}
  </section>;
}
