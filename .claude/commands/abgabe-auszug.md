---
description: Journal-Auszug seit dem letzten Termin für einen Abgabetermin als Excel exportieren
argument-hint: "<Termin, z. B. 28.10.>"
---
Termin: $ARGUMENTS

1. Den Termin in der Tabelle «Termine» in `docs/vorgaben/bma_vorgaben.md` suchen (Jahr ergänzen). Beginn des Auszugs = Tag nach dem vorherigen Termin dort; gibt es keinen, ab dem ersten Journaleintrag.
2. Prüfen, ob `docs/arbeitsjournal.csv` für diesen Zeitraum vollständig ist (Sessions laut `git log` und `docs/prompt_log.md` ohne Journalzeile?). Lücken dem User melden, nicht selbst füllen.
3. Export: `uv run python scripts/export_prozessunterlagen.py --von <JJJJ-MM-TT> --bis <JJJJ-MM-TT>` (schreibt nach `results/prozess/`).
4. Pfad der Datei, Anzahl Journalzeilen und alle Stellen mit `[bitte ergänzen]` im Auszug ausgeben.
