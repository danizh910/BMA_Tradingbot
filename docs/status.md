# Status gegenüber den BMA-Vorgaben

Stand: 2026-10-20 (Projektwoche). Abgleich mit `docs/vorgaben/bma_vorgaben.md`, neu prüfen mit `/status`.
✅ erledigt · 🟡 teilweise · ❌ offen. Geprüft wurde nur, was im Repo liegt. Was ausserhalb liegt (z. B. Konzept-Entwurf in Word), bitte nachtragen.

## Nächste Termine

| Datum | Abgabe / Anlass |
|---|---|
| **So 25.10.2026, 23:59** | **BMA-Konzept** (benotet, Teilnote Prozess) |
| Mi 28.10.2026 | 2. AAR (BMA-Woche) → Journal-Auszug mit `/abgabe-auszug 28.10.` |
| Mi 25.11.2026 | 3. AAR + Teil der BMA-Arbeit (wissenschaftliche Arbeitsweise) |

## Konzept (Abgabe 25.10.)

| | Punkt | Begründung |
|---|---|---|
| ❌ | Kompaktes Word/PDF mit Titelblatt und Inhaltsverzeichnis | Kein Konzeptdokument im Repo. |
| 🟡 | Quellen korrekt referenziert und bibliografiert | `docs/quellen.md` angelegt, 3 von 16 Quellen geprüft (Q1–Q3), Rest nur Kurzangabe. |
| ❌ | Motivation, Vorwissen, Fokus (½ Seite) | Nirgends festgehalten. |
| 🟡 | Fragestellung mit Kriterien/Messgrössen, Methoden für Produkt UND Dokumentation | Fragestellung mit Sharpe/Max Drawdown, Zeitraum, Kosten steht (CLAUDE.md, Journal 30.09.); Methoden für die Dokumentation fehlen. |
| 🟡 | Vorgehen mit Methoden, Instrumenten, Modellen; Produktdefinition | Produkt (Bot + Dashboard) gebaut, Methodik in Metaprompts und `entscheidungen.md`, aber noch kein Konzepttext. |
| ❌ | Mindmap der Untersuchungsthemen mit Zuständigkeiten | Nicht vorhanden. |
| ❌ | Erste Version des dreistufigen Inhaltsverzeichnisses | Nicht vorhanden. |
| 🟡 | Vorgehen zur weiteren Informationsbeschaffung | Deep Research + Prüfung mit `/quelle` vorhanden, aber nicht ausformuliert. |
| 🟡 | Fachliteratur beschrieben und bewertet (Autorenvertrauen) | `autor_vertrauen` nur für Q1–Q3 ausgefüllt, `gelesen_von` überall leer. |
| ❌ | Aktivitäten der Projektwoche und erhoffte Erkenntnisse | Nicht dokumentiert. |
| ❌ | Professioneller Zeitplan bis zur Abgabe | Nicht vorhanden. |
| ✅ | 2 AARs oder erste Einträge im Arbeitsjournal | 8 Einträge in `docs/arbeitsjournal.csv` (23.09.–20.10.). |

## Rollen und Teamorganisation

| | Punkt | Begründung |
|---|---|---|
| ❌ | Fünf Rollen verteilt (Zeit, Raster, Wegleitung, KI, Deklaration) | In den Vorgaben alle mit «?». |
| 🟡 | Genutzte KI-Programme/Abos | Claude (Cowork), Claude Code bekannt; Deep-Research-Tool nicht benannt. |
| ❌ | Kommunikationswege, Antwortzeiten, fixer Besprechungstermin, Notenerwartung | Nirgends festgehalten. |
| 🟡 | AAR oder Arbeitsjournal | Journal gewählt; mit der Lehrperson zu klären, ob ein Auszug zu den AAR-Terminen reicht. |

## Projektwoche (Vorbereitung)

| | Punkt | Begründung |
|---|---|---|
| ❌ | Jede Person hat mindestens 1 Kapitel Fachliteratur gelesen | `gelesen_von` in `docs/quellen.md` leer. |
| ❌ | Interviewpartner angeschrieben | Interview mit Entwickler geplant (Journal 23.09.), Kontakt nicht dokumentiert. |
| ✅ | Art der Foto-Dokumentation festgelegt | `docs/fotostrecke.md` + Befehl `/fotostrecke`. |
| ❌ | Rollen verteilt | Siehe oben. |

## Dokumentation (laufend)

| | Punkt | Begründung |
|---|---|---|
| 🟡 | Arbeitsjournal | Vollständig bis 20.10., Spalte «wer» bei den Repo-Einträgen offen (Git-Name = GitHub-Name). |
| 🟡 | Prompt-Sammlung im Wortlaut | 22 Prompts erfasst; Wortlaut von Metaprompt A–E fehlt (`docs/prompts/` nur Platzhalter). |
| 🟡 | Naiv-Test (Metaprompt C) | `../naiv test/backtest.py` liegt ausserhalb des Repos und ist weder im Prompt-Log noch im Journal erfasst. |
| ✅ | KI-Fehlerlog | 2 Einträge; das Team-Review steht noch aus. |
| 🟡 | Entscheide vom Team bestätigt | 4 von 32 bestätigt (E2, E7, E19, E22), E20 Vorschlag offen. |
| 🟡 | Quellen mit 4-Schritte-Methode geprüft | Siehe Konzept. |
| 🟡 | Fotostrecke aller Phasen | Nur Phase Umsetzung (30.09.); Konzeptphase und Dashboard-Screenshots fehlen. |
| 🟡 | Deklaration laufend | Entwurf in `docs/deklaration_entwurf.md`, viele Punkte offen. |

## Schlussabgabe (07.02.2027)

| | Punkt | Begründung |
|---|---|---|
| ❌ | Schriftliche Dokumentation (PDF + Word, ca. 38'000 Zeichen) | Noch nicht begonnen. |
| 🟡 | Prozessunterlagen (Titelblatt + Journal + Einzelreflexionen) | Journal + Export (`scripts/export_prozessunterlagen.py`) bereit; Titelblatt und Einzelreflexionen fehlen. |
| 🟡 | Deklaration (PDF) | Entwurf vorhanden. |
| 🟡 | Produkt | `v0.1-ki-unreviewed` läuft (In-Sample); Team-Review und Out-of-Sample-Test fehlen. |

## Was fehlt bis zum 25.10. (Konzept)

1. Rollen verteilen und in `docs/vorgaben/bma_vorgaben.md` eintragen.
2. Konzeptdokument schreiben: Motivation, Fragestellung + Methoden (auch für die Dokumentation), Mindmap, 3-stufiges Inhaltsverzeichnis, Zeitplan, Aktivitäten Projektwoche.
3. Mindestens die zitierten Quellen (Q8–Q13) mit `/quelle` prüfen, jede Person liest ein Kapitel und trägt sich in `gelesen_von` ein.
