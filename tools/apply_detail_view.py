from pathlib import Path

MAIN = Path("frontend/src/main.jsx")
DETAIL_CSS = Path("frontend/src/detail.css")

source = MAIN.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global source
    if old not in source:
        raise RuntimeError(f"Expected source block not found:\n{old[:240]}")
    source = source.replace(old, new, 1)


replace_once(
    "  Settings, Plus, Pencil, Trash2, Save, ArrowLeft, RefreshCw, PackageOpen, ShieldCheck, CircleAlert, Menu\n",
    "  Settings, Plus, Pencil, Trash2, Save, ArrowLeft, RefreshCw, PackageOpen, ShieldCheck, CircleAlert, Menu,\n  BadgeEuro, Clock3, UserRound, Layers3, Info\n",
)
replace_once("import './styles.css';\n", "import './styles.css';\nimport './detail.css';\n")
replace_once(
    "  const [selected,setSelected]=useState(null);\n",
    "  const [selected,setSelected]=useState(null);\n  const [detailLoading,setDetailLoading]=useState(false);\n",
)
replace_once(
    "  const navigate=next=>{setTab(next);setMobileNav(false)};\n",
    """  const navigate=next=>{setSelected(null);setTab(next);setMobileNav(false)};
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
""",
)
replace_once(
    "    {tab==='admin' ? <AdminCenter brands={brands} items={items} twins={twins} notes={notes} reload={load} flash={flash}/> :\n",
    "    {selected ? <DetailPage item={selected} twins={twins} loading={detailLoading} onBack={()=>setSelected(null)} onOpen={openDetail}/> : tab==='admin' ? <AdminCenter brands={brands} items={items} twins={twins} notes={notes} reload={load} flash={flash}/> :\n",
)
source = source.replace("onOpen={setSelected}", "onOpen={openDetail}")
replace_once("    {selected&&<Detail item={selected} onClose={()=>setSelected(null)}/>}\n", "")

old_detail = "function Detail({item,onClose}){return <div className=\"modal-backdrop\" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><article className=\"modal\"><button className=\"modal-close\" onClick={onClose}><X/></button><div className=\"modal-hero\"><div className=\"big-bottle\">{item.image_url?<img src={item.image_url}/>:<span>{item.brand.name.slice(0,2).toUpperCase()}</span>}</div><div><span className=\"kicker\">{item.brand.name}</span><h2>{item.name}</h2><p>{item.description}</p><div className=\"meta\">{item.gender} · {item.concentration||'Konzentration offen'} {item.year?`· ${item.year}`:''}</div><strong className=\"price\">{item.price_eur!=null?euro.format(item.price_eur):'Preis offen'}</strong></div></div><div className=\"notes\"><div><small>Kopfnote</small><p>{item.top_notes||'Noch nicht erfasst'}</p></div><div><small>Herznote</small><p>{item.heart_notes||'Noch nicht erfasst'}</p></div><div><small>Basisnote</small><p>{item.base_notes||'Noch nicht erfasst'}</p></div></div><div className=\"meters\"><Meter label=\"Haltbarkeit\" value={item.longevity}/><Meter label=\"Projektion\" value={item.projection}/><Meter label=\"Süße\" value={item.sweetness}/><Meter label=\"Frische\" value={item.freshness}/></div></article></div>}"

new_detail = r'''function ImageWithFallback({item,className=''}) {
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
}'''

replace_once(old_detail, new_detail)
MAIN.write_text(source, encoding="utf-8")

DETAIL_CSS.write_text(r'''/* DGD 2.0: eigene Duftdetailansicht */
.detail-page{max-width:1280px;margin:0 auto;padding:34px 28px 100px}.detail-toolbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:30px;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.12em}.detail-toolbar button{display:flex;align-items:center;gap:8px;border:1px solid var(--line);background:var(--surface);color:var(--text);padding:11px 15px;border-radius:12px;cursor:pointer;text-transform:none;letter-spacing:0}.detail-hero{display:grid;grid-template-columns:minmax(300px,.85fr) minmax(0,1.15fr);gap:64px;align-items:center;padding:28px 0 80px}.detail-visual{min-height:510px;border-radius:32px;background:radial-gradient(circle at 50% 38%,color-mix(in srgb,var(--gold) 25%,transparent),transparent 56%),var(--surface2);display:grid;place-items:center;position:relative;overflow:hidden;border:1px solid var(--line)}.detail-visual>img{width:88%;height:440px;object-fit:contain;position:relative;z-index:2}.detail-image-fallback{position:relative;z-index:2;width:190px;height:275px;border:1px solid color-mix(in srgb,var(--gold) 72%,var(--line));border-radius:58px 58px 22px 22px;display:grid;place-items:center;align-content:center;gap:8px;background:color-mix(in srgb,var(--surface) 75%,transparent);box-shadow:inset 0 0 55px color-mix(in srgb,var(--gold) 15%,transparent),0 30px 60px rgba(0,0,0,.13)}.detail-image-fallback span{font-family:'Playfair Display';font-size:52px;color:var(--gold)}.detail-image-fallback small{color:var(--muted);text-transform:uppercase;letter-spacing:.12em}.detail-image-glow{position:absolute;width:260px;height:70px;bottom:30px;border-radius:50%;background:rgba(0,0,0,.2);filter:blur(18px)}.detail-intro h1{font-family:'Playfair Display';font-size:clamp(52px,7vw,92px);line-height:.95;margin:12px 0 24px}.detail-meta-row{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:28px}.detail-meta-row span{display:flex;align-items:center;gap:7px;padding:8px 11px;border:1px solid var(--line);border-radius:30px;color:var(--muted);font-size:12px;background:var(--surface)}.detail-description{color:var(--muted);line-height:1.8;font-size:17px;max-width:720px}.detail-accords{display:flex;flex-wrap:wrap;gap:8px;margin:25px 0}.detail-accords span{padding:8px 12px;border-radius:30px;background:var(--surface2);color:var(--text);font-size:12px}.detail-price-block{display:grid;grid-template-columns:1fr auto;gap:3px 20px;align-items:end;border-top:1px solid var(--line);padding-top:25px;margin-top:28px;max-width:540px}.detail-price-block small{color:var(--muted)}.detail-price-block strong{grid-row:1/3;grid-column:2;font-family:'Playfair Display';font-size:36px;color:var(--gold)}.detail-price-block span{font-size:13px}.detail-section{padding:68px 0;border-top:1px solid var(--line)}.detail-section-heading{max-width:720px;margin-bottom:30px}.detail-section-heading h2{font-family:'Playfair Display';font-size:clamp(36px,5vw,56px);margin:7px 0 10px}.detail-section-heading p{color:var(--muted);line-height:1.6}.detail-note-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.detail-note-column{background:var(--surface);border:1px solid var(--line);border-radius:22px;padding:24px;min-height:250px}.detail-note-heading{display:flex;gap:14px;align-items:center;padding-bottom:18px;border-bottom:1px solid var(--line)}.detail-note-heading>span{font-family:'Playfair Display';font-size:31px;color:var(--gold)}.detail-note-heading small{color:var(--muted);text-transform:uppercase;letter-spacing:.12em;font-size:9px}.detail-note-heading h3{font-family:'Playfair Display';font-size:24px;margin:2px 0}.detail-note-list{display:grid;gap:9px;margin-top:18px}.detail-note-list>div{display:flex;justify-content:space-between;gap:10px;padding:11px 12px;background:var(--surface2);border-radius:11px}.detail-note-list b{font-size:13px}.detail-note-list small{color:var(--muted);font-size:10px}.detail-empty-copy{color:var(--muted);font-size:13px}.detail-loading{padding:42px;background:var(--surface);border:1px dashed var(--line);border-radius:18px;color:var(--muted);text-align:center}.detail-meter-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:22px;background:var(--surface);border:1px solid var(--line);padding:28px;border-radius:22px}.detail-meter-grid .meter{padding:7px}.detail-meter-grid .meter-track{height:10px}.detail-twin-list{display:grid;gap:18px}.detail-twin-card{display:grid;grid-template-columns:115px minmax(220px,.75fr) minmax(300px,1.25fr) auto;gap:24px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:24px;padding:24px}.detail-twin-score{width:104px;height:104px;border-radius:50%;border:8px solid var(--surface2);box-shadow:inset 0 0 0 2px var(--gold);display:grid;place-items:center;align-content:center}.detail-twin-score strong{font-family:'Playfair Display';font-size:29px;color:var(--gold)}.detail-twin-score span{font-size:9px;color:var(--muted);text-transform:uppercase}.detail-twin-main>small,.detail-twin-copy small{color:var(--gold);text-transform:uppercase;letter-spacing:.1em;font-size:9px}.detail-twin-main h3{font-family:'Playfair Display';font-size:29px;margin:5px 0}.detail-twin-main p{color:var(--muted);margin:0}.detail-twin-prices{display:flex;gap:10px;align-items:center;margin-top:14px}.detail-twin-prices span{font-weight:700}.detail-twin-prices b{font-size:10px;padding:5px 8px;background:var(--surface2);border-radius:20px;color:var(--muted)}.detail-saving{display:flex;gap:7px;align-items:center;color:var(--gold);font-size:11px;margin-top:10px}.detail-twin-copy{display:grid;grid-template-columns:1fr 1fr;gap:15px}.detail-twin-copy p{color:var(--muted);font-size:12px;line-height:1.55;margin:6px 0 0}.detail-source{grid-column:1/-1;display:flex;gap:8px;align-items:flex-start;padding:9px 11px;border-radius:10px;background:var(--surface2);color:var(--muted);font-size:11px}.detail-open-twin{display:flex;align-items:center;gap:6px;border:0;background:var(--text);color:var(--bg);padding:11px 13px;border-radius:11px;cursor:pointer;white-space:nowrap}.detail-no-twins{text-align:center;padding:55px;background:var(--surface);border:1px dashed var(--line);border-radius:22px;color:var(--muted)}.detail-no-twins svg{color:var(--gold);width:34px;height:34px}.detail-no-twins h3{font-family:'Playfair Display';font-size:27px;color:var(--text);margin:12px 0 6px}
@media(max-width:1000px){.detail-hero{grid-template-columns:1fr;gap:35px}.detail-visual{min-height:390px}.detail-visual>img{height:340px}.detail-twin-card{grid-template-columns:105px 1fr}.detail-twin-copy{grid-column:1/-1}.detail-open-twin{grid-column:2;justify-self:start}.detail-note-grid{grid-template-columns:1fr}}
@media(max-width:650px){.detail-page{padding:24px 16px 70px}.detail-toolbar>span{display:none}.detail-hero{padding-bottom:55px}.detail-visual{min-height:330px;border-radius:23px}.detail-visual>img{height:290px}.detail-image-fallback{width:145px;height:215px}.detail-intro h1{font-size:50px}.detail-description{font-size:15px}.detail-price-block strong{font-size:29px}.detail-meter-grid{grid-template-columns:1fr;padding:18px}.detail-twin-card{grid-template-columns:1fr;padding:19px}.detail-twin-score{width:88px;height:88px}.detail-twin-copy{grid-template-columns:1fr}.detail-open-twin{grid-column:1}.detail-note-column{min-height:0}}
''', encoding="utf-8")
