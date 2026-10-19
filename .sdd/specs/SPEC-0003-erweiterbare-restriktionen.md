---
id: SPEC-0003
title: Erweiterbare Restriktionen
type: feature
status: implemented
owner: Boris Brünen
created: 2026-10-19
updated: '2026-10-19'
version: 0.3.0
priority: high
tags:
- restrictions
- plugin
depends_on: []
fr_test_map:
  FR-01: TST-0007
  FR-02: TST-0006
  FR-03: TST-0006
  FR-04: TST-0006
  FR-05: TST-0007
  FR-06: TST-0006
  FR-07: TST-0007
  FR-08: TST-0006
contracts:
- CON-0006
- CON-0007
tests:
- TST-0006
- TST-0007
started_at: '2026-10-19T13:12:26Z'
---
# Erweiterbare Restriktionen

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.3.0

## 1. Kontext & Motivation

Die Liste der Planungsregeln wird wachsen (z. B. „Person A nie mit Person B", „Thema X nicht am Freitag"). Neue Regeln dürfen den Solver-Kern nicht verändern müssen.

## 2. Zielsetzung

**Primärziel:** Restriktionen sind eigenständige, registrierbare Bausteine; eine neue Regel braucht nur eine neue Klasse/Datei.

**Erfolgskriterien (messbar):**
- [ ] Eine neue Restriktion lässt sich ohne Änderung an Solver, GUI oder Import hinzufügen.
- [ ] Jede Restriktion ist einzeln aktivier-/deaktivierbar und parametrierbar.

**Nicht-Ziele (explizit):**
- Keine grafische Regel-Programmiersprache.
- Kein Laden fremden Codes aus untrusted Quellen (nur lokale Plugins).

## 3. User Stories

| ID    | Als ...    | möchte ich ...                              | um ...                               |
|-------|------------|---------------------------------------------|--------------------------------------|
| US-01 | Entwickler | eine neue Regel als kleine Klasse ergänzen | ohne Kernänderung zu erweitern       |
| US-02 | Planer:in  | Regeln an- und abschalten und gewichten    | Varianten des Plans zu vergleichen   |

## 4. Funktionale Anforderungen

- **FR-01:** Schnittstelle `Restriktion` mit: eindeutiger Name, Typ (`hart`/`weich`), Parameterschema, Methode `anwenden(modell, solver_kontext)`, Methode `erklaere(plan)` für Verstöße.
- **FR-02:** Registry mit Registrierung per Dekorator und per Python-Entry-Point (`konfiplaner.restriktionen`).
- **FR-03:** Auch die mitgelieferten Grundregeln sind anpassbar: je Restriktion Aktivierung, Typ (hart/weich/aus), Gewicht und Parameter in einer Konfigurationsdatei (YAML) und in der GUI änderbar, ohne Codeänderung.
- **FR-04:** Mitgelieferte Grundregeln (Bezeichner, Standard-Typ): `themenabdeckung` (hart), `mindestanzahl` (hart), `schwerpunkte` (hart), `keine_ueberschneidung` (hart), `verfuegbarkeit` (hart), `wichtigkeit` (weich).
- **FR-05:** Optional können Regeln aus Excel (Blatt `Regeln`) mit Parametern geladen werden.
- **FR-07 (Abstraktion):** `anwenden` erhält einen abstrakten `Planungskontext` (Variablen für Termin-Slot und Teilnahme, Methoden zum Hinzufügen harter Bedingungen und gewichteter Strafterme), nicht das konkrete Solver-Objekt. Der Kontext wird vom Solver-Adapter bereitgestellt.
- **FR-08 (Rangfaktor, SPEC-0008):** `Planungskontext.bedingung` hat einen optionalen `faktor` (Standard 1), der die Kosten einer verletzten weichen Bedingung multipliziert. `schwerpunkte` setzt ihn nach Rang der Konferenz der Person (100, 10, 1).
- **FR-06:** Unbekannte oder fehlerhaft parametrierte Restriktionen führen zu einer klaren Fehlermeldung vor dem Solverlauf.

## 5. Nicht-funktionale Anforderungen

| Kategorie       | Anforderung                                               |
|-----------------|-----------------------------------------------------------|
| Erweiterbarkeit | Neue Regel ≤ 1 neue Datei, keine Änderung im Kern         |
| Testbarkeit     | Jede Restriktion einzeln testbar                          |
| Sicherheit      | Nur lokal installierte Plugins                            |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Restriktionen

  Scenario: Neue Regel registrieren
    Given eine Klasse "NichtZusammen" ist registriert
    When ich plane mit Parametern Person A und Person B
    Then sind A und B in keinem gemeinsamen Termin

  Scenario: Regel deaktivieren
    Given die Regel "keine Überschneidung" ist deaktiviert
    When ich plane
    Then wird sie nicht angewendet

  Scenario: Unbekannte Regel
    Given die Konfiguration nennt eine nicht registrierte Regel
    When ich plane
    Then erhalte ich einen Fehler vor dem Solverlauf
```

## 7. Edge Cases & Fehlerfälle

- Widersprüchliche harte Regeln → Diagnose nennt beide Regeln.
- Gleicher Name doppelt registriert → Fehler.
- Weiche Regel ohne Gewicht → Standardgewicht 1.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                          |
|-------------|----------|-----------------------------------------------|
| CON-0006    | behavior | Verhalten der Restriktions-Schnittstelle      |
| CON-0007    | data     | JSON-Schema der Regel-Konfiguration           |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                |
|----------|------------|----------------------------------------------------|
| TST-0007 | unit       | Registry, Parametervalidierung, Konfigurationsschema |
| TST-0006 | acceptance | Gherkin-Szenarien aus CON-0006                     |
| TST-0007 | contract   | Konfigurationsschema                               |

## 10. Offene Fragen

- [x] Für v1 nur die Grundregeln, diese aber vollständig anpassbar (geklärt 2026-10-19).
- [ ] Sollen Nicht-Entwickler Regeln über Excel/GUI anlegen können oder nur per Code?

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
| 2026-10-19 | 0.2.0   | Boris Brünen | Klärung: Mindestanzahl, Wichtigkeit, Excel-Layout, anpassbare Grundregeln |
| 2026-10-19 | 0.3.0   | Boris Brünen | SOLID-Review: Abhängigkeitsrichtung und Abstraktionen präzisiert |
| 2026-10-19 | +      | Boris Brünen | Nachtrag zu SPEC-0008 (Festtermine, Rangfaktor), Version unverändert |
