---
description: Session abschliessen – Prompt-Log, Prompt-Sammlung, Journal-Entwurf, Deklaration, Status, Commit + Push
argument-hint: "[optionale Notizen zur Session]"
---
Schliesse die aktuelle Session gemäss CLAUDE.md («BMA-Dokumentation») ab. Zusätzliche Notizen des Teams: $ARGUMENTS

Ermittle zuerst `git config user.name` (= Spalte «wer»; ist es kein Klarname, schreibe `[bitte ergänzen]`) sowie `git log` und `git diff --stat` seit dem letzten «docs: Session-Doku»-Commit.

1. **docs/prompt_log.md:** neuer Eintrag im bestehenden Format (Datum, Prompt-Zusammenfassung, Iterationen ehrlich gezählt, geänderte/neue Dateien, offene Punkte).
2. **docs/prompt_sammlung.csv:** pro Team-Prompt dieser Session eine Zeile (nächste `nr`, Datum ISO, Tool/Modell, wer, Zweck, Wortlaut bzw. Verweis auf `docs/prompts/`, Ergebnis, übernommen, Iterationen). Lange Prompts im Wortlaut unter `docs/prompts/` ablegen.
3. **docs/arbeitsjournal.csv:** Entwurf EINER Zeile (datum, wer, was_warum_wie, woher_quellen_ki_dritte inkl. KI-Tool und Modell, miss_erfolge, lehren_massnahmen), Ich-/Wir-Form, sachlich, wie von Lernenden geschrieben. **Dem User zeigen und auf Bestätigung oder Korrektur warten**, erst dann eintragen.
4. **docs/deklaration_entwurf.md:** betroffene Aktivitäten 7–20 bzw. Aussagen 1–6 mit Beleg (Prompt-Nr.) nachführen.
5. **docs/status.md:** gegen `docs/vorgaben/bma_vorgaben.md` aktualisieren (Stand-Datum, ✅/🟡/❌, nächste 3 Termine).
6. Neue Fehler im KI-Code? → `docs/ki_fehlerlog.csv`. Danach `uv run pytest`, dann commit «docs: Session-Doku <Datum> – <Thema>» und `git push origin main`.
