---
description: Grafiken und Dashboard-Screenshots für einen Meilenstein in die kommentierte Fotostrecke aufnehmen
argument-hint: "<Meilenstein, z. B. «nach Review» oder «OOS-Test»>"
---
Meilenstein: $ARGUMENTS

1. Aktuelle Grafiken (`results/*.png`, `results/optimization/*_heatmap.png`) nach `docs/fotostrecke/<JJJJ-MM-TT>_<name>.png` kopieren (Datum des Resultats). Bilder, die unverändert schon in der Fotostrecke sind, nicht doppelt aufnehmen.
2. Falls möglich Screenshots der Dashboard-Seiten: `uv run streamlit run dashboard/app.py --server.headless true --server.port 8599` im Hintergrund starten, dann mit Playwright (Chromium, z. B. `uv run --with playwright python …`, beim ersten Mal `playwright install chromium`) jede Seite aufnehmen und Streamlit wieder beenden. Geht das nicht, im Eintrag vermerken und ohne Screenshots weitermachen.
3. Jedes Bild ansehen und in `docs/fotostrecke.md` unter «<Datum> · Phase: <Meilenstein>» eintragen: Bilddatei, 2–3 Sätze (was ist zu sehen, welcher Entscheid / welche Erkenntnis). Nur beschreiben, was auf dem Bild wirklich zu sehen ist.
4. Keine OOS-Resultate zeigen, solange das Team den OOS-Test nicht freigegeben hat.
