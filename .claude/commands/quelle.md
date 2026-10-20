---
description: Quelle prüfen (DOI/URL/Angabe) und als APA-7-Eintrag mit Prüfstatus in docs/quellen.md aufnehmen
argument-hint: "<DOI | URL | Literaturangabe>"
---
Zu prüfende Quelle: $ARGUMENTS

1. **Existiert sie?** DOI über `https://api.crossref.org/works/<DOI>` bzw. `https://doi.org/<DOI>` auflösen; bei Büchern einen Katalog (z. B. Open Library, Verlag); bei URLs die Seite öffnen. Ohne DOI zuerst per Titel suchen.
2. **Stimmen Titel, Autoren, Jahr** (und Zeitschrift, Band, Heft, Seiten) mit der Angabe überein? Abweichungen notieren.
3. Eintrag in `docs/quellen.md` (nächste id oder bestehende Zeile ergänzen): APA-7-Angabe nur aus den geprüften Metadaten, DOI/URL, typ, `geprueft`, `pruefung_4_schritte` (Datum, was wie geprüft), autor_vertrauen, kurzinhalt, verwendet_fuer. `gelesen_von` nur ausfüllen, wenn das Team es sagt.
4. **Nicht verifizierbar** → `geprueft = unsicher`, Grund notieren, **nichts ergänzen oder erfinden** (keine DOIs, Seitenzahlen, Autoren).

Melde das Ergebnis in einem Satz (gefunden / abweichend / nicht gefunden).
