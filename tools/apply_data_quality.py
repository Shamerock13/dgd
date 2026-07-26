from pathlib import Path


def replace_once(path, old, new):
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Missing block in {path}: {old[:120]}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "backend/app/main.py",
    "from .perfumer_routes import router as perfumer_router\n",
    "from .perfumer_routes import router as perfumer_router\nfrom .quality_routes import router as quality_router\n",
)
replace_once(
    "backend/app/main.py",
    "app.include_router(perfumer_router)\n",
    "app.include_router(perfumer_router)\napp.include_router(quality_router)\n",
)

replace_once(
    "frontend/src/main.jsx",
    "import {PerfumerAdmin, PerfumerProfile} from './perfumer.jsx';\n",
    "import {PerfumerAdmin, PerfumerProfile} from './perfumer.jsx';\nimport QualityWorklist from './quality.jsx';\n",
)
replace_once(
    "frontend/src/main.jsx",
    "      <button className={section==='perfumers'?'active':''} onClick={()=>{setSection('perfumers');setEditing(null)}}>Parfümeure <b>{perfumers.length}</b></button>\n      <button className={section==='updates'?'active':''}",
    "      <button className={section==='perfumers'?'active':''} onClick={()=>{setSection('perfumers');setEditing(null)}}>Parfümeure <b>{perfumers.length}</b></button>\n      <button className={section==='quality'?'active':''} onClick={()=>{setSection('quality');setEditing(null)}}>Arbeitsliste</button>\n      <button className={section==='updates'?'active':''}",
)
replace_once(
    "frontend/src/main.jsx",
    "    {section==='perfumers'&&<PerfumerAdmin api={api} flash={flash} perfumers={perfumers} reload={reload}/>}\n    {section==='updates'&&<UpdateCenter flash={flash}/>}\n",
    "    {section==='perfumers'&&<PerfumerAdmin api={api} flash={flash} perfumers={perfumers} reload={reload}/>}\n    {section==='quality'&&<QualityWorklist api={api} flash={flash} onOpenSection={value=>{setSection(value);setEditing(null)}}/>}\n    {section==='updates'&&<UpdateCenter flash={flash}/>}\n",
)

with Path("docs/PROJECT_CONTEXT.md").open("a", encoding="utf-8") as file:
    file.write("""

## Aktueller Stand: Datenqualität & redaktionelle Arbeitsliste 1.0

Der Admin-Bereich besitzt nun eine dynamische Arbeitsliste unter `/api/quality/worklist`. Sie prüft Marken, Düfte, Duftzwillinge, Quellen und Parfümeure auf fehlende oder ungeprüfte Angaben. Aufgaben werden nach Priorität sortiert und führen direkt in den passenden Verwaltungsbereich. Der Qualitätswert ist ein redaktioneller Fortschrittsindikator und kein wissenschaftlicher Datenwert. Das Datenbankschema bleibt bei `0010`, da die Arbeitsliste aus den vorhandenen Tabellen berechnet wird.
""")

with Path("docs/ROADMAP.md").open("a", encoding="utf-8") as file:
    file.write("""

## Fortschritt: Datenqualität & redaktionelle Arbeitsliste 1.0

**Status: umgesetzt**

- dynamische Qualitätsprüfung ohne zusätzliche Datenduplikate
- priorisierte Aufgabenliste für Marken, Düfte, Bilder und Quellen
- Prüfung fehlender Duftpyramiden und Parfümeurprofile
- Prüfung unvollständiger oder unbelegter Duftzwillinge
- Suche sowie Filter nach Priorität und Kategorie
- direkter Sprung in den passenden Admin-Bereich
- redaktioneller Qualitätswert und Aufgabenkennzahlen

**Nächstes größeres Paket:** Lokaler Bildupload & Medienablage 1.0.
""")

with Path("docs/DEV_WORKFLOW.md").open("a", encoding="utf-8") as file:
    file.write("""

## Datenqualität und Arbeitsliste testen

- `/api/quality/worklist` liefert Summary, Kategorien und Aufgaben
- fehlendes Bild, fehlende Quelle und fehlende Duftpyramide werden erkannt
- exakt vorhandene Parfümeurprofile werden nicht fälschlich beanstandet
- Prioritäts-, Kategorie- und Textfilter funktionieren gemeinsam
- Schaltfläche `Bearbeiten` öffnet den passenden Admin-Bereich
- erneute Prüfung aktualisiert die Arbeitsliste nach Änderungen
- Qualitätswert ausdrücklich nur als redaktionellen Fortschrittsindikator behandeln
""")
