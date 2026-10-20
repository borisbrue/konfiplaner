---
id: SPEC-0012
title: "Verteilung der Lehrkräfte auf Konferenzen"
type: feature           # feature | bug-fix
status: implemented           # draft | review | approved | implemented | deprecated
owner: "Boris Brünen"
created: 2026-10-20
updated: 2026-10-20
version: 0.1.0
priority: critical        # low | medium | high | critical
tags: [verteilung, regeln, solver, lehrerliste]
depends_on: ["SPEC-0002", "SPEC-0003", "SPEC-0006", "SPEC-0007", "SPEC-0008", "SPEC-0010"]          # z.B. ["SPEC-0001"]
fr_test_map:
  FR-01: TST-0024
  FR-02: TST-0025
  FR-03: TST-0025
  FR-04: TST-0025
  FR-05: TST-0024
  FR-06: TST-0025
  FR-07: TST-0024
  FR-08: TST-0024
  FR-09: TST-0025
  FR-10: TST-0025
  FR-11: TST-0024
contracts: ["CON-0017"]           # z.B. ["CON-0001"] – MUSS mindestens einen Eintrag enthalten
tests: ["TST-0024", "TST-0025"]               # z.B. ["TST-0001"] – MUSS mindestens einen Eintrag enthalten
---

# Verteilung der Lehrkräfte auf Konferenzen

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

Mit den echten Daten ließ sich nicht planen: Die Regel `schwerpunkte` verlangt, dass jede Lehrkraft **alle** ihre zwei bis drei Konferenzen besucht, die Konferenzen finden aber im selben Slot statt. In der Praxis muss nicht jede Lehrkraft an jeder ihrer Konferenzen teilnehmen. Nur der Vorsitz ist gesetzt; alle anderen verteilen sich auf die Konferenzen ihres Sets, möglichst gleichmäßig, mit der Rangfolge FK I vor II vor III als Vorliebe. Wo Konferenzen zeitlich getrennt liegen, besucht eine Lehrkraft so viele, wie zeitlich passen.

## 2. Zielsetzung

**Primärziel:** Lehrerlisten lassen sich standardmäßig planen: Jede Lehrkraft nimmt an mindestens einer ihrer Konferenzen teil, der Vorsitz ist gesetzt, die Mindestanzahl wird gesichert, und der Rest wird nach Rangfolge und Ausgleich verteilt.

**Erfolgskriterien (messbar):**
- [ ] Die echte Liste (101 Lehrkräfte, 16 ausgewählte Konferenzen, ein Slot) ist ohne Regeländerung planbar.
- [ ] Jede Lehrkraft mit mindestens einer Konferenz nimmt an mindestens einer teil; kein Vorsitz fehlt in seiner Konferenz.
- [ ] Die Teilnehmerzahlen weichen so wenig wie möglich von der Zielgröße ab, solange Mindestanzahl und Sets das zulassen.
- [ ] Planung für 101/16 in ≤ 60 s.

**Nicht-Ziele (explizit):**
- Kein Verschieben von Terminen (SPEC-0008).
- Das Drag-&-Drop-Brett folgt in SPEC-0013.

## 3. User Stories

| ID    | Als ...   | möchte ich ...                                           | um ...                                          |
|-------|-----------|----------------------------------------------------------|-------------------------------------------------|
| US-01 | Planer:in | dass sich Lehrkräfte auf ihre Konferenzen verteilen      | statt alle Konferenzen gleichzeitig besuchen zu müssen |
| US-02 | Planer:in | dass kleine Konferenzen genug Teilnehmende bekommen      | die Mindestanzahl zu sichern                    |
| US-03 | Planer:in | bei Unlösbarkeit einen verständlichen Hinweis            | die richtige Regel anzupassen                   |

## 4. Funktionale Anforderungen

- **FR-01 (Profil „Verteilen"):** Für Lehrerlisten (SPEC-0007) gilt standardmäßig, solange die Regel nicht von Hand gesetzt wurde (SPEC-0008 FR-06): `verteilung` hart, `rangfolge` weich (Gewicht 1), `ausgleich` weich (Gewicht 1), `schwerpunkte` aus. Das Profil löst für Lehrerlisten das Profil „Festtermine" ab; für andere Dateien mit Konferenztermine bleibt es wie bisher.
- **FR-02 (Regel `verteilung`):** Neue Grundregel (Standard aus): Jede Lehrkraft, die mindestens eine wirksame Konferenz hat (Schwerpunkt oder Vorsitz), nimmt an mindestens einer davon teil. Die Regel nennt Person und Konferenzen, wenn das nicht geht.
- **FR-03 (Regel `rangfolge`):** Neue Grundregel (Standard aus, nur weich oder aus): Jede nicht besuchte Konferenz einer Lehrkraft kostet nach ihrem Rang 100 (erste), 10 (zweite) oder 1 (weitere), mal Gewicht. Es entstehen keine Verstoßmeldungen: nicht an jeder Konferenz teilzunehmen ist kein Fehler. Dadurch besucht eine Lehrkraft bevorzugt ihre erste und zusätzlich so viele weitere, wie zeitlich passen.
- **FR-04 (Regel `ausgleich`):** Neue Grundregel (Standard aus, nur weich oder aus): Zielgröße = Zahl der Lehrkräfte mit Konferenz geteilt durch Zahl der Konferenzen, gerundet, mindestens 1. Jede Teilnehmerzahl einer Konferenz, die von der Zielgröße abweicht, kostet je Person Unterschied 150, mal Gewicht. Der Ausgleich zählt mehr als der Rangunterschied zwischen erster und zweiter Konferenz, weniger als die Mindestanzahl (hart).
- **FR-05 (Mindestanzahl und Vorsitz):** Beide bleiben hart (SPEC-0002 FR-03, SPEC-0006 FR-02). Der Vorsitz zählt als Teilnahme seiner Konferenz.
- **FR-06 (Ein Treffen je Konferenz):** `PlanerOptionen.max_termine_je_thema` begrenzt die Zahl der Termine je Konferenz ohne Festtermine (Standard 3). Für Lehrerlisten setzt die Sitzung 1: eine Konferenz ist ein Treffen.
- **FR-07 (Überschneidung):** Die Regel `keine_ueberschneidung` bleibt hart. Liegen alle Konferenzen im selben Slot, besucht jede Lehrkraft genau eine; liegen sie getrennt, so viele wie die Rangfolge nahelegt.
- **FR-08 (Hinweis bei Unlösbarkeit):** Gibt es keinen Plan und ist `schwerpunkte` hart, nennt die Oberfläche zusätzlich einen Tipp: Die Regel verlangt, dass jede Lehrkraft alle ihre Konferenzen besucht; auf „weich" oder „aus" stellen oder das Profil „Verteilen" nutzen. Die Begründung nennt die tatsächlichen Konflikte.
- **FR-09 (Konferenzebene fest):** `Fixierungen.konferenzen` (Person → Konferenzen) verlangt als harte Vorgabe die Teilnahme an mindestens einem Termin der Konferenz; die Diagnose nennt sie als Regel `fixierung`. `Sitzung.setze_zuweisung(person, konferenzen)` setzt sie dauerhaft (gespeichert wie die übrigen Änderungen, SPEC-0010 FR-10).
- **FR-11 (Profilwahl):** Auf der Seite „Regeln“ wählt ein Auswahlfeld das Profil: Automatisch (folgt der Datei), Verteilen, Rangfolge bei gleichzeitigen Terminen (SPEC-0008) oder Klassisch (alle Konferenzen besuchen). Die Wahl wird gespeichert, stellt alle nicht von Hand gesetzten Regeln um und verwirft den Plan.
- **FR-10 (Planungskontext):** `Planungskontext.abweichung(terme, ziel, text, faktor)` fügt der Zielfunktion die absolute Abweichung der Summe vom Ziel hinzu (SPEC-0003 FR-07).

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                                |
|---------------|------------------------------------------------------------|
| Performance   | 101 Lehrkräfte / 16 Konferenzen ≤ 60 s (CON-0005 bleibt)   |
| Datenschutz   | Keine Namen im Log                                         |
| Kompatibilität| Dateien im Minimalformat verhalten sich wie bisher         |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Verteilung

  Scenario: Lehrkräfte verteilen sich
    Given 2 Konferenzen im selben Slot und Lehrkräfte mit beiden als Set
    When ich plane
    Then nimmt jede Lehrkraft an genau einer teil
    And die Konferenzen sind möglichst gleich groß
```

## 7. Edge Cases & Fehlerfälle

- Eine Konferenz hat weniger mögliche Mitglieder als ihre Mindestanzahl → kein Plan, Begründung nennt Konferenz und Regel `mindestanzahl`.
- Ein Vorsitz leitet zwei gleichzeitige Konferenzen → kein Plan, Begründung nennt beide.
- Lehrkraft ohne Konferenz → keine Pflicht (Warnung wie bisher).

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                          |
|-------------|----------|-----------------------------------------------|
| CON-0017    | behavior | Verteilung, Profil, Ausgleich, Konferenz-Fixierung |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                          |
|----------|------------|--------------------------------------------------------------|
| TST-0024 | acceptance | Gherkin aus CON-0017: Profil, echte Größe, Tipp              |
| TST-0025 | unit       | Regeln, Ausgleich, Fixierungen im Solver, Planungskontext     |

## 10. Offene Fragen

- [ ] Zielgröße je Konferenz proportional zur Mitgliederzahl (später als eigene Spec, falls gleichmäßig nicht passt).

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-20 | 0.1.0   | Boris Brünen | Initiale Erstellung |
