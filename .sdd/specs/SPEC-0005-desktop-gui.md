---
id: SPEC-0005
title: "Desktop-GUI"
type: feature
status: implemented
owner: "Boris Brünen"
created: 2026-10-19
updated: 2026-10-19
version: 0.1.0
priority: medium
tags: [gui, pyside6]
depends_on: ["SPEC-0001", "SPEC-0002", "SPEC-0003", "SPEC-0004"]
fr_test_map:
  FR-01: TST-0010
  FR-02: TST-0010
  FR-03: TST-0010
  FR-04: TST-0010
  FR-05: TST-0010
  FR-06: TST-0010
  FR-07: TST-0011
  FR-08: TST-0011
  FR-09: TST-0011
  FR-10: TST-0010
  FR-11: TST-0011
contracts: ["CON-0010"]
tests: ["TST-0010", "TST-0011"]
---

# Desktop-GUI

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

Planer:innen sollen ohne Kommandozeile arbeiten: Excel laden, Regeln wählen, planen, Ergebnis prüfen, exportieren.

## 2. Zielsetzung

**Primärziel:** Eine Desktop-Anwendung (PySide6/Qt) bedient den gesamten Ablauf Import → Planung → Export.

**Erfolgskriterien (messbar):**
- [ ] Kompletter Durchlauf mit ≤ 5 Klicks aus gültiger Excel-Datei.
- [ ] GUI bleibt während der Planung bedienbar (Solver in Hintergrund-Thread, Abbruch möglich).

**Nicht-Ziele (explizit):**
- Kein Mehrbenutzer-/Web-Betrieb.
- Kein vollständiger manueller Plan-Editor in v1 (nur Ansicht; Drag-and-Drop später).

## 3. User Stories

| ID    | Als ...   | möchte ich ...                          | um ...                                  |
|-------|-----------|-----------------------------------------|-----------------------------------------|
| US-01 | Planer:in | Excel-Datei laden und Fehler sehen      | die Daten korrigieren zu können         |
| US-02 | Planer:in | Regeln an-/abschalten und gewichten     | Planvarianten zu erzeugen               |
| US-03 | Planer:in | Fortschritt sehen und abbrechen         | bei langen Läufen die Kontrolle zu behalten |
| US-04 | Planer:in | den Plan nach Termin und Person ansehen | ihn zu prüfen, bevor ich exportiere     |

## 4. Funktionale Anforderungen

- **FR-01:** Hauptfenster mit Schritten: Daten laden, Regeln, Planen, Ergebnis, Export.
- **FR-02:** Fehlerliste aus SPEC-0001 wird tabellarisch angezeigt; Klick markiert die Quelle.
- **FR-03:** Regelverwaltung listet alle registrierten Restriktionen (SPEC-0003) mit Schalter und Gewicht.
- **FR-04:** Planung läuft in einem Worker-Thread mit Fortschritt, Zeitlimit und Abbrechen.
- **FR-05:** Ergebnisansichten: nach Termin, nach Person, nach Thema; Verletzungen hervorgehoben.
- **FR-06:** Export über Dialog (SPEC-0004).
- **FR-07:** Letzte Einstellungen (Dateipfad, Regelkonfiguration) werden gespeichert.
- **FR-09 (Abstraktion):** Die GUI nutzt `Planer` mit Fortschritts-Callback und Abbruchsignal (SPEC-0002 FR-12) und speichert Einstellungen über eine Schnittstelle `Einstellungsspeicher` (Qt-unabhängig, Standard: YAML-Datei).
- **FR-08:** Die GUI enthält keine Fachlogik; sie ruft nur die Library-Schnittstellen auf.
- **FR-10 (Daten ergänzen):** Fehlen in der Excel Themenwerte oder Zeitslots, kann die Seite „Daten" sie ergänzen: Wichtigkeit, Mindestanzahl und Dauer je Thema sind in einer Tabelle bearbeitbar; Zeitslots lassen sich per Formular (Tage, Beginn, Ende, Slotlänge) erzeugen. „Planen" ist erst möglich, wenn Daten fehlerfrei und Zeitslots vorhanden sind.
- **FR-11 (Anwendungsschicht):** Zustand und Abläufe (Laden, Themen/Slots ändern, Regeln, Planen, Export, Einstellungen) liegen in einer Qt-freien Klasse `Sitzung`; die Widgets sind dünne Ansichten darauf.

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                           |
|---------------|-------------------------------------------------------|
| Plattform     | Linux, Windows, macOS                                 |
| Accessibility | Tastaturbedienbar, Kontrast gemäß Systemtheme         |
| Sprache       | Oberfläche deutsch                                    |
| Datenschutz   | Keine Netzwerkzugriffe                                |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: GUI-Ablauf

  Scenario: Voller Durchlauf
    Given die App ist gestartet
    When ich eine gültige Excel-Datei lade und "Planen" wähle
    Then sehe ich den Plan nach Termin und Person
    And kann ich ihn als Excel exportieren

  Scenario: Planung abbrechen
    Given eine laufende Planung
    When ich "Abbrechen" wähle
    Then bleibt die GUI bedienbar und ich erhalte die beste bisherige Lösung
```

## 7. Edge Cases & Fehlerfälle

- Datei während der Arbeit geändert → Neuladen anbieten.
- Hohe DPI/kleine Bildschirme.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                  |
|-------------|----------|---------------------------------------|
| CON-0010    | behavior | Gherkin-Abläufe der GUI               |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                          |
|----------|------------|----------------------------------------------|
| TST-0010 | acceptance | Abläufe per pytest-qt (offscreen)            |
| TST-0011 | unit       | Sitzung, Zeitraster, Einstellungen (ohne Qt) |

## 10. Offene Fragen

- [x] PySide6 (LGPL) als Toolkit; bei Einwänden später änderbar, da die Logik Qt-frei ist.
- [x] v1: nur Ansicht, kein manuelles Nachjustieren.

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
| 2026-10-19 | 0.3.0   | Boris Brünen | SOLID-Review: Abhängigkeitsrichtung und Abstraktionen präzisiert |
| 2026-10-19 | 0.4.0   | Boris Brünen | Daten ergänzen (FR-10), Anwendungsschicht (FR-11) |
