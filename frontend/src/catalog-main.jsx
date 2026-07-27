import React, {useEffect, useMemo, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {ArrowLeft, ChevronLeft, ChevronRight, FlaskConical, Search, SlidersHorizontal, X} from 'lucide-react';
import './catalog.css';

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
  };
}

function toSearchParams(state, includeDetail=true) {
  const params = new URLSearchParams();
  const mapping = {
    q:'q', brand_id:'brand', gender:'gender', concentration:'concentration', note:'note',
    year_from:'year_from', year_to:'year_to', min_price:'min_price', max_price:'max_price',
    min_longevity:'min_longevity', sort:'sort', page:'page', fragrance:'fragrance',
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
    api('/api/brands').then(setBrands).catch(e=>setError(e.message));
  },[]);

  useEffect(()=>{
    const timer = window.setTimeout(()=>{
      setFilters(current=>current.q===queryInput?current:{...current,q:queryInput,page:1,fragrance:''});
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

  useEffect(()=>{
    replaceUrl(filters);
    const id=++requestId.current;
    setLoading(true);
    setError('');
    const params=toSearchParams(filters,false);
    params.set('page_size',String(PAGE_SIZE));
    if (!params.has('sort')) params.set('sort',filters.q.trim()?'relevance':'brand-name');
    api(`/api/catalog/fragrances?${params}`)
      .then(data=>{
        if(id!==requestId.current)return;
        setItems(data.items||[]);
        setPagination(data.pagination||{});
        setFacets(data.facets||{});
      })
      .catch(e=>{if(id===requestId.current)setError(e.message)})
      .finally(()=>{if(id===requestId.current)setLoading(false)});
  },[filters.q,filters.brand_id,filters.gender,filters.concentration,filters.note,filters.year_from,filters.year_to,filters.min_price,filters.max_price,filters.min_longevity,filters.sort,filters.page]);

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

  const setFilter=(key,value)=>setFilters(current=>({...current,[key]:value,page:1,fragrance:''}));
  const clearAll=()=>{
    const next={q:'',brand_id:'',gender:'',concentration:'',note:'',year_from:'',year_to:'',min_price:'',max_price:'',min_longevity:'',sort:'relevance',page:1,fragrance:''};
    setQueryInput('');
    setFilters(next);
  };
  const openDetail=item=>{
    const next={...filters,fragrance:item.id};
    pushUrl(next);
    setFilters(next);
    window.scrollTo({top:0,behavior:'smooth'});
  };
  const closeDetail=()=>window.history.back();
  const changePage=page=>{
    const next={...filters,page,fragrance:''};
    pushUrl(next);
    setFilters(next);
    window.scrollTo({top:0,behavior:'smooth'});
  };

  const activeCount=['q','brand_id','gender','concentration','note','year_from','year_to','min_price','max_price','min_longevity'].filter(key=>filters[key]!==''&&filters[key]!=null).length;

  if(filters.fragrance){
    return <div className="catalog-shell">
      <Header/>
      <main className="detail-wrap">
        <button className="back-button" onClick={closeDetail}><ArrowLeft size={18}/> Zurück zu den Ergebnissen</button>
        {detailLoading?<div className="catalog-empty">Duft wird geladen …</div>:detail?<Detail fragrance={detail} notes={detailNotes}/>:null}
      </main>
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
        {loading?<div className="catalog-empty">Ergebnisse werden geladen …</div>:items.length?<div className="catalog-grid">{items.map(item=><Card key={item.id} item={item} onOpen={openDetail}/>)}</div>:<div className="catalog-empty"><Search size={30}/><h3>Keine passenden Düfte</h3><p>Ändere die Suche oder entferne einzelne Filter.</p><button onClick={clearAll}>Filter zurücksetzen</button></div>}
        {!loading&&pagination.pages>1&&<Pagination pagination={pagination} onChange={changePage}/>} 
      </section>
    </main>
  </div>;
}

function Header(){return <header className="catalog-header"><a href="/"><span><FlaskConical size={22}/></span><div><b>DGD</b><small>Das große Duftlexikon</small></div></a><nav><a href="/">Bisherige Ansicht</a><a className="active" href="/catalog.html">Katalog 2.0</a></nav></header>}

function Card({item,onOpen}){return <button className="catalog-card" onClick={()=>onOpen(item)}><div className="card-image">{item.image_url?<img src={item.image_url} alt="" loading="lazy"/>:<span>{item.brand?.name?.slice(0,2).toUpperCase()||'DG'}</span>}</div><div className="card-body"><small>{item.brand?.name}</small><h3>{item.name}</h3><p>{[item.concentration,item.year].filter(Boolean).join(' · ')||'Details offen'}</p><div><span>{item.price_eur!=null?euro.format(item.price_eur):'Kein Preis'}</span><ChevronRight size={18}/></div></div></button>}

function Pagination({pagination,onChange}){
  const pages=[];
  const start=Math.max(1,pagination.page-2);
  const end=Math.min(pagination.pages,start+4);
  for(let page=Math.max(1,end-4);page<=end;page++)pages.push(page);
  return <nav className="pagination" aria-label="Seitennavigation"><button disabled={!pagination.has_previous} onClick={()=>onChange(pagination.page-1)}><ChevronLeft size={18}/> Zurück</button>{pages.map(page=><button key={page} className={page===pagination.page?'current':''} onClick={()=>onChange(page)}>{page}</button>)}<button disabled={!pagination.has_next} onClick={()=>onChange(pagination.page+1)}>Weiter <ChevronRight size={18}/></button></nav>
}

function Detail({fragrance,notes}){
  const grouped={top:[],heart:[],base:[]};
  notes.forEach(row=>{if(grouped[row.pyramid])grouped[row.pyramid].push(row.note.name)});
  return <article className="catalog-detail"><div className="detail-image">{fragrance.image_url?<img src={fragrance.image_url} alt=""/>:<span>{fragrance.brand?.name?.slice(0,2).toUpperCase()||'DG'}</span>}</div><div className="detail-content"><small>{fragrance.brand?.name}</small><h1>{fragrance.name}</h1><p className="detail-meta">{[fragrance.concentration,fragrance.year,fragrance.gender].filter(Boolean).join(' · ')}</p>{fragrance.description&&<p>{fragrance.description}</p>}<div className="detail-facts"><div><span>Preis</span><b>{fragrance.price_eur!=null?euro.format(fragrance.price_eur):'Nicht hinterlegt'}</b></div><div><span>Parfümeur</span><b>{fragrance.perfumer||'Nicht hinterlegt'}</b></div><div><span>Haltbarkeit</span><b>{fragrance.longevity!=null?`${fragrance.longevity}/10`:'Nicht bewertet'}</b></div></div><div className="note-groups"><NoteGroup title="Kopfnoten" values={grouped.top}/><NoteGroup title="Herznoten" values={grouped.heart}/><NoteGroup title="Basisnoten" values={grouped.base}/></div>{fragrance.accords&&<div className="accords"><span>Akkorde</span><p>{fragrance.accords}</p></div>}</div></article>
}
function NoteGroup({title,values}){if(!values.length)return null;return <div><span>{title}</span><p>{values.join(', ')}</p></div>}

createRoot(document.getElementById('root')).render(<App/>);
