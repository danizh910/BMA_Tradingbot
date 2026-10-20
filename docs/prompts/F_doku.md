# Metaprompt F – BMA-Dokumentation im Repo verankern (Claude Code)

**Vorbereitung (vor dem Ausführen):**
1. `bma_vorgaben.md` nach `docs/vorgaben/bma_vorgaben.md` kopieren.
2. `Arbeitsjournal_BMA_Tradingbot.xlsx` (aus Cowork) nach `docs/import/` kopieren.
3. `BMA_Metaprompts_Umsetzung.md` (aus dem Cowork-Projekt) nach `docs/import/` kopieren.
4. Jede Person setzt lokal ihren eigenen Git-Namen: `git config user.name "Vorname Nachname"`. So ist für die Deklaration nachvollziehbar, wer was gemacht hat.

**Keine Original-PDFs der Schule ins Repo legen** (das Repo ist öffentlich), nur unsere Zusammenfassung.

---

```
Lies CLAUDE.md, docs/vorgaben/bma_vorgaben.md, docs/prompt_log.md, docs/ki_fehlerlog.csv und docs/entscheidungen.md. In diesem Schritt änderst du KEINEN Code in src/, scripts/run_*.py oder tests/ und keine Resultate. Es geht nur darum, die BMA-Dokumentation dauerhaft im Repo zu verankern, damit sie in jeder Session automatisch mitläuft.

## 1. Neue Dokumente in docs/
- docs/arbeitsjournal.csv – Hauptversion des Arbeitsjournals. Spalten exakt wie die Schulvorlage: datum, wer, was_warum_wie, woher_quellen_ki_dritte, miss_erfolge, lehren_massnahmen. Übernimm alle Einträge aus docs/import/Arbeitsjournal_BMA_Tradingbot.xlsx (Blatt «Arbeitsjournal»), Text unverändert. Ergänze danach Einträge für die Arbeit im Repo vom 30.09. und 19.10. auf Basis von docs/prompt_log.md und git log (in Ich-/Wir-Form, sachlich, wie von Lernenden geschrieben, KI-Hilfe in der Spalte woher offen nennen). Spalte «wer» mit [bitte ergänzen] markieren, wenn es nicht aus git log hervorgeht.
- docs/prompt_sammlung.csv – Spalten: nr, datum, tool_modell, wer, zweck, prompt_wortlaut_oder_verweis, ergebnis_verwendung, uebernommen, iterationen. Übernimm das Blatt «Prompt-Log» aus der xlsx. Ergänze die bisherigen Claude-Code-Prompts aus docs/prompt_log.md.
- docs/prompts/ – die Metaprompts A–E im Wortlaut aus docs/import/BMA_Metaprompts_Umsetzung.md, je eine Datei (A_init.md, B_umsetzung.md, C_naiv.md, D_audit.md, E_oos.md). Unverändert, nur kopiert.
- docs/quellen.md – zentrale Quellensammlung (Vorgabe Wegleitung 2.3). Tabelle: id, APA-7-Angabe, DOI/URL, typ (Studie/Buch/Doku/Web), geprueft (ja/nein/unsicher), pruefung_4_schritte (Kurznotiz), autor_vertrauen (warum glaubwürdig), kurzinhalt (1 Satz), verwendet_fuer (Kapitel/These-Teil), gelesen_von. Trage die Quellen aus docs/entscheidungen.md und docs/review_checkliste.md ein. Quellen aus den Deep-Research-Berichten NICHT selbst erfinden oder ergänzen; markiere nur bekannte Angaben, alles andere bleibt leer.
- docs/fotostrecke.md – kommentierte Fotostrecke der Produkterstellung (Vorgabe Kreation). Pro Eintrag: Datum, Phase, Bilddatei (docs/fotostrecke/…png), 2–3 Sätze Kommentar (was ist zu sehen, welcher Entscheid/welche Erkenntnis). Lege die ersten Einträge mit den bestehenden PNGs aus results/ an (in docs/fotostrecke/ kopieren, Datum im Dateinamen).
- docs/deklaration_entwurf.md – laufender Entwurf nach Struktur der Schul-Deklaration: Tabelle Aktivität 7–20 (Quellen-/Literatursuche, Thema/Fragestellung, Ausformulierung Fragestellung/Methodik, messbare Kriterien, Inhaltsverzeichnis, Literatur auswerten, Interviews formulieren/transkribieren, Grafiken, Datenanalyse, sprachliche Korrektur, Beurteilung im Fazit, Schlussfolgerungen) mit Spalten KI-Tool und Drittperson. Fülle aus, was aus Prompt-Log und Journal belegbar ist (z. B. Claude in Cowork für Fragestellung/Thesen, Claude Code für Programmierung und Datenanalyse, Deep-Research-Tool für Literatursuche). Unklares mit [bitte ergänzen] markieren.
- docs/status.md – Abgleich mit docs/vorgaben/bma_vorgaben.md: jede Checkliste (Konzept, Rollen, Projektwoche, Dokumentation, Schlussabgabe) mit ✅/🟡/❌ und einer Zeile Begründung, dazu die nächsten 3 Termine.

## 2. CLAUDE.md ergänzen (bestehende Regeln NICHT ändern), neuer Abschnitt «BMA-Dokumentation (Pflicht in jeder Session)»
- Am Ende jeder Session /session-ende ausführen bzw. dessen Schritte erledigen.
- Prompts des Teams im prompt_log und in der prompt_sammlung im Wortlaut festhalten (lange Prompts: Verweis auf docs/prompts/). Iterationen ehrlich zählen.
- Jeder gefundene Fehler im KI-Code → docs/ki_fehlerlog.csv (auch kleine, auch selbst gefundene; gefunden_durch korrekt setzen).
- Neue Quellen nur in docs/quellen.md eintragen; nie Quellen, DOIs oder Seitenzahlen erfinden. Unbelegtes als «ungeprüft» markieren.
- Texte für die Schriftliche Dokumentation: wissenschaftlich, 3. Person, keine «wir»-Form, Gendern ohne Stern/Doppelpunkt. Journal und Einzelreflexion dürfen Ich/Wir-Form haben.
- Wer etwas gemacht hat, steht in «wer» (aus git config user.name). Nicht raten, sondern [bitte ergänzen].
- Keine Schuldokumente (PDF) und keine personenbezogenen Daten ausser Namen der Teammitglieder committen.
- Wichtige Termine aus docs/vorgaben/bma_vorgaben.md kennen und bei /status darauf hinweisen.

## 3. Projekt-Befehle für Claude Code unter .claude/commands/ (je eine .md-Datei, Beschreibung im Frontmatter, Argumente über $ARGUMENTS)
- session-ende.md: (1) Eintrag in docs/prompt_log.md, (2) neue Zeile in docs/prompt_sammlung.csv, (3) Entwurf einer Zeile in docs/arbeitsjournal.csv (Was/Warum/Wie, Woher inkl. KI, Erfolge/Misserfolge, Lehren) und dem User zur Bestätigung zeigen, (4) docs/deklaration_entwurf.md aktualisieren, (5) docs/status.md aktualisieren, (6) commit «docs: Session-Doku …» und push.
- fehler.md: Fehler aus $ARGUMENTS ins Fehlerlog: Kennzahlen VORHER (run_insample.py) festhalten, Fehler beheben, Tests, Kennzahlen NACHHER, Eintrag vervollständigen, commit «fix(review): …», push. Tag v0.1-ki-unreviewed nie anfassen.
- quelle.md: Quelle aus $ARGUMENTS (DOI, URL oder Angabe) prüfen: Existiert sie (DOI auflösen bzw. Seite öffnen), stimmen Titel, Autoren, Jahr? Dann APA-7-Eintrag in docs/quellen.md mit Prüfstatus. Wenn nicht verifizierbar: Status «unsicher», nichts ergänzen.
- fotostrecke.md: Für den Meilenstein $ARGUMENTS die aktuellen Grafiken (results/*.png, Heatmaps) und, falls möglich, Screenshots der Dashboard-Seiten (Streamlit headless + Playwright mit Chromium) nach docs/fotostrecke/ kopieren und in docs/fotostrecke.md kommentieren.
- status.md: docs/status.md gegen docs/vorgaben/bma_vorgaben.md neu prüfen und eine kurze Liste «Was fehlt bis zum nächsten Termin» ausgeben.
- abgabe-auszug.md: Für den Termin $ARGUMENTS (z. B. 28.10.) einen Auszug des Arbeitsjournals seit dem letzten Termin erstellen und mit scripts/export_prozessunterlagen.py als Excel exportieren.
- audit.md: Prompt D aus docs/prompts/D_audit.md ausführen (Befunde auflisten, KEINEN Code ändern, Befunde ins Fehlerlog mit gefunden_durch = ki_audit).

## 4. scripts/export_prozessunterlagen.py
Exportiert docs/arbeitsjournal.csv (optional gefiltert nach Datum von/bis) und docs/prompt_sammlung.csv in eine Excel-Datei im Format der Schulvorlage (Spalten WANN?/WER?/WAS WARUM WIE? (EIGENLEISTUNG)/WOHER?/(MISS-)ERFOLGE/LEHREN/MASSNAHMEN, Zeilenumbruch, Datumsformat TT.MM.JJJJ, Querformat) nach results/prozess/. Mit Test.

## 5. Abschluss
- Prüfe, dass `uv run pytest` grün bleibt.
- Eintrag in docs/prompt_log.md (dieser Prompt = Metaprompt F, Wortlaut in docs/prompts/F_doku.md ablegen).
- Commit «docs: BMA-Dokumentation verankern (Journal, Prompt-Sammlung, Quellen, Fotostrecke, Deklaration, Befehle)» und push.
- Gib mir aus: Liste der neuen Befehle mit einem Satz Erklärung, Inhalt von docs/status.md, alle Stellen mit [bitte ergänzen].
```
