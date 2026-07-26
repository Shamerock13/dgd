from pathlib import Path


def replace_once(path, old, new):
    text = Path(path).read_text(encoding='utf-8')
    if old not in text:
        raise RuntimeError(f'Missing block in {path}: {old[:120]}')
    Path(path).write_text(text.replace(old, new, 1), encoding='utf-8')


# Backend router registration
replace_once('backend/app/main.py',
'''from .update_service import updater_request\n''',
'''from .update_service import updater_request\nfrom .source_routes import router as source_router\n''')
replace_once('backend/app/main.py',
'''app = FastAPI(title="DGD API", version="1.2.0", lifespan=lifespan)\n''',
'''app = FastAPI(title="DGD API", version="1.2.0", lifespan=lifespan)\napp.include_router(source_router)\n''')

# Migration 0009 for source status normalization and indexes
replace_once('backend/app/migrations.py',
'''    Migration(\n        version="0008",\n        description="Markenprofile um Gründungsjahr, Website und Verifizierungsstatus ergänzen",\n        statements=(\n            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS founded_year INTEGER",\n            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS website_url TEXT",\n            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS verification_status VARCHAR(40)",\n            "UPDATE brands SET verification_status = 'OPEN' WHERE verification_status IS NULL OR btrim(verification_status) = ''",\n            "ALTER TABLE brands ALTER COLUMN verification_status SET DEFAULT 'OPEN'",\n            "ALTER TABLE brands ALTER COLUMN verification_status SET NOT NULL",\n            "CREATE INDEX IF NOT EXISTS ix_brands_verification_status ON brands (verification_status)",\n        ),\n    ),\n\n)\n''',
'''    Migration(\n        version="0008",\n        description="Markenprofile um Gründungsjahr, Website und Verifizierungsstatus ergänzen",\n        statements=(\n            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS founded_year INTEGER",\n            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS website_url TEXT",\n            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS verification_status VARCHAR(40)",\n            "UPDATE brands SET verification_status = 'OPEN' WHERE verification_status IS NULL OR btrim(verification_status) = ''",\n            "ALTER TABLE brands ALTER COLUMN verification_status SET DEFAULT 'OPEN'",\n            "ALTER TABLE brands ALTER COLUMN verification_status SET NOT NULL",\n            "CREATE INDEX IF NOT EXISTS ix_brands_verification_status ON brands (verification_status)",\n        ),\n    ),\n    Migration(\n        version="0009",\n        description="Quellenregister und Verifizierungsstatus für die App absichern",\n        statements=(\n            "UPDATE master_sources SET trust_status = 'OPEN' WHERE trust_status IS NULL OR btrim(trust_status) = ''",\n            "UPDATE master_sources SET usage_status = 'OPEN' WHERE usage_status IS NULL OR btrim(usage_status) = ''",\n            "ALTER TABLE master_sources ALTER COLUMN trust_status SET DEFAULT 'OPEN'",\n            "ALTER TABLE master_sources ALTER COLUMN usage_status SET DEFAULT 'OPEN'",\n            "CREATE INDEX IF NOT EXISTS ix_master_sources_object ON master_sources (object_type, object_id)",\n            "CREATE INDEX IF NOT EXISTS ix_master_sources_trust_status ON master_sources (trust_status)",\n            "CREATE INDEX IF NOT EXISTS ix_master_sources_usage_status ON master_sources (usage_status)",\n        ),\n    ),\n\n)\n''')

# Frontend integration
replace_once('frontend/src/main.jsx',
'''import './brand.css';\n''',
'''import './brand.css';\nimport VerificationAdmin from './verification.jsx';\n''')
replace_once('frontend/src/main.jsx',
'''      <button className={section==='twins'?'active':''} onClick={()=>{setSection('twins');setEditing(null)}}>Duftzwillinge <b>{twins.length}</b></button>\n      <button className={section==='updates'?'active':''} onClick={()=>{setSection('updates');setEditing(null)}}>System & Updates</button>\n''',
'''      <button className={section==='twins'?'active':''} onClick={()=>{setSection('twins');setEditing(null)}}>Duftzwillinge <b>{twins.length}</b></button>\n      <button className={section==='sources'?'active':''} onClick={()=>{setSection('sources');setEditing(null)}}>Quellen & Prüfung</button>\n      <button className={section==='updates'?'active':''} onClick={()=>{setSection('updates');setEditing(null)}}>System & Updates</button>\n''')
replace_once('frontend/src/main.jsx',
'''    {section==='twins'&&<TwinAdmin items={items} twins={twins} reload={reload} flash={flash}/>}\n    {section==='updates'&&<UpdateCenter flash={flash}/>}\n''',
'''    {section==='twins'&&<TwinAdmin items={items} twins={twins} reload={reload} flash={flash}/>}\n    {section==='sources'&&<VerificationAdmin api={api} flash={flash} brands={brands} items={items} twins={twins}/>}\n    {section==='updates'&&<UpdateCenter flash={flash}/>}\n''')

# Documentation
for path, addition in {
'docs/PROJECT_CONTEXT.md': '''\n## Aktueller Stand: Quellen & Verifizierung 1.0\n\nDas bestehende `master_sources`-Register ist jetzt über die App nutzbar. Quellen können Marken, Düften, Duftzwillingen oder allgemeinen Themen zugeordnet werden. Vertrauensstatus (`OPEN`, `REVIEW`, `TRUSTED`, `REJECTED`) und Nutzungsstatus (`OPEN`, `ALLOWED`, `RESTRICTED`, `INTERNAL`) bilden den redaktionellen Prüfprozess ab. Schema-Version ist nun `0009`.\n''',
'docs/ROADMAP.md': '''\n## Fortschritt: Quellen & Verifizierung 1.0\n\n**Status: umgesetzt**\n\n- Quellenregister im Admin\n- Zuordnung zu Marken, Düften und Duftzwillingen\n- Vertrauens- und Nutzungsstatus\n- Prüfnotizen, Quellentyp, Datum sowie URL/Datei\n- Verifizierungsübersicht mit offenen Datensätzen\n\n**Nächstes größeres Paket:** Parfümeurprofile 1.0.\n''',
'docs/DEV_WORKFLOW.md': '''\n## Quellen und Verifizierung testen\n\n- Quelle anlegen, bearbeiten und löschen\n- Zuordnung zu Marke, Duft und Duftzwilling prüfen\n- Vertrauensfilter im Quellenregister prüfen\n- externe Quellenlinks nur mit `target="_blank"` und `rel="noreferrer"` öffnen\n- Statuswerte außerhalb der definierten Enum-Werte müssen vom Backend abgelehnt werden\n- Prüfübersicht muss nach Änderungen neu geladen werden\n'''
}.items():
    with Path(path).open('a', encoding='utf-8') as handle:
        handle.write(addition)
