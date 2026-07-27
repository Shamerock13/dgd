import React, {useEffect, useMemo, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {ArrowLeft, ChevronLeft, ChevronRight, FlaskConical, Search, SlidersHorizontal, X} from 'lucide-react';
import './catalog.css';
import './catalog-profile.css';

const euro = new Intl.NumberFormat('de-DE', {style:'currency', currency:'EUR'});
const PAGE_SIZE = 24;

async function api(url, options={}) {
  const response = await fetch(url, {
    headers: {'Content-Type':'application/json', ...(options.headers||{})},
    ...options,
  });
  if (!response.ok) {
    let message = `Fehler ${response.status}`;
    try { const body = await response.json(); message = body.detail || message; } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function readState() {
  const params = new URLSearchParams(window.location.search);
  return {
    q: params.get('q') || '',
    brand_id: params.get('brand') || '',
    gender: params.get('gender') || '',
    concentration: params.get('concentration') || '',
    note: params.get('note') || '',
    year_from: params.get('year_from') || '',
    year_to: params.get('year_to') || '',
    min_price: params.get('min_price') || '',
    max_price: params.get('max_price') || '',
    min_longevity: params.get('min_longevity') || '',
    sort: params.get('sort') || 'relevance',
    page: Math.max(1, Number(params.get('page') || 1)),
    fragrance: params.get('fragrance') || '',
    profile_type: params.get('profile') || '',
    profile_id: params.get('profile_id') || '',
  };
}

function toSearchParams(state, includeDetail=true) {
  const params = new URLSearchParams();
  const mapping = {
    q:'q', brand_id:'brand', gender:'gender', concentration:'concentration', note:'note',
    year_from:'year_from', year_to:'year_to', min_price:'min_price', max_price:'max_price',
    min_longevity:'min_longevity', sort:'sort', page:'page', fragrance:'fragrance',
    profile_type:'profile', profile_id:'profile_id',
  };
  Object.entries(mapping).forEach(([key,param])=>{
    if (!includeDetail && key === 'fragrance') return;
    const value = state[key];
    if (value === '' || value == null) return;
    if (key === 'sort' && value === 'relevance') return;
    if (key === 'page' && Number(value) === 1) return;
    params.set(param, String(value));
  });
  return params;
}

function replaceUrl(state) {
  const params = toSearchParams(state);
  const url = `${window.location.pathname}${params.toString()?`?${params}`:''}`;
  window.history.replaceState(state, '', url);
}

function pushUrl(state) {
  const params = toSearchParams(state);
  const url = `${window.location.pathname}${params.toString()?`?${params}`:''}`;
  window.history.pushState(state, '', url);
}

function App() {
  const initial = useMemo(readState, []);
  const [filters,setFilters] = useState(initial);
  const [queryInput,setQueryInput] = useState(initial.q);
  const [items,setItems] = useState([]);
  const [brands,setBrands] = useState([]);
  const [perfumers,setPerfumers] = useState([]);
  const [profilesLoading,setProfilesLoading] = useState(true);
  const [facets,setFacets] = useState({concentrations:[],year_min:null,year_max:null});
  const [pagination,setPagination] = useState({page:1,pages:0,total:0,has_previous:false,has_next:false});
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState('');
  const [showFilters,setShowFilters] = useState(false);
  const [detail,setDetail] = useState(null);
  const [detailNotes,setDetailNotes] = useState([]);
  const [detailLoading,setDetailLoading] = useState(false);
  const requestId = useRef(0);

  useEffect(()=>{
    Promise.all([api('/api/brands'), api('/api/perfumers')])
      .then(([brandRows,perfumerRows])=>{setBrands(brandRows||[]);setPerfumers(perfumerRows||[])})
      .catch(e=>setError(e.message))
      .finally(()=>setProfilesLoading(false));
  },[]);

  useEffect(()=>{
    const timer = window.setTimeout(()=>{
      setFilters(current=>current.q===queryInput?current:{...current,q:queryInput,page:1,fragrance:'',profile_type:'',profile_id:''});
    }, 300);
    return ()=>window.clearTimeout(timer);
  },[queryInput]);

  useEffect(()=>{
    const onPopState=()=>{
      const next=readState();
      setFilters(next);
      setQueryInput(next.q);
    };
    window.addEventListener('popstate',onPopState);
    return ()=>window.removeEventListener('popstate',onPopState);
  },[]);

  const activeProfile = useMemo(()=>{
    if(filters.profile_type==='brand') return brands.find(row=>row.id===filters.profile_id)||null;
    if(filters.profile_type==='perfumer') return perfumers.find(row=>row.id===filters.profile_id)||null;
    return null;
  },[filters.profile_type,filters.profile_id,brands,perfumers]);

  useEffect(()=>{
    replaceUrl(filters);
    const id=++requestId.current;
    setLoading(true);
    setError('');
    const params=new URLSearchParams();
    params.set('page_size',String(PAGE_SIZE));
    params.set('page',String(filters.page));

    if(filters.profile_type==='brand'&&filters.profile_id){
      params.set('brand_id',filters.profile_id);
      params.set('sort',filters.sort==='relevance'?'name':filters.sort);
    }else if(filters.profile_type==='perfumer'&&activeProfile){
      params.set('perfumer',activeProfile.name);
      params.set('sort',filters.sort==='relevance'?'brand-name':filters.sort);
    }else{
      const regular=toSearchParams(filters,false);
      ['q','brand','gender','concentration','note','year_from','year_to','min_price','max_price','min_longevity','sort'].forEach(key=>{
        if(regular.has(key)) params.set(key==='brand'?'brand_id':key,regular.get(key));
      });
      if(!params.has('sort')) params.set('sort',filters.q.trim()?'relevance':'brand-name');
    }

    if(filters.profile_type==='perfumer'&&!activeProfile&&profilesLoading) return;

    api(`/api/catalog/fragrances?${params}`)
      .then(data=>{
        if(id!==requestId.current)return;
        setItems(data.items||[]);
        setPagination(data.pagination||{});
        setFacets(data.facets||{});
      })
      .catch(e=>{if(id===requestId.current)setError(e.message)})
      .finally(()=>{if(id===requestId.current)setLoading(false)});
  },[filters.q,filters.brand_id,filters.gender,filters.concentration,filters.note,filters.year_from,filters.year_to,filters.min_price,filters.max_price,filters.min_longevity,filters.sort,filters.page,filters.profile_type,filters.profile_id,activeProfile,profilesLoading]);

  useEffect(()=>{
    if(!filters.fragrance){setDetail(null);setDetailNotes([]);return;}
    setDetailLoading(true);
    Promise.all([
      api(`/api/fragrances/${filters.fragrance}`),
      api(`/api/fragrances/${filters.fragrance}/notes`),
    ]).then(([fragrance,notes])=>{setDetail(fragrance);setDetailNotes(notes||[])})
      .catch(e=>{setError(e.message);setFilters(current=>({...current,fragrance:''}))})
      .finally(()=>setDetailLoading(false));
  },[filters.fragrance]);

  const setFilter=(key,value)=>setFilters(current=>({...current,[key]:value,page:1,fragrance:'',profile_type:'',profile_id:''}));
  const clearAll=()=>{
    const next={q:'',brand_id:'',gender:'',concentration:'',note:'',year_from:'',year_to:'',min_price:'',max_price:'',min_longevity:'',sort:'relevance',page:1,fragrance:'',profile_type:'',profile_id:''};
    setQueryInput('');
    setFilters(next);
  };
  const openDetail=item=>{
    const next={...filters,fragrance:item.id};
    pushUrl(next);
    setFilters(next);
    window.scrollTo({top:0,behavior:'smooth'});
  };
  const openProfile=(type,id)=>{
    const next={...filters,profile_type:type,profile_id:id,fragrance:'',page:1};
    pushUrl(next);
    setFilters(next);
    window.scrollTo({top:0,behavior:'smooth'});
  };
  const closeView=()=>window.history.back();
  const changePage=page=>{
    const next={...filters,page,fragrance:''};
    pushUrl(next);
    setFilters(next);
    window.scrollTo({top:0,behavior:'smooth'});
  };

  const activeCount=['q','brand_id','gender','concentration','note','year_from','year_to','min_price','max_price','min_longevity'].filter(key=>filters[key]!==''&&filters[key]!=null).length;
  const detailPerfumer=detail?.perfumer?perfumers.find(row=>row.name.toLocaleLowerCase('de-DE')===detail.perfumer.toLocaleLowerCase('de-DE')):null;

  if(filters.fragrance){
    return <div className="catalog-shell">
      <Header/>
      <main className="detail-wrap">
        <button className="back-button" onClick={closeView}><ArrowLeft size={18}/> Zurück</button>
        {detailLoading?<div className="catalog-empty">Duft wird geladen …</div>:detail?<Detail fragrance={detail} notes={detailNotes} perfumer={detailPerfumer} onBrand={()=>openProfile('brand',detail.brand.id)} onPerfumer={detailPerfumer?()=>openProfile('perfumer',detailPerfumer.id):null}/>:null}
      </main>
    </div>;
  }

  if(filters.profile_type){
    return <div className="catalog-shell">
      <Header/>
      <ProfileView type={filters.profile_type} profile={activeProfile} profilesLoading={profilesLoading} items={items} loading={loading} error={error} pagination={pagination} onBack={closeView} onOpen={openDetail} onBrand={id=>openProfile('brand',id)} onPage={changePage}/>
    </div>;
  }

  return <div className="catalog-shell">
    <Header/>
    <main>
      <section className="catalog-hero">
        <div className="eyebrow"><FlaskConical size={17}/> Katalog 2.0</div>
        <h1>Düfte finden, filtern und wiederfinden.</h1>
        <p>Die Suche läuft serverseitig, bleibt in der URL erhalten und bringt dich nach einer Detailansicht exakt zurück.</p>
        <div className="catalog-search"><Search size={21}/><input value={queryInput} onChange={e=>setQueryInput(e.target.value)} placeholder="Duft, Marke, Note, Akkord oder Parfümeur …"/>{queryInput&&<button onClick={()=>setQueryInput('')} aria-label="Suche löschen"><X size={18}/></button>}<button className={activeCount?'active':''} onClick={()=>setShowFilters(v=>!v)}><SlidersHorizontal size={18}/> Filter {activeCount>0&&<b>{activeCount}</b>}</button></div>
        {showFilters&&<div className="catalog-filters">
          <label>Marke<select value={filters.brand_id} onChange={e=>setFilter('brand_id',e.target.value)}><option value="">Alle Marken</option>{brands.map(brand=><option key={brand.id} value={brand.id}>{brand.name}</option>)}</select></label>
          <label>Zielgruppe<select value={filters.gender} onChange={e=>setFilter('gender',e.target.value)}><option value="">Alle</option><option>Unisex</option><option>Herren</option><option>Damen</option></select></label>
          <label>Konzentration<select value={filters.concentration} onChange={e=>setFilter('concentration',e.target.value)}><option value="">Alle</option>{(facets.concentrations||[]).map(value=><option key={value}>{value}</option>)}</select></label>
          <label>Duftnote<input value={filters.note} onChange={e=>setFilter('note',e.target.value)} placeholder="z. B. Patchouli"/></label>
          <label>Jahr von<input type="number" min="1500" max="2200" value={filters.year_from} onChange={e=>setFilter('year_from',e.target.value)} placeholder={facets.year_min||''}/></label>
          <label>Jahr bis<input type="number" min="1500" max="2200" value={filters.year_to} onChange={e=>setFilter('year_to',e.target.value)} placeholder={facets.year_max||''}/></label>
          <label>Preis von<input type="number" min="0" value={filters.min_price} onChange={e=>setFilter('min_price',e.target.value)} placeholder="0"/></label>
          <label>Preis bis<input type="number" min="0" value={filters.max_price} onChange={e=>setFilter('max_price',e.target.value)} placeholder="100"/></label>
          <label>Haltbarkeit ab<input type="number" min="0" max="10" step="0.5" value={filters.min_longevity} onChange={e=>setFilter('min_longevity',e.target.value)} placeholder="0"/></label>
          <label>Sortierung<select value={filters.sort} onChange={e=>setFilter('sort',e.target.value)}><option value="relevance">Relevanz</option><option value="brand-name">Marke & Name</option><option value="name">Name A–Z</option><option value="price-asc">Preis aufsteigend</option><option value="price-desc">Preis absteigend</option><option value="year-desc">Neueste zuerst</option><option value="longevity-desc">Beste Haltbarkeit</option></select></label>
          <button className="clear-button" onClick={clearAll}>Alle Filter löschen</button>
        </div>}
      </section>

      <section className="catalog-results">
        <div className="catalog-result-head"><div><span>Duftdatenbank</span><h2>{filters.q?`Ergebnisse für „${filters.q}“`:'Alle Düfte'}</h2></div><strong>{pagination.total||0} Treffer</strong></div>
        {error&&<div className="catalog-error">{error}</div>}
        {loading?<div className="catalog-empty">Ergebnisse werden geladen …</div>:items.length?<div className="catalog-grid">{items.map(item=><Card key={item.id} item={item} onOpen={openDetail} onBrand={id=>openProfile('brand',id)}/>)}</div>:<div className="catalog-empty"><Search size={30}/><h3>Keine passenden Düfte</h3><p>Ändere die Suche oder entferne einzelne Filter.</p><button onClick={clearAll}>Filter zurücksetzen</button></div>}
        {!loading&&pagination.pages>1&&<Pagination pagination={pagination} onChange={changePage}/>} 
      </section>
    </main>
  </div>;
}

function Header(){return <header className="catalog-header"><a href="/"><span><FlaskConical size={22}/></span><div><b>DGD</b><small>Das große Duftlexikon</small></div></a><nav><a className="active" href="/">Duftkatalog</a><a href="/admin.html">Admin Center</a></nav></header>}

function Card({item,onOpen,onBrand}){return <article className="catalog-card" role="button" tabIndex="0" onClick={()=>onOpen(item)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onOpen(item)}}}><div className="card-image">{item.image_url?<img src={item.image_url} alt="" loading="lazy"/>:<span>{item.brand?.name?.slice(0,2).toUpperCase()||'DG'}</span>}</div><div className="card-body"><button className="profile-link" onClick={e=>{e.stopPropagation();onBrand(item.brand.id)}}>{item.brand?.name}</button><h3>{item.name}</h3><p>{[item.concentration,item.year].filter(Boolean).join(' · ')||'Details offen'}</p><div><span>{item.price_eur!=null?euro.format(item.price_eur):'Kein Preis'}</span><ChevronRight size={18}/></div></div></article>}

function Pagination({pagination,onChange}){
  const pages=[];
  const start=Math.max(1,pagination.page-2);
  const end=Math.min(pagination.pages,start+4);
  for(let page=Math.max(1,end-4);page<=end;page++)pages.push(page);
  return <nav className="pagination" aria-label="Seitennavigation"><button disabled={!pagination.has_previous} onClick={()=>onChange(pagination.page-1)}><ChevronLeft size={18}/> Zurück</button>{pages.map(page=><button key={page} className={page===pagination.page?'current':''} onClick={()=>onChange(page)}>{page}</button>)}<button disabled={!pagination.has_next} onClick={()=>onChange(pagination.page+1)}>Weiter <ChevronRight size={18}/></button></nav>
}

function ProfileView({type,profile,profilesLoading,items,loading,error,pagination,onBack,onOpen,onBrand,onPage}){
  const isBrand=type==='brand';
  if(profilesLoading)return <main className="profile-wrap"><button className="back-button" onClick={onBack}><ArrowLeft size={18}/> Zurück</button><div className="catalog-empty">Profil wird geladen …</div></main>;
  if(!profile)return <main className="profile-wrap"><button className="back-button" onClick={onBack}><ArrowLeft size={18}/> Zurück</button><div className="profile-empty">Dieses Profil wurde nicht gefunden.</div></main>;
  return <main className="profile-wrap">
    <button className="back-button" onClick={onBack}><ArrowLeft size={18}/> Zurück</button>
    <section className="profile-hero">
      <div><small>{isBrand?'Markenprofil':'Parfümeurprofil'}</small><h1>{profile.name}</h1><p>{(isBrand?profile.description:profile.profile)||'Für dieses Profil ist noch keine ausführliche Beschreibung hinterlegt.'}</p></div>
      <div className="profile-meta">
        {isBrand?<><Meta label="Herkunft" value={profile.country}/><Meta label="Gegründet" value={profile.founded_year}/>{profile.website_url&&<div><span>Website</span><a href={profile.website_url} target="_blank" rel="noreferrer">Offizielle Seite ↗</a></div>}</>:<><Meta label="Nationalität" value={profile.nationality}/><Meta label="Geburtsjahr" value={profile.birth_year}/><Meta label="Stil" value={profile.style}/></>}
      </div>
    </section>
    <section>
      <div className="profile-results-head"><div><span>{isBrand?'Düfte der Marke':'Kreationen'}</span><h2>{pagination.total||0} zugeordnete Düfte</h2></div></div>
      {error&&<div className="catalog-error">{error}</div>}
      {loading?<div className="catalog-empty">Düfte werden geladen …</div>:items.length?<div className="catalog-grid">{items.map(item=><Card key={item.id} item={item} onOpen={onOpen} onBrand={onBrand}/>)}</div>:<div className="profile-empty">Noch keine Düfte zugeordnet.</div>}
      {!loading&&pagination.pages>1&&<Pagination pagination={pagination} onChange={onPage}/>} 
    </section>
  </main>;
}

function Meta({label,value}){if(value==null||value==='')return null;return <div><span>{label}</span><b>{value}</b></div>}

function Detail({fragrance,notes,perfumer,onBrand,onPerfumer}){
  const grouped={top:[],heart:[],base:[]};
  notes.forEach(row=>{if(grouped[row.pyramid])grouped[row.pyramid].push(row.note.name)});
  return <article className="catalog-detail"><div className="detail-image">{fragrance.image_url?<img src={fragrance.image_url} alt=""/>:<span>{fragrance.brand?.name?.slice(0,2).toUpperCase()||'DG'}</span>}</div><div className="detail-content"><button className="profile-link" onClick={onBrand}>{fragrance.brand?.name}</button><h1>{fragrance.name}</h1><p className="detail-meta">{[fragrance.concentration,fragrance.year,fragrance.gender].filter(Boolean).join(' · ')}</p>{fragrance.description&&<p>{fragrance.description}</p>}<div className="detail-facts"><div><span>Preis</span><b>{fragrance.price_eur!=null?euro.format(fragrance.price_eur):'Nicht hinterlegt'}</b></div><div><span>Parfümeur</span>{onPerfumer?<button className="profile-link" onClick={onPerfumer}>{perfumer.name}</button>:<b>{fragrance.perfumer||'Nicht hinterlegt'}</b>}</div><div><span>Haltbarkeit</span><b>{fragrance.longevity!=null?`${fragrance.longevity}/10`:'Nicht bewertet'}</b></div></div><div className="note-groups"><NoteGroup title="Kopfnoten" values={grouped.top}/><NoteGroup title="Herznoten" values={grouped.heart}/><NoteGroup title="Basisnoten" values={grouped.base}/></div>{fragrance.accords&&<div className="accords"><span>Akkorde</span><p>{fragrance.accords}</p></div>}</div></article>
}
function NoteGroup({title,values}){if(!values.length)return null;return <div><span>{title}</span><p>{values.join(', ')}</p></div>}

createRoot(document.getElementById('root')).render(<App/>);
