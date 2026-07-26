import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {
  Search, Sparkles, LibraryBig, Tags, GitCompareArrows, Star,
  Moon, Sun, SlidersHorizontal, X, ChevronRight, FlaskConical,
  Settings, Plus, Pencil, Trash2, Save, ArrowLeft, RefreshCw, PackageOpen, ShieldCheck, CircleAlert
} from 'lucide-react';
import './styles.css';

const euro = new Intl.NumberFormat('de-DE', {style:'currency', currency:'EUR'});
const emptyFragrance = {
  name:'', brand_id:'', year:'', gender:'Unisex', concentration:'', perfumer:'',
  price_eur:'', image_url:'', description:'', top_notes:'', heart_notes:'',
  base_notes:'', accords:'', longevity:'', projection:'', sweetness:'', freshness:''
};
const emptyBrand = {name:'', country:'', description:''};
const emptyTwin = {original_id:'', alternative_id:'', similarity:80, commonalities:'', differences:'', source_note:''};

async function api(url, options={}) {
  const res = await fetch(url, {
    headers: {'Content-Type':'application/json', ...(options.headers||{})},
    ...options
  });
  if(!res.ok) {
    let message = `Fehler ${res.status}`;
    try { const body = await res.json(); message = body.detail || message; } catch {}
    throw new Error(message);
  }
  return res.status === 204 ? null : res.json();
}

async function uploadApi(url, formData) {
  const res = await fetch(url, {method:'POST', body:formData});
  if(!res.ok) {
    let message=`Fehler ${res.status}`;
    try {const body=await res.json();message=body.detail||message}catch{}
    throw new Error(message);
  }
  return res.json();
}

function Meter({label, value}) {
  if (value == null) return null;
  return <div className="meter"><div className="meter-head"><span>{label}</span><strong>{Number(value).toFixed(1)}</strong></div>
    <div className="meter-track"><div className="meter-fill" style={{width:`${value*10}%`}} /></div></div>
}

function App() {
  const [dark,setDark]=useState(true);
  const [tab,setTab]=useState('entdecken');
  const [stats,setStats]=useState({});
  const [items,setItems]=useState([]);
  const [brands,setBrands]=useState([]);
  const [twins,setTwins]=useState([]);
  const [notes,setNotes]=useState([]);
  const [query,setQuery]=useState('');
  const [maxPrice,setMaxPrice]=useState('');
  const [minLongevity,setMinLongevity]=useState('');
  const [selected,setSelected]=useState(null);
  const [filters,setFilters]=useState(false);
  const [loading,setLoading]=useState(true);
  const [notice,setNotice]=useState('');

  useEffect(()=>document.documentElement.dataset.theme=dark?'dark':'light',[dark]);

  const load = async () => {
    setLoading(true);
    const params=new URLSearchParams();
    if(query) params.set('q',query);
    if(maxPrice) params.set('max_price',maxPrice);
    if(minLongevity) params.set('min_longevity',minLongevity);
    try {
      const [s,f,b,t,n]=await Promise.all([
        api('/api/dashboard'), api('/api/fragrances?'+params), api('/api/brands'), api('/api/twins'), api('/api/notes')
      ]);
      setStats(s);setItems(f);setBrands(b);setTwins(t);setNotes(n);
    } catch(e){setNotice(e.message)}
    setLoading(false);
  };
  useEffect(()=>{const x=setTimeout(load,150);return()=>clearTimeout(x)},[query,maxPrice,minLongevity]);

  const flash=(msg)=>{setNotice(msg);setTimeout(()=>setNotice(''),3500)};

  return <div className="shell">
    <header className="topbar">
      <button className="brand" onClick={()=>setTab('entdecken')}><span className="brand-mark"><FlaskConical size={23}/></span><span><b>DGD</b><small>Das große Duftlexikon</small></span></button>
      <nav>
        <button className={tab==='entdecken'?'active':''} onClick={()=>setTab('entdecken')}>Entdecken</button>
        <button className={tab==='duefte'?'active':''} onClick={()=>setTab('duefte')}>Düfte</button>
        <button className={tab==='zwillinge'?'active':''} onClick={()=>setTab('zwillinge')}>Duftzwillinge</button>
        <button className={tab==='admin'?'active':''} onClick={()=>setTab('admin')}><Settings size={15}/> Admin</button>
      </nav>
      <button className="icon-btn" onClick={()=>setDark(v=>!v)}>{dark?<Sun size={19}/>:<Moon size={19}/>}</button>
    </header>

    {notice && <div className="toast">{notice}</div>}

    {tab==='admin' ? <AdminCenter brands={brands} items={items} twins={twins} notes={notes} reload={load} flash={flash}/> :
    <main>
      <section className="hero">
        <div className="eyebrow"><Sparkles size={16}/> Wissen, vergleichen, entdecken</div>
        <h1>Finde den Duft, der<br/><em>wirklich</em> zu dir passt.</h1>
        <p>Durchsuche Duftnoten, Akkorde, Marken und Duftzwillinge – ohne Marketingnebel.</p>
        <div className="searchbox"><Search size={21}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="z. B. erdiges Patchouli, Leder oder Lattafa …"/>
          {query&&<button onClick={()=>setQuery('')}><X size={18}/></button>}
          <button className="filter-button" onClick={()=>setFilters(v=>!v)}><SlidersHorizontal size={18}/> Filter</button>
        </div>
        {filters&&<div className="filters">
          <label>Maximalpreis<div><input type="number" value={maxPrice} onChange={e=>setMaxPrice(e.target.value)} placeholder="z. B. 50"/><span>€</span></div></label>
          <label>Mindesthaltbarkeit<div><input type="number" min="0" max="10" step=".5" value={minLongevity} onChange={e=>setMinLongevity(e.target.value)} placeholder="0–10"/><span>/ 10</span></div></label>
          <button className="clear" onClick={()=>{setMaxPrice('');setMinLongevity('')}}>Zurücksetzen</button>
        </div>}
      </section>
      <section className="stats-grid">
        <Stat icon={<LibraryBig/>} value={stats.fragrances} label="Düfte"/><Stat icon={<Tags/>} value={stats.brands} label="Marken"/>
        <Stat icon={<GitCompareArrows/>} value={stats.twins} label="Duftzwillinge"/><Stat icon={<Star/>} value={`${stats.average_similarity||0}%`} label="Ø Ähnlichkeit"/>
      </section>
      {(tab==='entdecken'||tab==='duefte')&&<section className="content-section"><div className="section-head"><div><span className="kicker">Duftdatenbank</span><h2>{query?`Ergebnisse für „${query}“`:'Düfte entdecken'}</h2></div><span className="result-count">{items.length} Treffer</span></div>
        {loading?<div className="empty">Düfte werden geladen …</div>:items.length?<div className="card-grid">{items.map(i=><FragranceCard key={i.id} item={i} onOpen={setSelected}/>)}</div>:<div className="empty">Kein Duft passt zu diesen Filtern.</div>}
      </section>}
      {(tab==='entdecken'||tab==='zwillinge')&&<section className="content-section twin-section"><div className="section-head"><div><span className="kicker">Das Herzstück</span><h2>Starke Duftzwillinge</h2></div></div><div className="twin-grid">{twins.map(t=><TwinCard key={t.id} twin={t} onOpen={setSelected}/>)}</div></section>}
    </main>}
    <footer><b>DGD</b><span>Das große Parfum- & Duftzwillinge-Lexikon · Version 1.0.0</span></footer>
    {selected&&<Detail item={selected} onClose={()=>setSelected(null)}/>}
  </div>
}

function AdminCenter({brands,items,twins,notes,reload,flash}) {
  const [section,setSection]=useState('fragrances');
  const [editing,setEditing]=useState(null);
  return <main className="admin-main">
    <section className="admin-head"><div><span className="kicker">DGD Verwaltung</span><h1>Admin Center</h1><p>Düfte, Marken und Duftzwillinge direkt in PostgreSQL verwalten.</p></div></section>
    <div className="admin-tabs">
      <button className={section==='fragrances'?'active':''} onClick={()=>{setSection('fragrances');setEditing(null)}}>Düfte <b>{items.length}</b></button>
      <button className={section==='brands'?'active':''} onClick={()=>{setSection('brands');setEditing(null)}}>Marken <b>{brands.length}</b></button>
      <button className={section==='notes'?'active':''} onClick={()=>{setSection('notes');setEditing(null)}}>Duftnoten <b>{notes.length}</b></button>
      <button className={section==='import'?'active':''} onClick={()=>{setSection('import');setEditing(null)}}>Import</button>
      <button className={section==='twins'?'active':''} onClick={()=>{setSection('twins');setEditing(null)}}>Duftzwillinge <b>{twins.length}</b></button>
      <button className={section==='updates'?'active':''} onClick={()=>{setSection('updates');setEditing(null)}}>System & Updates</button>
    </div>
    {section==='fragrances'&&<FragranceAdmin brands={brands} items={items} notes={notes} reload={reload} flash={flash} editing={editing} setEditing={setEditing}/>}
    {section==='brands'&&<BrandAdmin brands={brands} reload={reload} flash={flash} editing={editing} setEditing={setEditing}/>}
    {section==='notes'&&<NoteAdmin notes={notes} reload={reload} flash={flash} editing={editing} setEditing={setEditing}/>}
    {section==='import'&&<ImportAdmin reload={reload} flash={flash}/>}
    {section==='twins'&&<TwinAdmin items={items} twins={twins} reload={reload} flash={flash}/>}
    {section==='updates'&&<UpdateCenter flash={flash}/>}
  </main>
}

function FragranceAdmin({brands,items,notes,reload,flash,editing,setEditing}) {
  const [form,setForm]=useState(emptyFragrance);
  const [noteAssignments,setNoteAssignments]=useState({top:[],heart:[],base:[]});
  useEffect(()=>{
    if(editing) {
      setForm({...emptyFragrance,...editing,brand_id:editing.brand.id});
      api(`/api/fragrances/${editing.id}/notes`).then(rows=>{
        const grouped={top:[],heart:[],base:[]};
        rows.forEach(r=>grouped[r.pyramid].push(r.note.id));
        setNoteAssignments(grouped);
      }).catch(()=>setNoteAssignments({top:[],heart:[],base:[]}));
    } else {
      setForm(emptyFragrance);
      setNoteAssignments({top:[],heart:[],base:[]});
    }
  },[editing]);
  const set=(k,v)=>setForm(f=>({...f,[k]:v}));
  const payload=()=>Object.fromEntries(Object.entries(form).map(([k,v])=>{
    if(k==='brand_id') return [k,v===''?null:v];
    if(k==='year') return [k,v===''?null:Number(v)];
    if(['price_eur','longevity','projection','sweetness','freshness'].includes(k)) return [k,v===''?null:Number(v)];
    return [k,v===''?null:v];
  }));
  const save=async e=>{
    e.preventDefault();
    try{
      const saved=await api(editing?`/api/fragrances/${editing.id}`:'/api/fragrances',{method:editing?'PUT':'POST',body:JSON.stringify(payload())});
      const assignments=[];
      ['top','heart','base'].forEach(pyramid=>noteAssignments[pyramid].forEach((note_id,position)=>assignments.push({note_id,pyramid,position})));
      await api(`/api/fragrances/${saved.id}/notes`,{method:'PUT',body:JSON.stringify(assignments)});
      flash(editing?'Duft aktualisiert.':'Duft angelegt.');setEditing(null);setForm(emptyFragrance);setNoteAssignments({top:[],heart:[],base:[]});await reload();
    }catch(e){flash(e.message)}
  };
  const remove=async item=>{
    if(!confirm(`„${item.name}“ wirklich löschen? Zugehörige Duftzwillinge werden ebenfalls entfernt.`)) return;
    try{await api(`/api/fragrances/${item.id}`,{method:'DELETE'});flash('Duft gelöscht.');await reload()}catch(e){flash(e.message)}
  };
  return <div className="admin-grid">
    <form className="editor" onSubmit={save}>
      <div className="editor-title"><div>{editing?<><Pencil/> Duft bearbeiten</>:<><Plus/> Neuer Duft</>}</div>{editing&&<button type="button" onClick={()=>setEditing(null)}><ArrowLeft/> Abbrechen</button>}</div>
      <div className="form-grid">
        <Field label="Name *"><input required value={form.name||''} onChange={e=>set('name',e.target.value)}/></Field>
        <Field label="Marke *"><select required value={form.brand_id||''} onChange={e=>set('brand_id',e.target.value)}><option value="">Bitte wählen</option>{brands.map(b=><option key={b.id} value={b.id}>{b.name}</option>)}</select></Field>
        <Field label="Jahr"><input type="number" value={form.year||''} onChange={e=>set('year',e.target.value)}/></Field>
        <Field label="Geschlecht"><select value={form.gender||'Unisex'} onChange={e=>set('gender',e.target.value)}><option>Unisex</option><option>Herren</option><option>Damen</option></select></Field>
        <Field label="Konzentration"><input value={form.concentration||''} onChange={e=>set('concentration',e.target.value)}/></Field>
        <Field label="Parfümeur"><input value={form.perfumer||''} onChange={e=>set('perfumer',e.target.value)}/></Field>
        <Field label="Preis in €"><input type="number" step=".01" value={form.price_eur??''} onChange={e=>set('price_eur',e.target.value)}/></Field>
        <Field label="Bild-URL"><input value={form.image_url||''} onChange={e=>set('image_url',e.target.value)}/></Field>
      </div>
      <Field label="Beschreibung"><textarea rows="3" value={form.description||''} onChange={e=>set('description',e.target.value)}/></Field>
      <div className="note-pyramid">
        <NotePicker title="Kopfnoten" notes={notes} selected={noteAssignments.top} onChange={value=>setNoteAssignments(v=>({...v,top:value}))}/>
        <NotePicker title="Herznoten" notes={notes} selected={noteAssignments.heart} onChange={value=>setNoteAssignments(v=>({...v,heart:value}))}/>
        <NotePicker title="Basisnoten" notes={notes} selected={noteAssignments.base} onChange={value=>setNoteAssignments(v=>({...v,base:value}))}/>
      </div>
      <Field label="Akkorde, kommagetrennt"><input value={form.accords||''} onChange={e=>set('accords',e.target.value)}/></Field>
      <div className="slider-grid">{['longevity:Haltbarkeit','projection:Projektion','sweetness:Süße','freshness:Frische'].map(x=>{const[k,l]=x.split(':');return <Field key={k} label={`${l}: ${form[k]||0}`}><input type="range" min="0" max="10" step=".1" value={form[k]||0} onChange={e=>set(k,e.target.value)}/></Field>})}</div>
      <button className="primary" type="submit"><Save/> {editing?'Änderungen speichern':'Duft anlegen'}</button>
    </form>
    <div className="admin-list"><h3>Vorhandene Düfte</h3>{items.map(i=><div className="admin-row" key={i.id}><div><small>{i.brand.name}</small><b>{i.name}</b><span>{i.price_eur!=null?euro.format(i.price_eur):'Kein Preis'}</span></div><div><button onClick={()=>setEditing(i)}><Pencil/></button><button className="danger" onClick={()=>remove(i)}><Trash2/></button></div></div>)}</div>
  </div>
}



function ImportAdmin({reload,flash}) {
  const [file,setFile]=useState(null);
  const [importType,setImportType]=useState('fragrances');
  const [duplicateMode,setDuplicateMode]=useState('skip');
  const [preview,setPreview]=useState(null);
  const [working,setWorking]=useState(false);
  const [result,setResult]=useState(null);

  const previewFile=async()=>{
    if(!file){flash('Bitte zuerst eine CSV- oder XLSX-Datei auswählen.');return}
    setWorking(true);setResult(null);
    try{
      const data=new FormData();
      data.append('file',file);
      data.append('import_type',importType);
      setPreview(await uploadApi('/api/import/preview',data));
    }catch(e){flash(e.message);setPreview(null)}
    finally{setWorking(false)}
  };

  const commit=async()=>{
    if(!file||!preview)return;
    if(!confirm(`${preview.valid_rows} gültige Zeilen jetzt in DGD importieren?`))return;
    setWorking(true);
    try{
      const data=new FormData();
      data.append('file',file);
      data.append('import_type',importType);
      data.append('duplicate_mode',duplicateMode);
      const response=await uploadApi('/api/import/commit',data);
      setResult(response);
      flash(`Import abgeschlossen: ${response.created} neu, ${response.updated} aktualisiert.`);
      await reload();
    }catch(e){flash(e.message)}
    finally{setWorking(false)}
  };

  const reset=()=>{setFile(null);setPreview(null);setResult(null)};

  return <div className="import-center">
    <section className="import-panel">
      <div className="editor-title"><div><LibraryBig/> Datenimport</div></div>
      <p className="import-intro">Lade viele Düfte oder Duftzwillinge auf einmal hoch. DGD prüft alles zuerst und schreibt erst nach deiner Bestätigung in PostgreSQL.</p>
      <div className="import-steps">
        <div><b>1</b><span>Dateityp wählen</span></div><div><b>2</b><span>Vorschau prüfen</span></div><div><b>3</b><span>Import bestätigen</span></div>
      </div>
      <div className="form-grid">
        <Field label="Importart"><select value={importType} onChange={e=>{setImportType(e.target.value);setPreview(null);setResult(null)}}><option value="fragrances">Düfte</option><option value="twins">Duftzwillinge</option></select></Field>
        <Field label="Dubletten behandeln"><select value={duplicateMode} onChange={e=>setDuplicateMode(e.target.value)}><option value="skip">Vorhandene überspringen</option><option value="update">Vorhandene aktualisieren</option></select></Field>
      </div>
      <label className="dropzone">
        <input type="file" accept=".csv,.xlsx" onChange={e=>{setFile(e.target.files?.[0]||null);setPreview(null);setResult(null)}}/>
        <FlaskConical/>
        <b>{file?file.name:'CSV- oder Excel-Datei auswählen'}</b>
        <span>{file?`${(file.size/1024).toFixed(1)} KB`:'Klicken oder Datei hier ablegen · maximal 20 MB'}</span>
      </label>
      <div className="import-actions">
        <a className="template-link" href="/DGD_Importvorlage_0.7.xlsx" download>Excel-Vorlage herunterladen</a>
        {file&&<button className="clear" onClick={reset}>Auswahl löschen</button>}
        <button className="primary" onClick={previewFile} disabled={working||!file}>{working?'Prüfung läuft …':'Import prüfen'}</button>
      </div>
    </section>

    {preview&&<section className="import-preview">
      <div className="section-head"><div><span className="kicker">Importvorschau</span><h2>{preview.total_rows} Zeilen erkannt</h2></div></div>
      <div className="import-kpis">
        <Stat value={preview.valid_rows} label="gültige Zeilen"/>
        <Stat value={preview.duplicate_count} label="Dubletten"/>
        <Stat value={preview.error_count} label="Fehler"/>
        {importType==='fragrances'&&<><Stat value={preview.new_brand_count} label="neue Marken"/><Stat value={preview.new_note_count} label="neue Duftnoten"/></>}
      </div>
      {preview.new_brands?.length>0&&<div className="import-info"><b>Neue Marken:</b> {preview.new_brands.slice(0,20).join(', ')}{preview.new_brands.length>20?' …':''}</div>}
      {preview.new_notes?.length>0&&<div className="import-info"><b>Neue Duftnoten:</b> {preview.new_notes.slice(0,30).join(', ')}{preview.new_notes.length>30?' …':''}</div>}
      <div className="preview-table-wrap"><table className="preview-table"><thead><tr>
        <th>Zeile</th>{importType==='fragrances'?<><th>Marke</th><th>Duft</th><th>Jahr</th><th>Preis</th></>:<><th>Original</th><th>Alternative</th><th>Ähnlichkeit</th></>}<th>Status</th><th>Hinweise</th>
      </tr></thead><tbody>{preview.rows.map(row=><tr key={row.row} className={row.errors.length?'has-error':''}>
        <td>{row.row}</td>{importType==='fragrances'?<><td>{row.brand}</td><td>{row.name}</td><td>{row.year||'–'}</td><td>{row.price_eur!=null?euro.format(row.price_eur):'–'}</td></>:<><td>{row.original}</td><td>{row.alternative}</td><td>{row.similarity!=null?`${row.similarity}%`:'–'}</td></>}<td><span className={`status status-${row.status.toLowerCase().replace('ü','u')}`}>{row.status}</span></td><td>{row.errors.join(' · ')||'Bereit'}</td>
      </tr>)}</tbody></table></div>
      {preview.rows_truncated&&<p className="table-note">Es werden nur die ersten 250 Zeilen angezeigt. Der vollständige Import wird trotzdem verarbeitet.</p>}
      <div className="commit-bar"><div><b>{preview.valid_rows} Zeilen bereit</b><span>{preview.error_count?`${preview.error_count} Fehler werden ausgelassen.`:'Keine Fehler erkannt.'}</span></div><button className="primary" onClick={commit} disabled={working||preview.valid_rows===0}><Save/> {working?'Import läuft …':'Jetzt importieren'}</button></div>
    </section>}

    {result&&<section className="import-result"><Sparkles/><div><h3>Import abgeschlossen</h3><p><b>{result.created}</b> neu angelegt · <b>{result.updated}</b> aktualisiert · <b>{result.skipped}</b> übersprungen · <b>{result.failed}</b> fehlerhaft</p></div></section>}
  </div>
}


function UpdateCenter({flash}) {
  const [data,setData]=useState(null);
  const [loading,setLoading]=useState(true);
  const [installing,setInstalling]=useState(false);
  const [diagnostics,setDiagnostics]=useState(null);

  const loadUpdates=async(silent=false)=>{
    if(!silent)setLoading(true);
    try{
      const [updates,diag]=await Promise.all([
        api('/api/system/updates'),
        api('/api/system/updates/diagnostics')
      ]);
      setData(updates);setDiagnostics(diag);
    }
    catch(e){if(!silent)flash(e.message)}
    finally{if(!silent)setLoading(false)}
  };

  const rescan=async()=>{
    setLoading(true);
    try{
      await api('/api/system/updates/rescan',{method:'POST'});
      await loadUpdates(true);
      flash('Updateordner wurde neu eingelesen.');
    }catch(e){flash(e.message)}
    finally{setLoading(false)}
  };

  const install=async(pkg)=>{
    const version=pkg.manifest?.version||pkg.filename;
    if(!confirm(`DGD ${version} installieren?\n\nVorher wird automatisch ein Datenbank-Backup erstellt. Während der Umschaltung ist DGD kurz nicht erreichbar.`))return;
    setInstalling(true);
    try{
      await api(`/api/system/updates/${encodeURIComponent(pkg.id)}/install`,{method:'POST'});
      flash(`Installation von DGD ${version} wurde gestartet.`);
    }catch(e){flash(e.message);setInstalling(false)}
  };

  useEffect(()=>{loadUpdates()},[]);
  useEffect(()=>{
    let ticks=0;
    const timer=setInterval(async()=>{
      try{
        const status=await api('/api/system/updates/status');
        setData(current=>current?{...current,status}:current);
        if(['success','error'].includes(status.state))setInstalling(false);
        if(status.state==='success')setTimeout(()=>window.location.reload(),1800);
        ticks++;
        if(ticks%4===0&&!['queued','running'].includes(status.state))await loadUpdates(true);
      }catch{}
    },2500);
    return()=>clearInterval(timer);
  },[]);

  if(loading&&!data)return <div className="empty">Update-Center wird geladen …</div>;

  const status=data?.status||{};
  const busy=['queued','running'].includes(status.state);
  const packages=data?.packages||[];

  return <div className="update-center">
    <section className="update-panel">
      <div className="editor-title"><div><ShieldCheck/> DGD Update-Center</div><button onClick={rescan} disabled={busy||loading}><RefreshCw/> Ordner prüfen</button></div>
      <p className="import-intro">Lege ein gültiges DGD-Update als ZIP-Datei in den Updateordner. DGD prüft das Paket, erstellt vor der Installation ein PostgreSQL-Backup und wechselt erst nach erfolgreichem Image-Build auf die neue Version.</p>
      <div className="update-paths">
        <div><small>Updateordner</small><code>{data?.configuration?.updates_dir||'/updates'}</code></div>
        <div><small>Backupordner</small><code>{data?.configuration?.backups_dir||'/backups'}</code></div>
        <div><small>App-Container</small><code>{data?.configuration?.app_container||'DGD-App'}</code></div>
      </div>
    </section>

    <section className={`update-status update-status-${status.state||'idle'}`}>
      <div className="update-status-head">
        {status.state==='error'?<CircleAlert/>:<RefreshCw className={busy?'spin':''}/>}
        <div><small>Updater-Status</small><h3>{status.message||'Bereit'}</h3></div>
        <b>{status.progress||0}%</b>
      </div>
      <div className="update-progress"><span style={{width:`${status.progress||0}%`}}/></div>
      {status.backup&&<p>Backup: <code>{status.backup}</code></p>}
      {status.log_tail?.length>0&&<details><summary>Technisches Protokoll</summary><pre>{status.log_tail.join('\n')}</pre></details>}
    </section>

    <section className="update-diagnostics">
      <div className="section-head"><div><span className="kicker">Systemprüfung</span><h2>Updater-Verbindung</h2></div></div>
      <div className="diagnostic-grid">
        {[
          ['Docker-Zugriff',diagnostics?.checks?.docker_socket],
          ['DGD-App',diagnostics?.checks?.app_container],
          ['PostgreSQL',diagnostics?.checks?.postgres_container],
          ['Datenbank bereit',diagnostics?.checks?.postgres_ready],
          ['Updateordner',diagnostics?.checks?.updates_writable],
          ['Backupordner',diagnostics?.checks?.backups_writable]
        ].map(([label,check])=><div className={`diagnostic-item ${check?.ok?'ok':'bad'}`} key={label}>
          <b>{check?.ok?'✓':'!'}</b><div><small>{label}</small><span>{check?.ok?(check.message||'Bereit'):(check?.error||'Prüfung fehlgeschlagen')}</span></div>
        </div>)}
      </div>
      {diagnostics?.resolved&&<p className="resolved-info">
        Erkannt: <code>{diagnostics.resolved.app_container||'–'}</code> ·
        PostgreSQL: <code>{diagnostics.resolved.postgres_container||'–'}</code> ·
        App-Version: <code>{diagnostics.resolved.app_version||'–'}</code>
      </p>}
    </section>

    <section className="update-packages">
      <div className="section-head"><div><span className="kicker">Lokale Pakete</span><h2>{packages.length} Update{packages.length===1?'':'s'} gefunden</h2></div></div>
      {packages.length===0?<div className="empty"><PackageOpen/><p>Noch keine ZIP-Datei im Updateordner gefunden.</p></div>:
      <div className="package-list">{packages.map(pkg=><article className={`package-card ${pkg.valid?'':'invalid'}`} key={pkg.id}>
        <div className="package-icon"><PackageOpen/></div>
        <div className="package-main">
          <small>{pkg.filename}</small>
          <h3>{pkg.valid?`DGD ${pkg.manifest.version}`:'Ungültiges Updatepaket'}</h3>
          <p>{pkg.valid?(pkg.manifest.notes?.join(' · ')||'DGD-Aktualisierung'):pkg.error}</p>
          <div className="package-meta">
            <span>{(pkg.size_bytes/1024/1024).toFixed(1)} MB</span>
            {pkg.valid&&<span>Mindestens {pkg.manifest.minimum_version||'keine Vorgabe'}</span>}
            {pkg.valid&&<span>Image {pkg.manifest.image}</span>}
          </div>
        </div>
        <div className="package-action">
          {pkg.valid&&pkg.compatible?<button className="primary" disabled={busy||installing} onClick={()=>install(pkg)}><Save/> Installieren</button>:
          <span className="package-error">{pkg.error||'Nicht kompatibel'}</span>}
        </div>
      </article>)}</div>}
    </section>
  </div>
}

function NotePicker({title,notes,selected,onChange}) {
  const [search,setSearch]=useState('');
  const filtered=notes.filter(n=>n.name.toLowerCase().includes(search.toLowerCase())).slice(0,24);
  const toggle=id=>onChange(selected.includes(id)?selected.filter(x=>x!==id):[...selected,id]);
  const selectedNotes=selected.map(id=>notes.find(n=>n.id===id)).filter(Boolean);
  return <div className="note-picker">
    <div className="note-picker-head"><b>{title}</b><span>{selected.length} gewählt</span></div>
    <input className="note-search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Duftnote suchen …"/>
    {selectedNotes.length>0&&<div className="selected-notes">{selectedNotes.map(n=><button type="button" key={n.id} onClick={()=>toggle(n.id)}>{n.name}<X/></button>)}</div>}
    <div className="note-options">{filtered.map(n=><button type="button" className={selected.includes(n.id)?'selected':''} key={n.id} onClick={()=>toggle(n.id)}><span>{n.name}</span><small>{n.category||'Ohne Kategorie'}</small></button>)}</div>
  </div>
}

function NoteAdmin({notes,reload,flash,editing,setEditing}) {
  const empty={name:'',category:'',description:''};
  const [form,setForm]=useState(empty);
  useEffect(()=>setForm(editing?{...empty,...editing}:empty),[editing]);
  const categories=['Aromatisch','Blumig','Erdig','Fruchtig','Gourmand','Grün','Harzig','Holzig','Leder','Moschus','Rauchig','Synthetisch','Tabak','Würzig','Zitrisch','Nicht kategorisiert'];
  const save=async e=>{
    e.preventDefault();
    try{
      await api(editing?`/api/notes/${editing.id}`:'/api/notes',{method:editing?'PUT':'POST',body:JSON.stringify({...form,category:form.category||null,description:form.description||null})});
      flash(editing?'Duftnote aktualisiert.':'Duftnote angelegt.');
      setEditing(null);setForm(empty);await reload();
    }catch(e){flash(e.message)}
  };
  const remove=async n=>{
    if(!confirm(`Duftnote „${n.name}“ wirklich löschen?`)) return;
    try{await api(`/api/notes/${n.id}`,{method:'DELETE'});flash('Duftnote gelöscht.');await reload()}catch(e){flash(e.message)}
  };
  const grouped=notes.reduce((acc,n)=>{const c=n.category||'Ohne Kategorie';(acc[c]??=[]).push(n);return acc},{});
  return <div className="admin-grid">
    <form className="editor compact" onSubmit={save}>
      <div className="editor-title"><div>{editing?<><Pencil/> Duftnote bearbeiten</>:<><Plus/> Neue Duftnote</>}</div>{editing&&<button type="button" onClick={()=>setEditing(null)}>Abbrechen</button>}</div>
      <Field label="Name *"><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></Field>
      <Field label="Kategorie"><input list="note-categories" value={form.category||''} onChange={e=>setForm({...form,category:e.target.value})}/><datalist id="note-categories">{categories.map(c=><option key={c} value={c}/>)}</datalist></Field>
      <Field label="Beschreibung"><textarea rows="5" value={form.description||''} onChange={e=>setForm({...form,description:e.target.value})}/></Field>
      <button className="primary"><Save/> Speichern</button>
    </form>
    <div className="admin-list note-admin-list"><h3>Duftnoten-Datenbank</h3>{Object.entries(grouped).sort().map(([category,rows])=><div className="note-category" key={category}><h4>{category} <span>{rows.length}</span></h4>{rows.map(n=><div className="admin-row" key={n.id}><div><b>{n.name}</b><span>{n.description||'Keine Beschreibung'}</span></div><div><button onClick={()=>setEditing(n)}><Pencil/></button><button className="danger" onClick={()=>remove(n)}><Trash2/></button></div></div>)}</div>)}</div>
  </div>
}

function BrandAdmin({brands,reload,flash,editing,setEditing}) {
  const [form,setForm]=useState(emptyBrand);
  useEffect(()=>setForm(editing?{...emptyBrand,...editing}:emptyBrand),[editing]);
  const save=async e=>{
    e.preventDefault();
    try{await api(editing?`/api/brands/${editing.id}`:'/api/brands',{method:editing?'PUT':'POST',body:JSON.stringify(form)});flash(editing?'Marke aktualisiert.':'Marke angelegt.');setEditing(null);setForm(emptyBrand);await reload()}catch(e){flash(e.message)}
  };
  const remove=async b=>{if(!confirm(`Marke „${b.name}“ wirklich löschen?`))return;try{await api(`/api/brands/${b.id}`,{method:'DELETE'});flash('Marke gelöscht.');await reload()}catch(e){flash(e.message)}};
  return <div className="admin-grid">
    <form className="editor compact" onSubmit={save}><div className="editor-title"><div>{editing?<><Pencil/> Marke bearbeiten</>:<><Plus/> Neue Marke</>}</div>{editing&&<button type="button" onClick={()=>setEditing(null)}>Abbrechen</button>}</div>
      <Field label="Markenname *"><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></Field>
      <Field label="Herkunftsland"><input value={form.country||''} onChange={e=>setForm({...form,country:e.target.value})}/></Field>
      <Field label="Beschreibung"><textarea rows="5" value={form.description||''} onChange={e=>setForm({...form,description:e.target.value})}/></Field>
      <button className="primary"><Save/> Speichern</button>
    </form>
    <div className="admin-list"><h3>Vorhandene Marken</h3>{brands.map(b=><div className="admin-row" key={b.id}><div><b>{b.name}</b><span>{b.country||'Land nicht erfasst'}</span></div><div><button onClick={()=>setEditing(b)}><Pencil/></button><button className="danger" onClick={()=>remove(b)}><Trash2/></button></div></div>)}</div>
  </div>
}

function TwinAdmin({items,twins,reload,flash}) {
  const [form,setForm]=useState(emptyTwin);
  const set=(k,v)=>setForm(f=>({...f,[k]:v}));
  const save=async e=>{e.preventDefault();try{await api('/api/twins',{method:'POST',body:JSON.stringify({...form,original_id:form.original_id,alternative_id:form.alternative_id,similarity:Number(form.similarity)})});flash('Duftzwilling angelegt.');setForm(emptyTwin);await reload()}catch(e){flash(e.message)}};
  const remove=async t=>{if(!confirm('Diese Duftzwilling-Verknüpfung löschen?'))return;try{await api(`/api/twins/${t.id}`,{method:'DELETE'});flash('Verknüpfung gelöscht.');await reload()}catch(e){flash(e.message)}};
  return <div className="admin-grid">
    <form className="editor compact" onSubmit={save}><div className="editor-title"><div><Plus/> Neuer Duftzwilling</div></div>
      <Field label="Original *"><select required value={form.original_id} onChange={e=>set('original_id',e.target.value)}><option value="">Bitte wählen</option>{items.map(i=><option key={i.id} value={i.id}>{i.brand.name} – {i.name}</option>)}</select></Field>
      <Field label="Alternative *"><select required value={form.alternative_id} onChange={e=>set('alternative_id',e.target.value)}><option value="">Bitte wählen</option>{items.map(i=><option key={i.id} value={i.id}>{i.brand.name} – {i.name}</option>)}</select></Field>
      <Field label={`Ähnlichkeit: ${form.similarity}%`}><input type="range" min="0" max="100" value={form.similarity} onChange={e=>set('similarity',e.target.value)}/></Field>
      <Field label="Gemeinsamkeiten"><textarea rows="3" value={form.commonalities} onChange={e=>set('commonalities',e.target.value)}/></Field>
      <Field label="Unterschiede"><textarea rows="3" value={form.differences} onChange={e=>set('differences',e.target.value)}/></Field>
      <Field label="Quellen-/Prüfhinweis"><textarea rows="2" value={form.source_note} onChange={e=>set('source_note',e.target.value)}/></Field>
      <button className="primary"><Save/> Verknüpfung speichern</button>
    </form>
    <div className="admin-list"><h3>Vorhandene Verknüpfungen</h3>{twins.map(t=><div className="admin-row" key={t.id}><div><small>{Math.round(t.similarity)} % ähnlich</small><b>{t.original.name} → {t.alternative.name}</b><span>{t.original.brand.name} / {t.alternative.brand.name}</span></div><div><button className="danger" onClick={()=>remove(t)}><Trash2/></button></div></div>)}</div>
  </div>
}

function Field({label,children}){return <label className="field"><span>{label}</span>{children}</label>}
function Stat({icon,value,label}){return <article className="stat"><span>{icon}</span><div><strong>{value??'–'}</strong><small>{label}</small></div></article>}
function FragranceCard({item,onOpen}){return <article className="fragrance-card" onClick={()=>onOpen(item)}><div className="bottle">{item.image_url?<img src={item.image_url}/>:<span>{item.brand.name.slice(0,2).toUpperCase()}</span>}</div><div className="card-body"><div className="brand-name">{item.brand.name}</div><h3>{item.name}</h3><div className="chips">{(item.accords||'').split(',').filter(Boolean).slice(0,3).map(a=><span key={a}>{a.trim()}</span>)}</div><div className="card-bottom"><b>{item.price_eur!=null?euro.format(item.price_eur):'Preis offen'}</b><button>Details <ChevronRight size={15}/></button></div></div></article>}
function TwinCard({twin,onOpen}){return <article className="twin-card"><div className="similarity"><strong>{Math.round(twin.similarity)}%</strong><span>Ähnlichkeit</span></div><div className="twin-pair"><button onClick={()=>onOpen(twin.original)}><small>Original</small><b>{twin.original.name}</b><span>{twin.original.brand.name}</span></button><GitCompareArrows/><button onClick={()=>onOpen(twin.alternative)}><small>Alternative</small><b>{twin.alternative.name}</b><span>{twin.alternative.brand.name}</span></button></div><p>{twin.commonalities}</p><div className="saving"><span>Preisunterschied</span><strong>{twin.original.price_eur&&twin.alternative.price_eur?euro.format(twin.original.price_eur-twin.alternative.price_eur):'–'}</strong></div></article>}
function Detail({item,onClose}){return <div className="modal-backdrop" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><article className="modal"><button className="modal-close" onClick={onClose}><X/></button><div className="modal-hero"><div className="big-bottle">{item.image_url?<img src={item.image_url}/>:<span>{item.brand.name.slice(0,2).toUpperCase()}</span>}</div><div><span className="kicker">{item.brand.name}</span><h2>{item.name}</h2><p>{item.description}</p><div className="meta">{item.gender} · {item.concentration||'Konzentration offen'} {item.year?`· ${item.year}`:''}</div><strong className="price">{item.price_eur!=null?euro.format(item.price_eur):'Preis offen'}</strong></div></div><div className="notes"><div><small>Kopfnote</small><p>{item.top_notes||'Noch nicht erfasst'}</p></div><div><small>Herznote</small><p>{item.heart_notes||'Noch nicht erfasst'}</p></div><div><small>Basisnote</small><p>{item.base_notes||'Noch nicht erfasst'}</p></div></div><div className="meters"><Meter label="Haltbarkeit" value={item.longevity}/><Meter label="Projektion" value={item.projection}/><Meter label="Süße" value={item.sweetness}/><Meter label="Frische" value={item.freshness}/></div></article></div>}

createRoot(document.getElementById('root')).render(<App/>);
