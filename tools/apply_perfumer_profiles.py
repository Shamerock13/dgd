from pathlib import Path


def replace_once(path, old, new):
    text=Path(path).read_text(encoding='utf-8')
    if old not in text:
        raise RuntimeError(f'Missing block in {path}: {old[:100]}')
    Path(path).write_text(text.replace(old,new,1),encoding='utf-8')

replace_once('backend/app/main.py','from .source_routes import router as source_router\n','from .source_routes import router as source_router\nfrom .perfumer_routes import router as perfumer_router\n')
replace_once('backend/app/main.py','app.include_router(source_router)\n','app.include_router(source_router)\napp.include_router(perfumer_router)\n')

p=Path('backend/app/migrations.py'); text=p.read_text(encoding='utf-8')
marker='\n)\n\n\ndef _ensure_migration_table'
block='''\n    Migration(\n        version="0010",\n        description="Parfümeurprofile und Artikelstatus absichern",\n        statements=(\n            "UPDATE master_perfumers SET article_status = 'OPEN' WHERE article_status IS NULL OR btrim(article_status) = ''",\n            "CREATE INDEX IF NOT EXISTS ix_master_perfumers_article_status ON master_perfumers (article_status)",\n        ),\n    ),\n'''
if 'version="0010"' not in text:
    text=text.replace(marker,block+marker,1);p.write_text(text,encoding='utf-8')

replace_once('frontend/src/main.jsx',"import VerificationAdmin from './verification.jsx';\n","import VerificationAdmin from './verification.jsx';\nimport {PerfumerAdmin, PerfumerProfile} from './perfumer.jsx';\n")
replace_once('frontend/src/main.jsx','  const [notes,setNotes]=useState([]);\n','  const [notes,setNotes]=useState([]);\n  const [perfumers,setPerfumers]=useState([]);\n')
replace_once('frontend/src/main.jsx','  const [selectedBrand,setSelectedBrand]=useState(null);\n','  const [selectedBrand,setSelectedBrand]=useState(null);\n  const [selectedPerfumer,setSelectedPerfumer]=useState(null);\n')
replace_once('frontend/src/main.jsx',"      const [s,f,b,t,n]=await Promise.all([\n        api('/api/dashboard'), api('/api/fragrances'), api('/api/brands'), api('/api/twins'), api('/api/notes')\n      ]);\n      setStats(s);setItems(f);setBrands(b);setTwins(t);setNotes(n);\n","      const [s,f,b,t,n,p]=await Promise.all([\n        api('/api/dashboard'), api('/api/fragrances'), api('/api/brands'), api('/api/twins'), api('/api/notes'), api('/api/perfumers')\n      ]);\n      setStats(s);setItems(f);setBrands(b);setTwins(t);setNotes(n);setPerfumers(p);\n")
replace_once('frontend/src/main.jsx','  const navigate=next=>{setSelected(null);setSelectedBrand(null);setTab(next);setMobileNav(false)};\n','  const navigate=next=>{setSelected(null);setSelectedBrand(null);setSelectedPerfumer(null);setTab(next);setMobileNav(false)};\n')
replace_once('frontend/src/main.jsx','  const openBrand=brand=>{setSelected(null);setSelectedBrand(brand);setMobileNav(false);window.scrollTo({top:0,behavior:\'smooth\'})};\n','  const openBrand=brand=>{setSelected(null);setSelectedPerfumer(null);setSelectedBrand(brand);setMobileNav(false);window.scrollTo({top:0,behavior:\'smooth\'})};\n  const openPerfumer=name=>{const profile=perfumers.find(p=>p.name.trim().toLowerCase()===String(name||\'\').trim().toLowerCase());if(profile){setSelected(null);setSelectedBrand(null);setSelectedPerfumer(profile);window.scrollTo({top:0,behavior:\'smooth\'})}else flash(`Für ${name} ist noch kein Profil angelegt.`)};\n')
replace_once('frontend/src/main.jsx',"    {selected ? <DetailPage item={selected} twins={twins} loading={detailLoading} onBack={()=>setSelected(null)} onOpen={openDetail} onOpenBrand={openBrand}/> : selectedBrand ? <BrandProfile brand={selectedBrand} items={items} onBack={()=>setSelectedBrand(null)} onOpen={openDetail}/> : tab==='admin' ? <AdminCenter brands={brands} items={items} twins={twins} notes={notes} reload={load} flash={flash}/> :\n","    {selected ? <DetailPage item={selected} twins={twins} loading={detailLoading} onBack={()=>setSelected(null)} onOpen={openDetail} onOpenBrand={openBrand} onOpenPerfumer={openPerfumer}/> : selectedBrand ? <BrandProfile brand={selectedBrand} items={items} onBack={()=>setSelectedBrand(null)} onOpen={openDetail}/> : selectedPerfumer ? <PerfumerProfile perfumer={selectedPerfumer} items={items} onBack={()=>setSelectedPerfumer(null)} onOpen={openDetail}/> : tab==='admin' ? <AdminCenter brands={brands} items={items} twins={twins} notes={notes} perfumers={perfumers} reload={load} flash={flash}/> :\n")
replace_once('frontend/src/main.jsx','function AdminCenter({brands,items,twins,notes,reload,flash}) {\n','function AdminCenter({brands,items,twins,notes,perfumers,reload,flash}) {\n')
replace_once('frontend/src/main.jsx',"      <button className={section==='sources'?'active':''} onClick={()=>{setSection('sources');setEditing(null)}}>Quellen & Prüfung</button>\n","      <button className={section==='sources'?'active':''} onClick={()=>{setSection('sources');setEditing(null)}}>Quellen & Prüfung</button>\n      <button className={section==='perfumers'?'active':''} onClick={()=>{setSection('perfumers');setEditing(null)}}>Parfümeure <b>{perfumers.length}</b></button>\n")
replace_once('frontend/src/main.jsx',"    {section==='sources'&&<VerificationAdmin api={api} flash={flash} brands={brands} items={items} twins={twins}/>}\n","    {section==='sources'&&<VerificationAdmin api={api} flash={flash} brands={brands} items={items} twins={twins}/>}\n    {section==='perfumers'&&<PerfumerAdmin api={api} flash={flash} perfumers={perfumers} reload={reload}/>}\n")
replace_once('frontend/src/main.jsx','function DetailPage({item,twins,loading,onBack,onOpen,onOpenBrand}) {\n','function DetailPage({item,twins,loading,onBack,onOpen,onOpenBrand,onOpenPerfumer}) {\n')
replace_once('frontend/src/main.jsx',"          <span><UserRound size={15}/>{item.perfumer||'Parfümeur offen'}</span>\n","          {item.perfumer?<button className=\"detail-perfumer-link\" onClick={()=>onOpenPerfumer(item.perfumer)}><UserRound size={15}/>{item.perfumer}</button>:<span><UserRound size={15}/>Parfümeur offen</span>}\n")

for doc,content in {
'docs/PROJECT_CONTEXT.md':'\n## Aktueller Stand: Parfümeurprofile 1.0\n\nDie vorhandene Tabelle `master_perfumers` ist jetzt vollständig über die App nutzbar. Profile enthalten Biografie, Nationalität, Geburtsjahr, Stil, bekannte Werke, Primärquelle, redaktionelle Notiz und Artikelstatus. Duftdetailseiten verlinken direkt auf passende Profile. Schema-Version ist `0010`.\n',
'docs/ROADMAP.md':'\n## Fortschritt: Parfümeurprofile 1.0\n\n**Status: umgesetzt**\n\n- eigene Parfümeurprofile\n- Biografie, Herkunft und Geburtsjahr\n- Stil und bekannte Werke\n- Primärquelle und Artikelstatus\n- Werkverzeichnis aus zugeordneten Düften\n- direkte Navigation aus Duftprofilen\n\n**Nächstes größeres Paket:** Datenqualität & redaktionelle Arbeitsliste 1.0.\n',
'docs/DEV_WORKFLOW.md':'\n## Parfümeurprofile testen\n\n- Profil anlegen, bearbeiten und löschen\n- Löschschutz bei zugeordneten Düften prüfen\n- Namenszuordnung zwischen Duft und Profil prüfen\n- Navigation Duftdetail → Parfümeurprofil → Duft prüfen\n- Primärquellen nur sicher extern öffnen\n- Frontend-Build und Backend-Compile ausführen\n'
}.items():
    p=Path(doc);p.write_text(p.read_text(encoding='utf-8')+content,encoding='utf-8')
