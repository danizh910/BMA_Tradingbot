---
description: KI-Audit des Codes nach Metaprompt D – nur Befunde, keinen Code ändern, Befunde ins Fehlerlog
argument-hint: "[optional: Fokus, z. B. Datei oder Thema]"
---
Fokus (optional): $ARGUMENTS

1. `docs/prompts/D_audit.md` lesen und Prompt D genau so ausführen. Enthält die Datei noch keinen Wortlaut (Platzhalter), abbrechen und den User bitten, ihn aus `BMA_Metaprompts_Umsetzung.md` einzufügen.
2. **Keinen Code ändern** (weder `src/`, `scripts/` noch `tests/`), keine Resultate neu erzeugen, keine OOS-Daten.
3. Befunde nummeriert auflisten: Datei:Zeile, Beschreibung, Kategorie, erwartete Auswirkung auf die Kennzahlen, Sicherheit (sicher/wahrscheinlich/unklar).
4. Jeden Befund als Zeile in `docs/ki_fehlerlog.csv` eintragen mit `gefunden_durch = ki_audit`; `behoben_in_commit` und Kennzahlen bleiben leer (Behebung später mit `/fehler`).
5. Eintrag in `docs/prompt_log.md` und `docs/prompt_sammlung.csv`, commit «docs: KI-Audit <Datum>», `git push origin main`.
