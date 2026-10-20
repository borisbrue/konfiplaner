# KonfiPlaner

Stellt Personen zu Terminen zusammen: Jede Person hat zwei Schwerpunktthemen, jedes Thema muss als Termin
stattfinden und hat eine Wichtigkeit, eine Mindestteilnehmerzahl und eine Dauer. Eingabe und Ausgabe sind
Excel-Dateien, geplant wird mit einem Constraint-Solver (OR-Tools CP-SAT). Entwickelt nach Spec-Driven
Development, siehe `.sdd/specs/`.

## Start

```bash
uv sync
uv run konfiplaner        # Desktop-Oberfläche
uv run pytest             # Tests (Performance-Test: uv run pytest -m performance)
```

## Oberfläche

Dunkles Design („Schiefertafel bei Abendlicht"): Die Schritte stehen links in einer Seitenleiste mit Kurzstatus
(Strg+1 bis Strg+6 wechselt die Seite), jede Fachkonferenz hat in allen Ansichten ihre eigene Fachfarbe, eine
`.xlsx`-Datei lässt sich auf das Fenster ziehen. Schrift: Atkinson Hyperlegible Next (SIL OFL, im Paket enthalten).

## Excel-Eingabe

Pflicht ist das Blatt `Personen` mit den Spalten `Name`, `Thema 1`, `Thema 2`. Optional:

| Blatt | Spalten |
|---|---|
| `Themen` | `Name`, `Wichtigkeit` (1–5), `Mindestanzahl`, `Dauer` (Minuten) |
| `Zeitslots` | `Tag`, `Start`, `Ende` |
| `Verfügbarkeiten` | `Person`, `Tag`, `Start` (Slot = Tag + Start) |

Fehlt `Themen`, gelten Wichtigkeit 3, Mindestanzahl 1 und 45 Minuten; fehlen `Zeitslots`, erzeugt man sie in
der Oberfläche. Überschriften werden unabhängig von Groß-/Kleinschreibung und Leerzeichen erkannt.

## Lehrerliste und Konferenzen

Die Software liest auch eine Lehrerliste (Spalten Nachname, Vorname, Fachkonferenz I–III, Vorsitzende) und ein
Blatt `Konferenzen` mit festen Terminen (Konferenz, Tag, Start, Ende, optional Hauptkonferenz, Wichtigkeit,
Mindestanzahl). Ablauf in der Oberfläche:

1. **Daten:** Datei laden; uneinheitliche Konferenznamen im Reiter „Normalisierung" zuordnen und bestätigen.
2. **Konferenzen:** die stattfindenden Konferenzen auswählen; wer eine verliert, behält die übrigen.
3. **Lehrkräfte:** Konferenzen und Rangfolge, Vorsitz, gesperrte und feste Termine einzeln oder für mehrere
   Lehrkräfte ändern; „Markierte neu verplanen" berechnet nur die geänderten Lehrkräfte neu.
4. **Regeln**, **Planen**, **Ergebnis** und Export wie zuvor. Bei gleichzeitigen Konferenzen gewinnt die
   höhere Rangfolge (Fachkonferenz I vor II vor III).

## Regeln erweitern

Eine Restriktion ist eine Klasse mit eindeutigem Namen (`konfiplaner.restriktionen.Restriktion`), registriert per
Dekorator `@restriktion` oder über den Entry-Point `konfiplaner.restriktionen`. Alle Regeln, auch die
Grundregeln, lassen sich je Lauf als hart, weich oder aus konfigurieren (GUI-Reiter „Regeln" oder YAML).

## macOS-App

Die App wird per GitHub Actions gebaut (Workflow „macOS-App“, Apple Silicon): Actions → macOS-App → Run workflow, danach `KonfiPlaner-macos.zip` aus den Artefakten laden. Die App ist nicht notarisiert; auf einem fremden Mac beim ersten Start Rechtsklick → Öffnen (oder `xattr -dr com.apple.quarantine KonfiPlaner.app`).
