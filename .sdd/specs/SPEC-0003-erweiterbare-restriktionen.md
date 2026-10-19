---
id: SPEC-0003
title: "Erweiterbare Restriktionen"
type: feature
status: draft
owner: "Boris Brünen"
created: 2026-10-19
updated: 2026-10-19
version: 0.2.0
priority: high
tags: [restrictions, plugin]
depends_on: []
contracts: []
tests: []
---

# Erweiterbare Restriktionen

> **Status:** draft · **Owner:** Boris Brünen · **Version:** 0.2.0

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
- **FR-04:** Mitgelieferte Restriktionen: Themenabdeckung, Mindestanzahl, Schwerpunkte, keine Überschneidung, Verfügbarkeit, Wichtigkeitsgewichtung.
- **FR-05:** Optional können Regeln aus Excel (Blatt `Regeln`) mit Parametern geladen werden.
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
| CON-XXXX    | behavior | Verhalten der Restriktions-Schnittstelle      |
| CON-XXXX    | data     | JSON-Schema der Regel-Konfiguration           |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                |
|----------|------------|----------------------------------------------------|
| TST-XXXX | unit       | Registry, Parametervalidierung                     |
| TST-XXXX | acceptance | Gherkin aus Sektion 6                              |
| TST-XXXX | contract   | Konfigurationsschema                               |

## 10. Offene Fragen

- [x] Für v1 nur die Grundregeln, diese aber vollständig anpassbar (geklärt 2026-10-19).
- [ ] Sollen Nicht-Entwickler Regeln über Excel/GUI anlegen können oder nur per Code?

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
| 2026-10-19 | 0.2.0   | Boris Brünen | Klärung: Mindestanzahl, Wichtigkeit, Excel-Layout, anpassbare Grundregeln |
