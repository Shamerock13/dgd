import React, {useEffect, useMemo, useState} from 'react';
import {Save, ShieldCheck, Sparkles} from 'lucide-react';
import './fragrance-dna-admin.css';

const DIMENSIONS = [
  ['fresh','Frisch'],['citrus','Zitrisch'],['green','Grün'],['aquatic','Aquatisch'],
  ['floral','Floral'],['fruity','Fruchtig'],['sweet','Süß'],['gourmand','Gourmandig'],
  ['spicy','Würzig'],['woody','Holzig'],['smoky','Rauchig'],['earthy','Erdig'],
  ['resinous','Harzig'],['leathery','Ledrig'],['powdery','Pudrig'],['animalic','Animalisch'],
];

const emptyValues = Object.fromEntries(DIMENSIONS.map(([key]) => [key, '']));
const emptyMetadata = {source:'MANUAL', status:'OPEN', source_count:'', confidence:'', disagreement:'', researched_at:''};

export default function FragranceDNAAdmin({fragranceId, api, flash}) {
  const [values,setValues]=useState(emptyValues);
  const [metadata,setMetadata]=useState(emptyMetadata);
  const [personal,setPersonal]=useState(emptyValues);
  const [loading,setLoading]=useState(true);
  const [saving,setSaving]=useState(false);

  useEffect(()=>{
    let active=true;
    setLoading(true);
    api(`/api/fragrances/${fragranceId}/dna`).then(data=>{
      if(!active)return;
      setValues({...emptyValues,...(data.values||{})});
      setPersonal({...emptyValues,...(data.personal_values||{})});
      setMetadata({...emptyMetadata,...(data.metadata||{}), researched_at:data.metadata?.researched_at?.slice?.(0,16)||''});
    }).catch(e=>flash(`Duft-DNA konnte nicht geladen werden: ${e.message}`)).finally(()=>active&&setLoading(false));
    return()=>{active=false};
  },[fragranceId]);

  const activeCount=useMemo(()=>Object.values(values).filter(v=>v!==''&&v!=null).length,[values]);
  const personalCount=useMemo(()=>Object.values(personal).filter(v=>v!==''&&v!=null).length,[personal]);
  const cleanValues=source=>Object.fromEntries(Object.entries(source).filter(([,value])=>value!==''&&value!=null).map(([key,value])=>[key,Number(value)]));

  const saveResearch=async()=>{
    const cleaned=cleanValues(values);
    if(!Object.keys(cleaned).length){flash('Mindestens eine Duft-DNA-Dimension muss gesetzt sein.');return}
    setSaving(true);
    try{
      await api(`/api/fragrances/${fragranceId}/dna`,{method:'PUT',body:JSON.stringify({
        values:cleaned,
        metadata:{
          source:metadata.source,
          status:metadata.status,
          source_count:metadata.source_count===''?null:Number(metadata.source_count),
          confidence:metadata.confidence===''?null:Number(metadata.confidence),
          disagreement:metadata.disagreement===''?null:Number(metadata.disagreement),
          researched_at:metadata.researched_at||null,
        }
      })});
      flash('Aggregierte Duft-DNA gespeichert.');
    }catch(e){flash(e.message)}finally{setSaving(false)}
  };

  const savePersonal=async()=>{
    const cleaned=cleanValues(personal);
    if(!Object.keys(cleaned).length){flash('Mindestens eine persönliche DNA-Dimension muss gesetzt sein.');return}
    setSaving(true);
    try{
      await api(`/api/fragrances/${fragranceId}/dna/personal`,{method:'PUT',body:JSON.stringify(cleaned)});
      flash('Persönliche Duft-DNA gespeichert.');
    }catch(e){flash(e.message)}finally{setSaving(false)}
  };

  if(loading)return <section className="dna-admin-card"><p>Duft-DNA wird geladen …</p></section>;

  const sliders=(state,setState,prefix)=>DIMENSIONS.map(([key,label])=><label className="dna-admin-slider" key={`${prefix}-${key}`}>
    <span><b>{label}</b><output>{state[key]===''?'offen':Number(state[key]).toFixed(1)}</output></span>
    <input type="range" min="0" max="10" step="0.1" value={state[key]===''?0:state[key]} onChange={e=>setState(current=>({...current,[key]:e.target.value}))}/>
    <button type="button" onClick={()=>setState(current=>({...current,[key]:''}))}>Wert leeren</button>
  </label>);

  return <section className="dna-admin-card">
    <div className="dna-admin-head"><div><span>Duft-DNA</span><h3>Charakterprofil pflegen</h3><p>Nur belegte Werte setzen. Leer bleibt wirklich unbekannt.</p></div><Sparkles/></div>

    <div className="dna-admin-meta">
      <label>Herkunft<select value={metadata.source} onChange={e=>setMetadata({...metadata,source:e.target.value})}><option value="MANUAL">Manuell</option><option value="RESEARCH">Recherche</option><option value="RULE_BASED">Regelbasiert</option></select></label>
      <label>Prüfstatus<select value={metadata.status} onChange={e=>setMetadata({...metadata,status:e.target.value})}><option value="OPEN">Offen</option><option value="REVIEW_REQUIRED">Prüfung nötig</option><option value="VERIFIED">Geprüft</option></select></label>
      <label>Quellenanzahl<input type="number" min="0" value={metadata.source_count??''} onChange={e=>setMetadata({...metadata,source_count:e.target.value})}/></label>
      <label>Vertrauen 0–1<input type="number" min="0" max="1" step="0.01" value={metadata.confidence??''} onChange={e=>setMetadata({...metadata,confidence:e.target.value})}/></label>
      <label>Abweichung 0–1<input type="number" min="0" max="1" step="0.01" value={metadata.disagreement??''} onChange={e=>setMetadata({...metadata,disagreement:e.target.value})}/></label>
      <label>Recherchedatum<input type="datetime-local" value={metadata.researched_at||''} onChange={e=>setMetadata({...metadata,researched_at:e.target.value})}/></label>
    </div>

    <div className="dna-admin-section-head"><div><ShieldCheck/><span>Aggregierte Werte</span></div><b>{activeCount} von 16 gesetzt</b></div>
    <div className="dna-admin-grid">{sliders(values,setValues,'research')}</div>
    <button type="button" className="primary dna-admin-save" disabled={saving} onClick={saveResearch}><Save/> Aggregierte DNA speichern</button>

    <div className="dna-admin-personal">
      <div className="dna-admin-section-head"><div><span>Meine persönliche DNA</span></div><b>{personalCount} von 16 gesetzt</b></div>
      <p>Diese Werte bleiben fachlich getrennt von Recherche- und Community-Daten.</p>
      <div className="dna-admin-grid">{sliders(personal,setPersonal,'personal')}</div>
      <button type="button" className="primary dna-admin-save" disabled={saving} onClick={savePersonal}><Save/> Persönliche DNA speichern</button>
    </div>
  </section>;
}
