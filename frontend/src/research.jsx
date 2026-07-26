import React,{useEffect,useMemo,useState} from 'react';
import {Check,ExternalLink,RefreshCw,Search,ShieldAlert,Trash2} from 'lucide-react';
import './research.css';

const empty={brand_name:'',fragrance_name:'',year:'',concentration:'',description:'',image_url:''};

export default function ResearchQueue({api,flash,reload}){
  const [rows,setRows]=useState([]);
  const [status,setStatus]=useState('PENDING');
  const [url,setUrl]=useState('');
  const [sourceName,setSourceName]=useState('');
  const [query,setQuery]=useState('');
  const [working,setWorking]=useState(false);
  const [editing,setEditing]=useState(null);
  const [form,setForm]=useState(empty);

  const load=async()=>{setWorking(true);try{setRows(await api(`/api/research/candidates?status=${status}`))}catch(e){flash(e.message)}finally{setWorking(false)}};
  useEffect(()=>{load()},[status]);

  const scan=async e=>{e.preventDefault();if(!url)return;setWorking(true);try{const result=await api('/api/research/scan',{method:'POST',body:JSON.stringify({url,source_name:sourceName||null})});flash(`${result.created} neue Vorschläge, ${result.possible_duplicates} mögliche Dubletten.`);setUrl('');await load()}catch(e){flash(e.message)}finally{setWorking(false)}};
  const startEdit=row=>{setEditing(row.id);setForm({brand_name:row.brand_name||'',fragrance_name:row.fragrance_name||'',year:row.year||'',concentration:row.concentration||'',description:row.description||'',image_url:row.image_url||''})};
  const save=async()=>{try{await api(`/api/research/candidates/${editing}`,{method:'PUT',body:JSON.stringify({...form,year:form.year===''?null:Number(form.year)})});flash('Vorschlag aktualisiert.');setEditing(null);await load()}catch(e){flash(e.message)}};
  const action=async(id,type)=>{try{await api(`/api/research/candidates/${id}/${type}`,{method:'POST'});flash(type==='approve'?'Vorschlag übernommen.':'Vorschlag abgelehnt.');await load();if(type==='approve')await reload()}catch(e){flash(e.message);await load()}};
  const visible=useMemo(()=>rows.filter(r=>`${r.brand_name} ${r.fragrance_name} ${r.source_name}`.toLowerCase().includes(query.toLowerCase())),[rows,query]);

  return <section className="research-queue">
    <div className="research-head"><div><span className="kicker">Recherche 1.0</span><h2>Import-Warteschlange</h2><p>Quellen scannen, Treffer prüfen und erst nach Freigabe in DGD übernehmen.</p></div><button onClick={load} disabled={working}><RefreshCw size={16}/> Aktualisieren</button></div>
    <form className="research-scan" onSubmit={scan}><div><label>Quellenadresse<input type="url" required value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://…"/></label><label>Quellenname<input value={sourceName} onChange={e=>setSourceName(e.target.value)} placeholder="Hersteller, Händler, Datenbank …"/></label></div><button disabled={working}><Search size={17}/>{working?'Scanne …':'Recherche starten'}</button><p><ShieldAlert size={15}/> Interne Netzwerkziele sind gesperrt. Die Seite wird nur gelesen; ein Treffer wird niemals automatisch veröffentlicht.</p></form>
    <div className="research-toolbar"><div><Search size={16}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Warteschlange durchsuchen …"/></div><select value={status} onChange={e=>setStatus(e.target.value)}><option value="PENDING">Offen</option><option value="APPROVED">Übernommen</option><option value="DUPLICATE">Dubletten</option><option value="REJECTED">Abgelehnt</option><option value="ALL">Alle</option></select><span>{visible.length} Treffer</span></div>
    <div className="research-list">{visible.map(row=><article key={row.id} className={row.duplicate_fragrance_id?'duplicate':''}>
      {editing===row.id?<div className="research-editor"><input value={form.brand_name} onChange={e=>setForm({...form,brand_name:e.target.value})} placeholder="Marke"/><input value={form.fragrance_name} onChange={e=>setForm({...form,fragrance_name:e.target.value})} placeholder="Duft"/><input type="number" value={form.year} onChange={e=>setForm({...form,year:e.target.value})} placeholder="Jahr"/><input value={form.concentration} onChange={e=>setForm({...form,concentration:e.target.value})} placeholder="Konzentration"/><textarea value={form.description} onChange={e=>setForm({...form,description:e.target.value})} placeholder="Beschreibung"/><input value={form.image_url} onChange={e=>setForm({...form,image_url:e.target.value})} placeholder="Bild-URL"/><div><button onClick={save} type="button">Speichern</button><button onClick={()=>setEditing(null)} type="button">Abbrechen</button></div></div>:<>
      <div className="research-score"><strong>{Math.round(row.confidence||0)}%</strong><span>Treffer</span></div><div className="research-copy"><small>{row.source_name} · {row.status}</small><h3>{row.brand_name} – {row.fragrance_name}</h3><p>{row.description||'Noch keine Beschreibung aus der Quelle übernommen.'}</p>{row.duplicate_fragrance_id&&<b className="duplicate-note">Mögliche Dublette erkannt</b>}<a href={row.source_url} target="_blank" rel="noreferrer">Quelle öffnen <ExternalLink size={13}/></a></div><div className="research-actions">{row.status==='PENDING'&&<><button onClick={()=>startEdit(row)}>Prüfen</button><button className="approve" onClick={()=>action(row.id,'approve')}><Check size={16}/> Übernehmen</button><button className="reject" onClick={()=>action(row.id,'reject')}><Trash2 size={16}/> Ablehnen</button></>}</div></>}
    </article>)}</div>
    {!working&&!visible.length&&<div className="research-empty">Keine Vorschläge für diesen Filter.</div>}
  </section>;
}
