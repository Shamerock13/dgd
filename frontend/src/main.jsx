import React, {useEffect, useMemo, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {
  Search, Sparkles, LibraryBig, Tags, GitCompareArrows, Star,
  Moon, Sun, SlidersHorizontal, X, ChevronRight, FlaskConical,
  Settings, Plus, Pencil, Trash2, Save, ArrowLeft, RefreshCw, PackageOpen, ShieldCheck, CircleAlert, Menu,
  BadgeEuro, Clock3, UserRound, Layers3, Info
} from 'lucide-react';
import './styles.css';
import './detail.css';

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
  const [brandFilter,setBrandFilter]=useState('');
  const [genderFilter,setGenderFilter]=useState('');
  const [concentrationFilter,setConcentrationFilter]=useState('');
  const [minPrice,setMinPrice]=useState('');
  const [maxPrice,setMaxPrice]=useState('');
  const [minLongevity,setMinLongevity]=useState('');
  const [sortBy,setSortBy]=useState('brand-name');
  const [selected,setSelected]=useState(null);
  const [detailLoading,setDetailLoading]=useState(false);
  const [filters,setFilters]=useState(false);
  const [mobileNav,setMobileNav]=useState(false);
  const [loading,setLoading]=useState(true);
  const [notice,setNotice]=useState('');

  useEffect(()=>document.documentElement.dataset.theme=dark?'dark':'light',[dark]);

  const load = async () => {
    setLoading(true);
    try {
      const [s,f,b,t,n]=await Promise.all([
        api('/api/dashboard'), api('/api/fragrances'), api('/api/brands'), api('/api/twins'), api('/api/notes')
      ]);
      setStats(s);setItems(f);setBrands(b);setTwins(t);setNotes(n);
    } catch(e){setNotice(e.message)}
    setLoading(false);
  };
  useEffect(()=>{load()},[]);

  const concentrations=useMemo(()=>[...new Set(items.map(i=>i.concentration).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'de')),[items]);

  const filteredItems=useMemo(()=>{
    const needle=query.trim().toLowerCase();
    const filtered=items.filter(item=>{
      const searchable=[
        item.name,item.brand?.name,item.accords,item.top_notes,item.heart_notes,
        item.base_notes,item.perfumer,item.description
      ].filter(Boolean).join(' ').toLowerCase();
      if(needle&&!searchable.includes(needle))return false;
      if(brandFilter&&item.brand?.id!==brandFilter)return false;
      if(genderFilter&&item.gender!==genderFilter)return false;
      if(concentrationFilter&&item.concentration!==concentrationFilter)return false;
      if(minPrice!==''&&(item.price_eur==null||Number(item.price_eur)<Number(minPrice)))return false;
      if(maxPrice!==''&&(item.price_eur==null||Number(item.price_eur)>Number(maxPrice)))return false;
      if(minLongevity!==''&&(item.longevity==null||Number(item.longevity)<Number(minLongevity)))return false;
      return true;
    });
    return [...filtered].sort((a,b)=>{
      if(sortBy==='name')return a.name.localeCompare(b.name,'de');
      if(sortBy==='price-asc')return (a.price_eur??Number.POSITIVE_INFINITY)-(b.price_eur??Number.POSITIVE_INFINITY);
      if(sortBy==='price-desc')return (b.price_eur??Number.NEGATIVE_INFINITY)-(a.price_eur??Number.NEGATIVE_INFINITY);
      if(sortBy==='year-desc')return (b.year??0)-(a.year??0);
      if(sortBy==='longevity-desc')return (b.longevity??-1)-(a.longevity??-1);
      return `${a.brand?.name||''} ${a.name}`.localeCompare(`${b.brand?.name||''} ${b.name}`,'de');
    });
  },[items,query,brandFilter,genderFilter,concentrationFilter,minPrice,maxPrice,minLongevity,sortBy]);

  const activeFilters=[
    query&&{key:'query',label:`Suche: ${query}`,clear:()=>setQuery('')},
    brandFilter&&{key:'brand',label:`Marke: ${brands.find(b=>b.id===brandFilter)?.name||'Auswahl'}`,clear:()=>setBrandFilter('')},
    genderFilter&&{key:'gender',label:`Geschlecht: ${genderFilter}`,clear:()=>setGenderFilter('')},
    concentrationFilter&&{key:'concentration',label:`Konzentration: ${concentrationFilter}`,clear:()=>setConcentrationFilter('')},
    minPrice!==''&&{key:'min-price',label:`ab ${euro.format(Number(minPrice))}`,clear:()=>setMinPrice('')},
    maxPrice!==''&&{key:'max-price',label:`bis ${euro.format(Number(maxPrice))}`,clear:()=>setMaxPrice('')},
    minLongevity!==''&&{key:'longevity',label:`Haltbarkeit ab ${minLongevity}/10`,clear:()=>setMinLongevity('')}
  ].filter(Boolean);

  const resetFilters=()=>{
    setQuery('');setBrandFilter('');setGenderFilter('');setConcentrationFilter('');
    setMinPrice('');setMaxPrice('');setMinLongevity('');setSortBy('brand-name');
  };

  const navigate=next=>{setSelected(null);setTab(next);setMobileNav(false)};
  const openDetail=async item=>{
    setSelected({...item,structured_notes:[]});
    setDetailLoading(true);
    setMobileNav(false);
    window.scrollTo({top:0,behavior:'smooth'});
    try{
      const structured_notes=await api(`/api/fragrances/${item.id}/notes`);
      setSelected(current=>current?.id===item.id?{...current,structured_notes}:current);
    }catch(e){
      flash(`Duftnoten konnten nicht geladen werden: ${e.message}`);
    }finally{
      setDetailLoading(false);
    }
  };
  const flash=(msg)=>{setNotice(msg);setTimeout(()=>setNotice(''),3500)};
  const discoveryItems=filteredItems.slice(0,6);
  const visibleItems=tab==='entdecken'?discoveryItems:filteredItems;

  return <div className="shell">
    <header className="topbar">
      <button className="brand" onClick={()=>navigate('entdecken')}><span className="brand-mark"><FlaskConical size={23}/></span><span><b>DGD</b><small>Das große Duftlexikon</small></span></button>
      <nav className={mobileNav?'open':''}>
        <button className={tab==='entdecken'?'active':''} onClick={()=>navigate('entdecken')}>Entdecken</button>
        <button className={tab==='duefte'?'active':''} onClick={()=>navigate('duefte')}>Alle Düfte</button>
        <button className={tab==='zwillinge'?'active':''} onClick={()=>navigate('zwillinge')}>Duftzwillinge</button>
        <button className={tab==='admin'?'active':''} onClick={()=>navigate('admin')}><Settings size={15}/> Admin</button>
      </nav>
      <div className="topbar-actions">
        <button className="icon-btn mobile-menu" aria-label="Menü öffnen" onClick={()=>setMobileNav(v=>!v)}>{mobileNav?<X size={19}/>:<Menu size={19}/>}</button>
        <button className="icon-btn" aria-label="Farbschema wechseln" onClick={()=>setDark(v=>!v)}>{dark?<Sun size={19}/>:<Moon size={19}/>}</button>
      </div>
    </header>

    {notice && <div className="toast">{notice}</div>}

    {selected ? <DetailPage item={selected} twins={twins} loading={detailLoading} onBack={()=>setSelected(null)} onOpen={openDetail}/> : tab==='admin' ? <AdminCenter brands={brands} items={items} twins={twins} notes={notes} reload={load} flash={flash}/> :
    <main>
      <section className="hero">
        <div className="eyebrow"><Sparkles size={16}/> Wissen, vergleichen, entdecken</div>
        <h1>Finde den Duft, der<br/><em>wirklich</em> zu dir passt.</h1>
        <p>Durchsuche Duftnoten, Akkorde, Marken und Duftzwillinge – ohne Marketingnebel.</p>
        <div className="searchbox"><Search size={21}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="z. B. erdiges Patchouli, Leder oder Lattafa …"/>
          {query&&<button aria-label="Suche löschen" onClick={()=>setQuery('')}><X size={18}/></button>}
          <button className={`filter-button ${activeFilters.length?'has-filters':''}`} onClick={()=>setFilters(v=>!v)}><SlidersHorizontal size={18}/> Filter {activeFilters.length>0&&<b>{activeFilters.length}</b>}</button>
        </div>
        {filters&&<div className="filter-panel">
          <div className="filter-grid">
            <label>Marke<select value={brandFilter} onChange={e=>setBrandFilter(e.target.value)}><option value="">Alle Marken</option>{brands.map(b=><option value={b.id} key={b.id}>{b.name}</option>)}</select></label>
            <label>Geschlecht<select value={genderFilter} onChange={e=>setGenderFilter(e.target.value)}><option value="">Alle</option><option value="Unisex">Unisex</option><option value="Herren">Herren</option><option value="Damen">Damen</option></select></label>
            <label>Konzentration<select value={concentrationFilter} onChange={e=>setConcentrationFilter(e.target.value)}><option value="">Alle</option>{concentrations.map(c=><option value={c} key={c}>{c}</option>)}</select></label>
            <label>Sortierung<select value={sortBy} onChange={e=>setSortBy(e.target.value)}><option value="brand-name">Marke & Name</option><option value="name">Name A–Z</option><option value="price-asc">Preis aufsteigend</option><option value="price-desc">Preis absteigend</option><option value="year-desc">Neueste zuerst</option><option value="longevity-desc">Beste Haltbarkeit</option></select></label>
            <label>Preis von<div className="number-field"><input type="number" min="0" value={minPrice} onChange={e=>setMinPrice(e.target.value)} placeholder="0"/><span>€</span></div></label>
            <label>Preis bis<div className="number-field"><input type="number" min="0" value={maxPrice} onChange={e=>setMaxPrice(e.target.value)} placeholder="100"/><span>€</span></div></label>
            <label>Haltbarkeit ab<div className="number-field"><input type="number" min="0" max="10" step=".5" value={minLongevity} onChange={e=>setMinLongevity(e.target.value)} placeholder="0"/><span>/ 10</span></div></label>
            <button className="clear filter-reset" onClick={resetFilters} disabled={!activeFilters.length&&sortBy==='brand-name'}>Alles zurücksetzen</button>
          </div>
        </div>}
        {activeFilters.length>0&&<div className="active-filters">
          {activeFilters.map(filter=><button key={filter.key} onClick={filter.clear}>{filter.label}<X size={13}/></button>)}
          <button className="reset-chip" onClick={resetFilters}>Alle löschen</button>
        </div>}
      </section>

      <section className="stats-grid">
        <Stat icon={<LibraryBig/>} value={stats.fragrances} label="Düfte"/><Stat icon={<Tags/>} value={stats.brands} label="Marken"/>
        <Stat icon={<GitCompareArrows/>} value={stats.twins} label="Duftzwillinge"/><Stat icon={<Star/>} value={`${stats.average_similarity||0}%`} label="Ø Ähnlichkeit"/>
      </section>

      {(tab==='entdecken'||tab==='duefte')&&<section className="content-section">
        <div className="section-head">
          <div><span className="kicker">Duftdatenbank</span><h2>{query?`Ergebnisse für „${query}“`:tab==='entdecken'?'Ausgewählte Düfte':'Alle Düfte'}</h2></div>
          <div className="result-tools"><span className="result-count">{filteredItems.length} Treffer</span>{tab==='entdecken'&&filteredItems.length>6&&<button className="text-action" onClick={()=>navigate('duefte')}>Alle anzeigen <ChevronRight size={15}/></button>}</div>
        </div>
        {loading?<div className="empty">Düfte werden geladen …</div>:visibleItems.length?<div className="card-grid">{visibleItems.map(i=><FragranceCard key={i.id} item={i} onOpen={openDetail}/>)}</div>:<div className="empty empty-search"><Search/><h3>Keine passenden Düfte</h3><p>Ändere die Suche oder entferne einzelne Filter.</p><button className="clear" onClick={resetFilters}>Filter zurücksetzen</button></div>}
      </section>}

      {(tab==='entdecken'||tab==='zwillinge')&&<section className="content-section twin-section">
        <div className="section-head"><div><span className="kicker">Das Herzstück</span><h2>{tab==='entdecken'?'Starke Duftzwillinge':'Alle Duftzwillinge'}</h2></div>{tab==='entdecken'&&twins.length>4&&<button className="text-action" onClick={()=>navigate('zwillinge')}>Alle anzeigen <ChevronRight size={15}/></button>}</div>
        <div className="twin-grid">{(tab==='entdecken'?twins.slice(0,4):twins).map(t=><TwinCard key={t.id} twin={t} onOpen={openDetail}/>)}</div>
      </section>}

      {tab==='entdecken'&&<section className="content-section brand-section">
        <div className="section-head"><div><span className="kicker">Markenwelt</span><h2>Marken entdecken</h2></div><span className="result-count">{brands.length} Marken</span></div>
        <div className="brand-grid">{brands.slice(0,12).map(brand=><button className="brand-card" key={brand.id} onClick={()=>{setBrandFilter(brand.id);navigate('duefte')}}><span>{brand.name.slice(0,2).toUpperCase()}</span><div><b>{brand.name}</b><small>{brand.country||'Herkunft offen'}</small></div><ChevronRight/></button>)}</div>
      </section>}
    </main>}

    <footer><b>DGD</b><span>Das große Parfum- & Duftzwillinge-Lexikon · Version 2.0 · Entwicklung</span></footer>
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
function FragranceCard({item,onOpen}){
  const accords=(item.accords||"").split(",").map(a=>a.trim()).filter(Boolean).slice(0,3);
  const longevity=item.longevity!=null?Math.max(0,Math.min(10,Number(item.longevity))):null;
  return <article className="fragrance-card" onClick={()=>onOpen(item)}>
    <div className="bottle">
      {item.image_url?<img src={item.image_url} alt={`${item.brand.name} ${item.name}`}/>:<span>{item.brand.name.slice(0,2).toUpperCase()}</span>}
      <div className="card-badges">
        {item.gender&&<span>{item.gender}</span>}
        {item.concentration&&<span>{item.concentration}</span>}
      </div>
    </div>
    <div className="card-body">
      <div className="brand-name">{item.brand.name}</div>
      <h3>{item.name}</h3>
      <div className="fragrance-meta">
        <span>{item.year||"Jahr offen"}</span>
        <span>{item.perfumer||"Parfümeur offen"}</span>
      </div>
      {accords.length>0?<div className="chips">{accords.map(a=><span key={a}>{a}</span>)}</div>:<div className="chips muted-chip"><span>Akkorde noch offen</span></div>}
      {longevity!=null&&<div className="card-rating">
        <div><span>Haltbarkeit</span><strong>{longevity.toFixed(1)}/10</strong></div>
        <div className="card-rating-track"><span style={{width:`${longevity*10}%`}}/></div>
      </div>}
      <div className="card-bottom">
        <b>{item.price_eur!=null?euro.format(item.price_eur):"Preis offen"}</b>
        <button type="button">Details <ChevronRight size={15}/></button>
      </div>
    </div>
  </article>
}
function TwinCard({twin,onOpen}){return <article className="twin-card"><div className="similarity"><strong>{Math.round(twin.similarity)}%</strong><span>Ähnlichkeit</span></div><div className="twin-pair"><button onClick={()=>onOpen(twin.original)}><small>Original</small><b>{twin.original.name}</b><span>{twin.original.brand.name}</span></button><GitCompareArrows/><button onClick={()=>onOpen(twin.alternative)}><small>Alternative</small><b>{twin.alternative.name}</b><span>{twin.alternative.brand.name}</span></button></div><p>{twin.commonalities}</p><div className="saving"><span>Preisunterschied</span><strong>{twin.original.price_eur&&twin.alternative.price_eur?euro.format(twin.original.price_eur-twin.alternative.price_eur):'–'}</strong></div></article>}
function ImageWithFallback({item,className=''}) {
  const [broken,setBroken]=useState(false);
  useEffect(()=>setBroken(false),[item.image_url]);
  if(!item.image_url||broken)return <div className={`detail-image-fallback ${className}`}><span>{item.brand.name.slice(0,2).toUpperCase()}</span><small>Bild folgt</small></div>;
  return <img className={className} src={item.image_url} alt={`${item.brand.name} ${item.name}`} onError={()=>setBroken(true)}/>;
}

function NoteColumn({title,pyramid,rows,fallback}) {
  const structured=rows.filter(row=>row.pyramid===pyramid).sort((a,b)=>a.position-b.position);
  const legacy=structured.length?[]:(fallback||'').split(',').map(value=>value.trim()).filter(Boolean);
  const notes=structured.length?structured.map(row=>({id:row.id,name:row.note.name,category:row.note.category})):legacy.map((name,index)=>({id:`legacy-${pyramid}-${index}`,name,category:null}));
  return <article className={`detail-note-column note-${pyramid}`}>
    <div className="detail-note-heading"><span>{pyramid==='top'?'01':pyramid==='heart'?'02':'03'}</span><div><small>Duftpyramide</small><h3>{title}</h3></div></div>
    {notes.length?<div className="detail-note-list">{notes.map(note=><div key={note.id}><b>{note.name}</b>{note.category&&<small>{note.category}</small>}</div>)}</div>:<p className="detail-empty-copy">Noch nicht erfasst</p>}
  </article>;
}

function DetailTwinCard({twin,item,onOpen}) {
  const itemIsOriginal=twin.original.id===item.id;
  const counterpart=itemIsOriginal?twin.alternative:twin.original;
  const priceDistance=item.price_eur!=null&&counterpart.price_eur!=null?Math.abs(Number(item.price_eur)-Number(counterpart.price_eur)):null;
  const cheaper=priceDistance!=null?(Number(counterpart.price_eur)<Number(item.price_eur)?counterpart:item):null;
  return <article className="detail-twin-card">
    <div className="detail-twin-score"><strong>{Math.round(twin.similarity)}%</strong><span>Ähnlichkeit</span></div>
    <div className="detail-twin-main">
      <small>{itemIsOriginal?'Alternative zu diesem Duft':'Zugeordnetes Original'}</small>
      <h3>{counterpart.name}</h3>
      <p>{counterpart.brand.name}</p>
      <div className="detail-twin-prices"><span>{counterpart.price_eur!=null?euro.format(counterpart.price_eur):'Preis offen'}</span>{priceDistance!=null&&<b>{euro.format(priceDistance)} Abstand</b>}</div>
      {cheaper&&<div className="detail-saving"><BadgeEuro size={17}/>{cheaper.id===counterpart.id?`${counterpart.name} ist günstiger`:`${item.name} ist günstiger`}</div>}
    </div>
    <div className="detail-twin-copy">
      <div><small>Gemeinsamkeiten</small><p>{twin.commonalities||'Noch keine Beschreibung hinterlegt.'}</p></div>
      <div><small>Unterschiede</small><p>{twin.differences||'Noch keine Beschreibung hinterlegt.'}</p></div>
      {twin.source_note&&<div className="detail-source"><Info size={16}/><span>{twin.source_note}</span></div>}
    </div>
    <button className="detail-open-twin" onClick={()=>onOpen(counterpart)}>Duft öffnen <ChevronRight size={16}/></button>
  </article>;
}

function DetailPage({item,twins,loading,onBack,onOpen}) {
  const relatedTwins=twins.filter(twin=>twin.original.id===item.id||twin.alternative.id===item.id);
  const accords=(item.accords||'').split(',').map(value=>value.trim()).filter(Boolean);
  const structuredNotes=item.structured_notes||[];
  useEffect(()=>window.scrollTo({top:0}),[item.id]);
  return <main className="detail-page">
    <div className="detail-toolbar"><button onClick={onBack}><ArrowLeft size={18}/> Zurück zur Übersicht</button><span>DGD Duftprofil</span></div>
    <section className="detail-hero">
      <div className="detail-visual"><ImageWithFallback item={item}/><div className="detail-image-glow"/></div>
      <div className="detail-intro">
        <span className="kicker">{item.brand.name}</span>
        <h1>{item.name}</h1>
        <div className="detail-meta-row">
          <span><Clock3 size={15}/>{item.year||'Jahr offen'}</span>
          <span><Layers3 size={15}/>{item.concentration||'Konzentration offen'}</span>
          <span><UserRound size={15}/>{item.perfumer||'Parfümeur offen'}</span>
        </div>
        <p className="detail-description">{item.description||'Für diesen Duft ist noch keine ausführliche Beschreibung hinterlegt.'}</p>
        {accords.length>0&&<div className="detail-accords">{accords.map(accord=><span key={accord}>{accord}</span>)}</div>}
        <div className="detail-price-block"><small>Erfasster Preis</small><strong>{item.price_eur!=null?euro.format(item.price_eur):'Preis offen'}</strong><span>{item.gender||'Unisex'}</span></div>
      </div>
    </section>

    <section className="detail-section">
      <div className="detail-section-heading"><span className="kicker">Duftaufbau</span><h2>Die Notenpyramide</h2><p>Kopf, Herz und Basis zeigen, wie sich der Duft auf der Haut entwickelt.</p></div>
      {loading?<div className="detail-loading">Strukturierte Duftnoten werden geladen …</div>:<div className="detail-note-grid">
        <NoteColumn title="Kopfnoten" pyramid="top" rows={structuredNotes} fallback={item.top_notes}/>
        <NoteColumn title="Herznoten" pyramid="heart" rows={structuredNotes} fallback={item.heart_notes}/>
        <NoteColumn title="Basisnoten" pyramid="base" rows={structuredNotes} fallback={item.base_notes}/>
      </div>}
    </section>

    <section className="detail-section detail-character">
      <div className="detail-section-heading"><span className="kicker">Charakter</span><h2>So ist der Duft eingeordnet</h2></div>
      <div className="detail-meter-grid"><Meter label="Haltbarkeit" value={item.longevity}/><Meter label="Projektion" value={item.projection}/><Meter label="Süße" value={item.sweetness}/><Meter label="Frische" value={item.freshness}/></div>
    </section>

    <section className="detail-section detail-twins-section">
      <div className="detail-section-heading"><span className="kicker">Duftzwillinge 2.0</span><h2>{relatedTwins.length?`${relatedTwins.length} passende ${relatedTwins.length===1?'Verknüpfung':'Verknüpfungen'}`:'Noch keine Duftzwillinge'}</h2><p>Ähnlichkeit, Unterschiede, Preisabstand und Quellenhinweis direkt am Duft.</p></div>
      {relatedTwins.length?<div className="detail-twin-list">{relatedTwins.map(twin=><DetailTwinCard key={twin.id} twin={twin} item={item} onOpen={onOpen}/>)}</div>:<div className="detail-no-twins"><GitCompareArrows/><h3>Noch keine Verknüpfung vorhanden</h3><p>Dieser Duft kann später über den Admin-Bereich mit Originalen oder Alternativen verbunden werden.</p></div>}
    </section>
  </main>;
}

createRoot(document.getElementById('root')).render(<App/>);
