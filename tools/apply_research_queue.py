from pathlib import Path


def replace(path, old, new):
    p=Path(path); text=p.read_text();
    if old not in text: raise RuntimeError(f'pattern missing in {path}: {old[:80]}')
    p.write_text(text.replace(old,new,1))

replace('backend/app/main.py',
"from .media_routes import router as media_router, MEDIA_ROOT, ensure_media_dirs\n",
"from .media_routes import router as media_router, MEDIA_ROOT, ensure_media_dirs\nfrom .research_routes import router as research_router\n")
replace('backend/app/main.py',
"app.include_router(media_router)\nensure_media_dirs()",
"app.include_router(media_router)\napp.include_router(research_router)\nensure_media_dirs()")

p=Path('backend/app/migrations.py'); text=p.read_text(); marker='\n)\n\n\ndef _ensure_migration_table'
block='''\n    Migration(\n        version="0011",\n        description="Recherche- und Import-Warteschlange anlegen",\n        statements=(\n            """CREATE TABLE IF NOT EXISTS research_candidates (\n                id UUID PRIMARY KEY, fingerprint VARCHAR(1000) NOT NULL UNIQUE,\n                source_name VARCHAR(300), source_url TEXT NOT NULL,\n                brand_name VARCHAR(160) NOT NULL, fragrance_name VARCHAR(200) NOT NULL,\n                year INTEGER, concentration VARCHAR(80), description TEXT, image_url TEXT,\n                status VARCHAR(30) NOT NULL DEFAULT 'PENDING', confidence FLOAT NOT NULL DEFAULT 0,\n                duplicate_fragrance_id UUID REFERENCES fragrances(id) ON DELETE SET NULL,\n                approved_fragrance_id UUID REFERENCES fragrances(id) ON DELETE SET NULL,\n                raw_data JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP\n            )""",\n            "CREATE INDEX IF NOT EXISTS ix_research_candidates_status ON research_candidates(status)",\n            "CREATE INDEX IF NOT EXISTS ix_research_candidates_created_at ON research_candidates(created_at DESC)",\n        ),\n    ),\n'''
if marker not in text: raise RuntimeError('migration marker missing')
p.write_text(text.replace(marker,block+marker,1))

replace('frontend/src/main.jsx',
"import MediaUpload from './media-upload.jsx';\n",
"import MediaUpload from './media-upload.jsx';\nimport ResearchQueue from './research.jsx';\n")
replace('frontend/src/main.jsx',
"      <button className={section==='quality'?'active':''} onClick={()=>{setSection('quality');setEditing(null)}}>Arbeitsliste</button>\n",
"      <button className={section==='quality'?'active':''} onClick={()=>{setSection('quality');setEditing(null)}}>Arbeitsliste</button>\n      <button className={section==='research'?'active':''} onClick={()=>{setSection('research');setEditing(null)}}>Recherche</button>\n")
replace('frontend/src/main.jsx',
"    {section==='quality'&&<QualityWorklist api={api} flash={flash} onOpenSection={value=>{setSection(value);setEditing(null)}}/>}\n",
"    {section==='quality'&&<QualityWorklist api={api} flash={flash} onOpenSection={value=>{setSection(value);setEditing(null)}}/>}\n    {section==='research'&&<ResearchQueue api={api} flash={flash} reload={reload}/>}\n")

Path('docs/PROJECT_CONTEXT.md').write_text(Path('docs/PROJECT_CONTEXT.md').read_text()+'''\n\n## Aktueller Stand: Automatische Recherche & Import-Warteschlange 1.0\n\nDer Admin-Bereich besitzt nun eine kontrollierte Recherche-Warteschlange. Öffentliche HTTP-/HTTPS-Seiten können manuell gescannt werden; JSON-LD-Produktdaten und Seitentitel werden als Vorschläge erfasst. Jeder Treffer enthält Quelle, Konfidenz und Dublettenhinweis. Erst eine ausdrückliche Freigabe legt Marke und Duft an. Private und interne Netzwerkziele sind aus Sicherheitsgründen gesperrt. Schema-Version ist `0011`.\n''')
Path('docs/ROADMAP.md').write_text(Path('docs/ROADMAP.md').read_text()+'''\n\n## Fortschritt: Automatische Recherche & Import-Warteschlange 1.0\n\n**Status: umgesetzt**\n\n- manuelles Scannen öffentlicher Quellseiten\n- Erkennung strukturierter JSON-LD-Produktdaten\n- Import-Warteschlange mit Bearbeitung und Statusfiltern\n- Dublettenprüfung gegen Marke und Duftname\n- Freigabe oder Ablehnung vor Datenbankübernahme\n- Quellenlink, Trefferqualität und Rohdaten bleiben nachvollziehbar\n- SSRF-Schutz gegen interne Netzwerkziele\n\n**Nächstes größeres Paket:** Recherchequellen & zeitgesteuerter Scanner 1.0.\n''')
Path('docs/DEV_WORKFLOW.md').write_text(Path('docs/DEV_WORKFLOW.md').read_text()+'''\n\n## Recherche-Warteschlange testen\n\n- öffentliche HTML-Seite mit JSON-LD-Produktdaten scannen\n- Seite ohne JSON-LD über Titel-Fallback prüfen\n- private, lokale und Link-Local-Adressen müssen abgelehnt werden\n- identische Quelle und identischer Treffer dürfen nicht doppelt angelegt werden\n- bekannte Marke/Duft-Kombination muss als Dublette markiert werden\n- Bearbeiten, Freigeben und Ablehnen prüfen\n- nach Freigabe muss der neue Duft in der normalen Duftliste erscheinen\n- Frontend-Build und Backend-Compile ausführen\n''')
