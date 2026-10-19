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

## Excel-Eingabe

Pflicht ist das Blatt `Personen` mit den Spalten `Name`, `Thema 1`, `Thema 2`. Optional:

| Blatt | Spalten |
|---|---|
| `Themen` | `Name`, `Wichtigkeit` (1–5), `Mindestanzahl`, `Dauer` (Minuten) |
| `Zeitslots` | `Tag`, `Start`, `Ende` |
| `Verfügbarkeiten` | `Person`, `Tag`, `Start` (Slot = Tag + Start) |

Fehlt `Themen`, gelten Wichtigkeit 3, Mindestanzahl 1 und 45 Minuten; fehlen `Zeitslots`, erzeugt man sie in
der Oberfläche. Überschriften werden unabhängig von Groß-/Kleinschreibung und Leerzeichen erkannt.

## Regeln erweitern

Eine Restriktion ist eine Klasse mit eindeutigem Namen (`konfiplaner.restriktionen.Restriktion`), registriert per
Dekorator `@restriktion` oder über den Entry-Point `konfiplaner.restriktionen`. Alle Regeln, auch die
Grundregeln, lassen sich je Lauf als hart, weich oder aus konfigurieren (GUI-Reiter „Regeln" oder YAML).
