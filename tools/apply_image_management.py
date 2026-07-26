from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path}: {old[:180]}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


# Backend model fields
replace_once(
    "backend/app/models.py",
    "    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)\n    description: Mapped[str | None] = mapped_column(Text, nullable=True)",
    "    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)\n    image_source_name: Mapped[str | None] = mapped_column(String(200), nullable=True)\n    image_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)\n    image_usage_note: Mapped[str | None] = mapped_column(Text, nullable=True)\n    image_status: Mapped[str] = mapped_column(String(30), nullable=False, default=\"OPEN\", server_default=\"OPEN\")\n    description: Mapped[str | None] = mapped_column(Text, nullable=True)",
)

# API schemas
replace_once(
    "backend/app/schemas.py",
    "    image_url: str | None = None\n    description: str | None = None",
    "    image_url: str | None = None\n    image_source_name: str | None = Field(default=None, max_length=200)\n    image_source_url: str | None = None\n    image_usage_note: str | None = None\n    image_status: str = Field(default=\"OPEN\", pattern=\"^(OPEN|VERIFIED|BROKEN)$\")\n    description: str | None = None",
)
replace_once(
    "backend/app/schemas.py",
    "    image_url: str | None = None\n    description: str | None = None\n    top_notes: str | None = None",
    "    image_url: str | None = None\n    image_source_name: str | None = None\n    image_source_url: str | None = None\n    image_usage_note: str | None = None\n    image_status: str = \"OPEN\"\n    description: str | None = None\n    top_notes: str | None = None",
)

# Migration 0007
migration_path = Path("backend/app/migrations.py")
migrations = migration_path.read_text(encoding="utf-8")
needle = "    ),\n\n)\n\n\ndef _ensure_migration_table"
if needle not in migrations:
    raise RuntimeError("Migration insertion point not found")
block = '''    ),\n    Migration(\n        version="0007",\n        description="Bildquellen, Nutzungsstatus und robuste Bildverwaltung ergänzen",\n        statements=(\n            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS image_source_name VARCHAR(200)",\n            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS image_source_url TEXT",\n            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS image_usage_note TEXT",\n            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS image_status VARCHAR(30)",\n            "UPDATE fragrances SET image_status = 'OPEN' WHERE image_status IS NULL OR btrim(image_status) = ''",\n            "ALTER TABLE fragrances ALTER COLUMN image_status SET DEFAULT 'OPEN'",\n            "ALTER TABLE fragrances ALTER COLUMN image_status SET NOT NULL",\n            "CREATE INDEX IF NOT EXISTS ix_fragrances_image_status ON fragrances (image_status)",\n        ),\n    ),\n\n)\n\n\ndef _ensure_migration_table'''
migration_path.write_text(migrations.replace(needle, block, 1), encoding="utf-8")

# Standard importer aliases and validation
replace_once(
    "backend/app/import_service.py",
    "from pathlib import Path\nfrom typing import Any",
    "from pathlib import Path\nfrom typing import Any\nfrom urllib.parse import urlparse",
)
replace_once(
    "backend/app/import_service.py",
    '    "bild-url": "image_url",\n    "beschreibung": "description",',
    '    "bild-url": "image_url",\n    "bildquelle": "image_source_name",\n    "bildquelle name": "image_source_name",\n    "bildquelle url": "image_source_url",\n    "bild-quellen-url": "image_source_url",\n    "bild nutzungshinweis": "image_usage_note",\n    "bildrechte": "image_usage_note",\n    "bildstatus": "image_status",\n    "beschreibung": "description",',
)
replace_once(
    "backend/app/import_service.py",
    "def split_notes(value: Any) -> list[str]:",
    '''def normalize_image_status(value: Any) -> str:\n    folded = str(value or "OPEN").strip().casefold()\n    aliases = {\n        "open": "OPEN", "offen": "OPEN",\n        "verified": "VERIFIED", "geprüft": "VERIFIED", "geprueft": "VERIFIED",\n        "broken": "BROKEN", "fehlerhaft": "BROKEN", "defekt": "BROKEN",\n    }\n    return aliases.get(folded, "OPEN")\n\n\ndef valid_image_location(value: str | None) -> bool:\n    if not value:\n        return True\n    if value.startswith("/"):\n        return True\n    return urlparse(value).scheme in {"http", "https"}\n\n\ndef split_notes(value: Any) -> list[str]:''',
)
replace_once(
    "backend/app/import_service.py",
    '        "image_url": clean_text(row.get("image_url")),\n        "description": clean_text(row.get("description")),',
    '        "image_url": clean_text(row.get("image_url")),\n        "image_source_name": clean_text(row.get("image_source_name")),\n        "image_source_url": clean_text(row.get("image_source_url")),\n        "image_usage_note": clean_text(row.get("image_usage_note")),\n        "image_status": normalize_image_status(row.get("image_status")),\n        "description": clean_text(row.get("description")),',
)
replace_once(
    "backend/app/import_service.py",
    '    if parsed["year"] is not None and not 1700 <= parsed["year"] <= 2200:\n        errors.append("Jahr liegt außerhalb des gültigen Bereichs")\n\n    return parsed, errors',
    '    if parsed["year"] is not None and not 1700 <= parsed["year"] <= 2200:\n        errors.append("Jahr liegt außerhalb des gültigen Bereichs")\n    if not valid_image_location(parsed["image_url"]):\n        errors.append("Bild-URL muss mit http://, https:// oder / beginnen")\n    if not valid_image_location(parsed["image_source_url"]):\n        errors.append("Bildquellen-URL muss mit http://, https:// oder / beginnen")\n\n    return parsed, errors',
)
replace_once(
    "backend/app/import_service.py",
    '                    "image_url", "description", "accords", "longevity",\n                    "projection", "sweetness", "freshness",',
    '                    "image_url", "image_source_name", "image_source_url",\n                    "image_usage_note", "image_status", "description", "accords",\n                    "longevity", "projection", "sweetness", "freshness",',
)

# Master importer picks up image columns when present in future master files.
replace_once(
    "backend/app/master_import_service.py",
    '            "perfumer": perfumer_name,\n            "master_data": master_data,',
    '            "perfumer": perfumer_name,\n            "image_url": data.get("Bild-URL") or data.get("Bild URL"),\n            "image_source_name": data.get("Bildquelle") or data.get("Bildquelle Name"),\n            "image_source_url": data.get("Bildquelle URL"),\n            "image_usage_note": data.get("Bildrechte") or data.get("Bild Nutzungshinweis"),\n            "image_status": str(data.get("Bildstatus") or "OPEN").strip().upper(),\n            "master_data": master_data,',
)

# Frontend state and imports
replace_once(
    "frontend/src/main.jsx",
    "  BadgeEuro, Clock3, UserRound, Layers3, Info\n} from 'lucide-react';\nimport './styles.css';\nimport './detail.css';",
    "  BadgeEuro, Clock3, UserRound, Layers3, Info, ImageIcon, ExternalLink\n} from 'lucide-react';\nimport './styles.css';\nimport './detail.css';\nimport './image.css';",
)
replace_once(
    "frontend/src/main.jsx",
    "  price_eur:'', image_url:'', description:'', top_notes:'', heart_notes:'',\n  base_notes:'', accords:'', longevity:'', projection:'', sweetness:'', freshness:''",
    "  price_eur:'', image_url:'', image_source_name:'', image_source_url:'',\n  image_usage_note:'', image_status:'OPEN', description:'', top_notes:'', heart_notes:'',\n  base_notes:'', accords:'', longevity:'', projection:'', sweetness:'', freshness:''",
)
replace_once(
    "frontend/src/main.jsx",
    '        <Field label="Bild-URL"><input value={form.image_url||\'\'} onChange={e=>set(\'image_url\',e.target.value)}/></Field>\n      </div>\n      <Field label="Beschreibung">',
    '''        <Field label="Bild-URL"><input value={form.image_url||''} onChange={e=>set('image_url',e.target.value)} placeholder="https://… oder später /media/…"/></Field>\n        <Field label="Bildstatus"><select value={form.image_status||'OPEN'} onChange={e=>set('image_status',e.target.value)}><option value="OPEN">Offen</option><option value="VERIFIED">Geprüft</option><option value="BROKEN">Fehlerhaft</option></select></Field>\n        <Field label="Bildquelle"><input value={form.image_source_name||''} onChange={e=>set('image_source_name',e.target.value)} placeholder="Hersteller, Händler, eigenes Bild …"/></Field>\n        <Field label="Link zur Bildquelle"><input value={form.image_source_url||''} onChange={e=>set('image_source_url',e.target.value)} placeholder="https://…"/></Field>\n      </div>\n      <Field label="Nutzungs- / Rechtehinweis zum Bild"><textarea rows="2" value={form.image_usage_note||''} onChange={e=>set('image_usage_note',e.target.value)} placeholder="Interne Notiz zur Herkunft und erlaubten Nutzung"/></Field>\n      <ImageAdminPreview item={{...form,brand:brands.find(b=>b.id===form.brand_id)||{name:'DGD'}}}/>\n      <Field label="Beschreibung">''',
)
replace_once(
    "frontend/src/main.jsx",
    '      {item.image_url?<img src={item.image_url} alt={`${item.brand.name} ${item.name}`}/>:<span>{item.brand.name.slice(0,2).toUpperCase()}</span>}',
    '      <ManagedImage item={item} variant="card"/>',
)
replace_once(
    "frontend/src/main.jsx",
    "function ImageWithFallback({item,className=''}) {\n  const [broken,setBroken]=useState(false);\n  useEffect(()=>setBroken(false),[item.image_url]);\n  if(!item.image_url||broken)return <div className={`detail-image-fallback ${className}`}><span>{item.brand.name.slice(0,2).toUpperCase()}</span><small>Bild folgt</small></div>;\n  return <img className={className} src={item.image_url} alt={`${item.brand.name} ${item.name}`} onError={()=>setBroken(true)}/>;\n}",
    '''function ManagedImage({item,variant='detail',showStatus=false}) {\n  const [broken,setBroken]=useState(false);\n  useEffect(()=>setBroken(false),[item.image_url]);\n  const fallback=!item.image_url||broken;\n  const status=broken?'BROKEN':(item.image_status||'OPEN');\n  const label={OPEN:'Offen',VERIFIED:'Geprüft',BROKEN:'Fehlerhaft'}[status]||'Offen';\n  return <div className={`managed-image managed-image-${variant}`}>\n    {fallback?<div className="managed-image-fallback"><ImageIcon/><span>{item.brand.name.slice(0,2).toUpperCase()}</span><small>Bild folgt</small></div>:<img src={item.image_url} alt={`${item.brand.name} ${item.name}`} onError={()=>setBroken(true)}/>}\n    {showStatus&&<span className={`image-status image-status-${status.toLowerCase()}`}>{label}</span>}\n  </div>;\n}\n\nfunction ImageAdminPreview({item}) {\n  return <section className="image-admin-preview">\n    <ManagedImage item={item} variant="admin" showStatus/>\n    <div><small>Bildverwaltung 1.0</small><b>{item.image_source_name||'Bildquelle noch offen'}</b><span>{item.image_usage_note||'Noch kein Nutzungs- oder Rechtehinweis hinterlegt.'}</span>{item.image_source_url&&<a href={item.image_source_url} target="_blank" rel="noreferrer"><ExternalLink size={14}/> Quelle öffnen</a>}</div>\n  </section>;\n}''',
)
replace_once(
    "frontend/src/main.jsx",
    '<div className="detail-visual"><ImageWithFallback item={item}/><div className="detail-image-glow"/></div>',
    '<div className="detail-visual"><ManagedImage item={item} variant="detail" showStatus/><div className="detail-image-glow"/></div>',
)
replace_once(
    "frontend/src/main.jsx",
    '        <div className="detail-price-block"><small>Erfasster Preis</small><strong>{item.price_eur!=null?euro.format(item.price_eur):\'Preis offen\'}</strong><span>{item.gender||\'Unisex\'}</span></div>',
    '''        <div className="detail-price-block"><small>Erfasster Preis</small><strong>{item.price_eur!=null?euro.format(item.price_eur):'Preis offen'}</strong><span>{item.gender||'Unisex'}</span></div>\n        <div className="detail-image-source"><ImageIcon size={17}/><div><small>Bildquelle</small><b>{item.image_source_name||'Noch nicht dokumentiert'}</b>{item.image_usage_note&&<span>{item.image_usage_note}</span>}</div>{item.image_source_url&&<a href={item.image_source_url} target="_blank" rel="noreferrer" aria-label="Bildquelle öffnen"><ExternalLink size={16}/></a>}</div>''',
)

Path("frontend/src/image.css").write_text('''/* DGD 2.0 – Bildverwaltung und Bildquellen */\n.managed-image{position:relative;display:grid;place-items:center;width:100%;height:100%;overflow:hidden}.managed-image img{width:100%;height:100%;object-fit:contain}.managed-image-card{height:100%}.managed-image-card img{padding:18px}.managed-image-fallback{display:grid;place-items:center;align-content:center;gap:6px;width:100%;height:100%;color:var(--muted);background:radial-gradient(circle at 50% 35%,color-mix(in srgb,var(--gold) 15%,transparent),transparent 50%)}.managed-image-fallback svg{width:26px;height:26px;color:var(--gold)}.managed-image-fallback span{font-family:'Playfair Display';font-size:42px;color:var(--gold)}.managed-image-fallback small{text-transform:uppercase;letter-spacing:.1em;font-size:9px}.managed-image-detail img{width:88%;height:440px;position:relative;z-index:2}.managed-image-detail .managed-image-fallback{position:relative;z-index:2;width:190px;height:275px;border:1px solid color-mix(in srgb,var(--gold) 72%,var(--line));border-radius:58px 58px 22px 22px;background:color-mix(in srgb,var(--surface) 75%,transparent)}.image-status{position:absolute;right:12px;bottom:12px;padding:6px 9px;border-radius:999px;font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;background:var(--surface);border:1px solid var(--line);z-index:4}.image-status-verified{color:#3aa879}.image-status-broken{color:#d46767}.image-status-open{color:var(--gold)}.image-admin-preview{display:grid;grid-template-columns:150px 1fr;gap:18px;align-items:center;margin:18px 0 24px;padding:16px;border:1px solid var(--line);border-radius:18px;background:var(--surface2)}.managed-image-admin{height:150px;border-radius:14px;background:var(--surface);border:1px solid var(--line)}.image-admin-preview>div{display:grid;gap:5px}.image-admin-preview small{color:var(--gold);text-transform:uppercase;letter-spacing:.08em}.image-admin-preview span{color:var(--muted);font-size:12px;line-height:1.5}.image-admin-preview a,.detail-image-source a{display:inline-flex;align-items:center;gap:6px;color:var(--gold);font-size:12px;text-decoration:none}.detail-image-source{display:grid;grid-template-columns:auto 1fr auto;gap:11px;align-items:start;margin-top:18px;padding:14px;border:1px solid var(--line);border-radius:14px;background:var(--surface2);max-width:540px}.detail-image-source>svg{color:var(--gold)}.detail-image-source div{display:grid;gap:3px}.detail-image-source small{color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-size:9px}.detail-image-source span{color:var(--muted);font-size:11px;line-height:1.4}@media(max-width:650px){.image-admin-preview{grid-template-columns:1fr}.managed-image-admin{height:210px}.managed-image-detail img{height:290px}.managed-image-detail .managed-image-fallback{width:145px;height:215px}}\n''', encoding="utf-8")

# Project documentation
for path, section in {
    "docs/PROJECT_CONTEXT.md": '''\n\n## Aktueller Stand: Bildverwaltung & Bildquellen 1.0\n\nDie Bildverwaltung wird bewusst in zwei Stufen umgesetzt. Stufe 1 verwaltet externe oder künftig lokale Bildpfade samt Quelle, Nutzungsnotiz und Prüfstatus. Ein echter Upload folgt erst mit einem klaren Unraid-Speicher-, Backup- und Löschkonzept.\n\nUmgesetzt in diesem Paket:\n\n- Migration `0007` für Bildmetadaten\n- Bildquelle, Quellenlink und Nutzungs-/Rechtehinweis je Duft\n- Status `OPEN`, `VERIFIED` oder `BROKEN`\n- einheitlicher Bildbaustein für Karten, Admin und Detailseite\n- belastbarer Fallback bei leerer oder defekter Bild-URL\n- Import-Unterstützung für die neuen Bildfelder\n- Vorbereitung auf spätere lokale Pfade wie `/media/...`\n''',
    "docs/ROADMAP.md": '''\n\n## Fortschritt: Bildverwaltung & Bildquellen 1.0\n\n**Status: umgesetzt**\n\nEnthalten sind externe Bildpfade, Bildquelle, Quellenlink, Nutzungsnotiz, Prüfstatus, Admin-Vorschau und ein gemeinsamer Fallback-Baustein.\n\n### Nachgelagertes Paket: Lokaler Bildupload\n\n- dauerhaft gemountetes Unraid-Verzeichnis\n- erlaubte Dateitypen und Größenbegrenzung\n- sichere Dateinamen und Dublettenstrategie\n- Thumbnail-/Optimierungsstrategie\n- Backup- und Löschregeln\n- Migration bestehender externer Bilder nur nach bewusster Freigabe\n\n**Nächstes größeres Paket:** Markenprofile 1.0.\n''',
    "docs/DEV_WORKFLOW.md": '''\n\n## Bildänderungen testen\n\nBei Änderungen an Bildfeldern oder der Bilddarstellung zusätzlich prüfen:\n\n- leere Bild-URL zeigt den DGD-Fallback\n- nicht erreichbare Bild-URL fällt nach `onError` auf den Fallback zurück\n- Bildstatus und Quellenhinweise werden im Admin korrekt gespeichert\n- externe Links öffnen mit `target=\"_blank\"` und `rel=\"noreferrer\"`\n- relative Pfade wie `/media/...` bleiben für den späteren lokalen Upload zulässig\n- keine externen Bilder automatisch herunterladen oder in Produktion kopieren\n''',
}.items():
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    heading = section.strip().splitlines()[0]
    if heading not in text:
        file.write_text(text.rstrip() + section + "\n", encoding="utf-8")
