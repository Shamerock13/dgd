from pathlib import Path


def replace(path, old, new):
    p=Path(path); text=p.read_text();
    if old not in text: raise RuntimeError(f'pattern missing in {path}: {old[:80]}')
    p.write_text(text.replace(old,new,1))

replace('backend/app/main.py','from .quality_routes import router as quality_router\n','from .quality_routes import router as quality_router\nfrom .media_routes import router as media_router, MEDIA_ROOT, ensure_media_dirs\n')
replace('backend/app/main.py','app.include_router(quality_router)\n','app.include_router(quality_router)\napp.include_router(media_router)\nensure_media_dirs()\napp.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")\n')
replace('frontend/src/main.jsx',"import QualityWorklist from './quality.jsx';\n","import QualityWorklist from './quality.jsx';\nimport MediaUpload from './media-upload.jsx';\n")
replace('frontend/src/main.jsx','      <ImageAdminPreview item={{...form,brand:brands.find(b=>b.id===form.brand_id)||{name:\'DGD\'}}}/>\n','      <ImageAdminPreview item={{...form,brand:brands.find(b=>b.id===form.brand_id)||{name:\'DGD\'}}}/>\n      <MediaUpload item={editing?{...editing,...form}:null} flash={flash} onChanged={patch=>{setForm(current=>({...current,...patch}));if(editing)setEditing(current=>({...current,...patch}))}}/>\n')
replace('docker-compose.dev.yml','      AUTO_SEED: ${AUTO_SEED}\n','      AUTO_SEED: ${AUTO_SEED}\n      MEDIA_ROOT: /app/media\n      MAX_IMAGE_BYTES: 8388608\n')
replace('docker-compose.dev.yml','      - ./backend/app:/app/app\n','      - ./backend/app:/app/app\n      - /mnt/user/appdata/dgd-dev-media:/app/media\n')

for path, text in {
'docs/PROJECT_CONTEXT.md':'\n\n## Aktueller Stand: Lokaler Bildupload & Medienablage 1.0\n\nDuftbilder können nun als JPEG, PNG oder WebP bis 8 MB direkt im Admin hochgeladen werden. Die Dateien liegen persistent unter `/mnt/user/appdata/dgd-dev-media` und werden im Container über `/app/media` sowie öffentlich über `/media` bereitgestellt. Uploads erhalten kollisionsfreie Dateinamen, werden anhand von Dateisignatur und MIME-Typ geprüft und können ersetzt oder gelöscht werden. Externe Bild-URLs bleiben weiterhin möglich.\n',
'docs/ROADMAP.md':'\n\n## Fortschritt: Lokaler Bildupload & Medienablage 1.0\n\n**Status: umgesetzt**\n\n- persistenter Unraid-Medienordner\n- Upload für JPEG, PNG und WebP bis 8 MB\n- Prüfung von MIME-Typ und Dateisignatur\n- automatische kollisionsfreie Dateinamen\n- Ersetzen und Löschen lokaler Duftbilder\n- weiterhin Unterstützung externer Bild-URLs\n- dokumentierte Backup- und Speicherregeln\n\n**Nächstes größeres Paket:** Automatische Recherche & Import-Warteschlange 1.0.\n',
'docs/DEV_WORKFLOW.md':'\n\n## Lokale Medien testen und sichern\n\n- Upload mit JPEG, PNG und WebP testen\n- falsche Dateiendung beziehungsweise ungültige Signatur muss abgelehnt werden\n- Größenlimit von 8 MB prüfen\n- Ersetzen entfernt die vorherige lokale Datei\n- Löschen ist nur für lokale `/media/fragrances/...`-Dateien erlaubt\n- `/mnt/user/appdata/dgd-dev-media` muss in das Unraid-Backup aufgenommen werden\n- Datenbank und Medienordner immer gemeinsam sichern und wiederherstellen\n'
}.items():
    p=Path(path); p.write_text(p.read_text()+text)
