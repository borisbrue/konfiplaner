# AGENTS.md

> Dieses Dokument gibt Code-generierenden Agenten den nötigen Kontext über dieses Repository.
> Es wird von `sdd validate` auf Vollständigkeit geprüft.
> **Fülle alle Sektionen aus** — unvollständige Sektionen reduzieren die Code-Qualität des Agenten.

## Service-Zweck

**KonfiPlaner** (Arbeitstitel) stellt Personen zu Terminen zusammen. Jede Person hat zwei
Schwerpunktthemen aus einem festen Themenset; jedes Thema muss als Termin vorkommen, hat eine
Wichtigkeit, eine Mindestanzahl und eine Dauer.

- Eingabe: Excel-Listen (Personen, Themen, Zeitslots, Verfügbarkeiten); Ausgabe: Excel-Plan.
- Planung per Constraint-Solver (OR-Tools CP-SAT), Restriktionen als Plugins erweiterbar.
- Desktop-GUI (PySide6), vollständig lokal (DSGVO-freundlich).

## Architektur

- **Typ:** Desktop-App + Library
- **Schichten:** GUI → Anwendungslogik → IO (Excel) / Solver → Restriktionen → Domänenmodell
- **Externe Systeme:** keine
- **Muster:** Strategy/Registry für Restriktionen; GUI ohne Fachlogik (Library-first).

## Verzeichnisstruktur

```
/
├── konfiplaner/
│   ├── modell.py        # Domänenmodell (Thema, Person, Zeitslot, Termin, Plan)
│   ├── excel_import.py  # SPEC-0001
│   ├── solver.py        # SPEC-0002
│   ├── restriktionen/   # SPEC-0003 (Registry + Regeln)
│   ├── excel_export.py  # SPEC-0004
│   └── gui/             # SPEC-0005 (PySide6)
├── tests/
└── .sdd/                # Specs, Contracts, Tests
```

## Externe Abhängigkeiten

| Service | Zweck |
|---------|-------|
| (keine) | Alles lokal |

Laufzeit-Bibliotheken: `ortools`, `openpyxl`, `PySide6`, `pyyaml`. Dev: `pytest`, `pytest-qt`, `ruff`.

## Build- und Start-Befehle

```bash
uv sync
uv run konfiplaner      # GUI starten
uv run pytest
sdd validate
```

## Linting- und Formatierungsregeln

- **Formatter/Linter:** ruff
- **Kritische Regeln:** Ruff-Fehler und fehlschlagende Tests brechen den Build.

## Taste Invariants

<!-- Kleine, versionierte Regelsets die als harte CI-Fehler durchgesetzt werden (nie als Warnings).
     Agenten dürfen diese Regeln NIEMALS mit Inline-Suppress-Kommentaren umgehen. -->

- **Inline-Disable verboten:** Unterdrücke niemals Linter-Fehler durch Inline-Kommentare
  (z.B. `# noqa`, `// eslint-disable-next-line`, `@SuppressWarnings`, `# type: ignore`).
  Beheble die Ursache — unterdrücke nicht den Fehler.
- <!-- Weitere Taste Invariants, z.B.: -->
  <!-- - "Alle REST-Endpunkte brauchen Auth-Annotations" -->
  <!-- - "Services importieren nie aus der Controller-Schicht" -->
  <!-- - "Logging ausschließlich via structlog/logger.info, kein print/console.log" -->

## Konventionen

- Python ≥ 3.11, Typannotationen überall; Code-Bezeichner deutsch (Domäne), Docstrings deutsch.
- Kein Code ohne Spec/Test (SDD): erst Spec → Contract → Test → Code.
- Logging nur über `logging`, keine Personennamen im Log.

## SDD-Kontext

<!-- Welche Specs, Contracts und Holdout-Szenarien sind relevant für neue Features? -->

- Specs: `specs/` — definieren WAS gebaut werden soll
- Contracts: `contracts/` — definieren WIE die Schnittstellen aussehen
- Holdout: `.sdd/holdout/` — **nicht lesen** (Test-Isolation)
