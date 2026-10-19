---
id: SPEC-0007
title: "Lehrerlisten-Import und Normalisierung"
type: feature           # feature | bug-fix
status: implemented           # draft | review | approved | implemented | deprecated
owner: "Boris Brünen"
created: 2026-10-19
updated: 2026-10-19
version: 0.1.0
priority: high        # low | medium | high | critical
tags: [import, normalisierung, lehrerliste]
depends_on: ["SPEC-0001", "SPEC-0002", "SPEC-0005", "SPEC-0006"]          # z.B. ["SPEC-0001"]
fr_test_map:
  FR-01: TST-0014
  FR-02: TST-0014
  FR-03: TST-0014
  FR-04: TST-0015
  FR-05: TST-0015
  FR-06: TST-0014
  FR-07: TST-0015
  FR-08: TST-0014
  FR-09: TST-0014
  FR-10: TST-0014
  FR-11: TST-0014
  FR-12: TST-0015
contracts: ["CON-0012"]           # z.B. ["CON-0001"] – MUSS mindestens einen Eintrag enthalten
tests: ["TST-0014", "TST-0015"]               # z.B. ["TST-0001"] – MUSS mindestens einen Eintrag enthalten
---

# Lehrerlisten-Import und Normalisierung

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

Die reale Eingabe ist eine Zuordnungsliste von Lehrkräften zu Fachkonferenzen: je Zeile Nachname, Vorname, Fächer, Fachkonferenz I, Fachkonferenz II, optional Fachkonferenz III und die Spalte „Vorsitzende" (Name der geleiteten Konferenz). Die Konferenznamen sind uneinheitlich geschrieben (Mathe/Mathematik, SoWi/Sowi/WiPo, Päda/Pädagogik, Philosophie/PPL) und teils zusammengesetzt („GL/Sowi", „NW/Biologie"). Manche Lehrkräfte haben keine, andere nur eine Konferenz. Ein Import muss diese Liste einlesen, die Konferenznamen auf einen einheitlichen Satz abbilden und alles Unklare sichtbar machen, statt zu raten.

## 2. Zielsetzung

**Primärziel:** Eine Lehrerliste wird eingelesen; jede Konferenzangabe wird einer oder mehreren einheitlichen Konferenzen zugeordnet, und nur bestätigte Zuordnungen führen zu einem Planungsmodell.

**Erfolgskriterien (messbar):**
- [ ] Die Beispielliste (101 Personen, 26 Vorsitzende) lässt sich importieren; jede Konferenzangabe erscheint genau einmal in der Normalisierungstabelle mit Vorkommen, Zuordnung und Status.
- [ ] Nur exakte Übereinstimmungen (ohne Beachtung von Groß-/Kleinschreibung und Leerzeichen) gelten ohne Bestätigung; alle anderen Zuordnungen bleiben Fehler, bis sie bestätigt sind.
- [ ] Personen ohne Konferenz sind in Import, GUI und Export sichtbar.

**Nicht-Ziele (explizit):**
- Zeitslots je Konferenz und Haupt-/Unterkonferenz-Beziehungen (SPEC-0008).
- Rangfolge der Konferenzen bei Konflikten (SPEC-0008); die Reihenfolge I, II, III wird aber im Modell erhalten.
- Automatisches Raten ohne Bestätigung.

## 3. User Stories

| ID    | Als ...   | möchte ich ...                                           | um ...                                       |
|-------|-----------|----------------------------------------------------------|----------------------------------------------|
| US-01 | Planer:in | die Lehrerliste direkt laden                             | sie nicht umbauen zu müssen                  |
| US-02 | Planer:in | uneinheitliche Konferenznamen einmal zuordnen und merken | beim nächsten Import nichts neu klären zu müssen |
| US-03 | Planer:in | Lehrkräfte ohne Konferenz sehen                          | Lücken in der Liste zu erkennen              |

## 4. Funktionale Anforderungen

- **FR-01 (Format-Erkennung):** Ein Blatt mit den Spalten Nachname und Vorname gilt als Lehrerliste. Die Spalten Fachkonferenz I, II und III (auch als „FK I" u. ä., auch mit Zusatztext wie „ggfs. FK III …") und „Vorsitzende" werden tolerant erkannt (Groß-/Kleinschreibung, Leerzeichen, Zusatztexte); Fächer wird ignoriert. Alle anderen Blätter bleiben im Format von SPEC-0001.
- **FR-02 (Personen):** Der Name einer Person ist „Vorname Nachname" mit bereinigten Leerzeichen. Die Konferenzen der Person (Modell: `Person.themen`) sind die zugeordneten Konferenzen aus FK I, II, III in dieser Reihenfolge ohne Doppelte; es sind 0 bis n. Doppelte Namen sind eine Warnung (erste Zeile gilt, wie SPEC-0001 FR-08).
- **FR-03 (Konferenzsatz):** Der Satz der Konferenzen (Themen) ergibt sich aus der Spalte „Vorsitzende" (jeder verschiedene Wert nach Normalisierung); fehlt die Spalte, aus den einfachen Werten (ohne „/" oder „,"). Weitere Konferenzen kommen durch bestätigte Zuordnungen dazu. Themen erhalten die Standardwerte aus SPEC-0001 FR-05.
- **FR-04 (Normalisierungsstufen):** Jede Konferenzangabe (Rohwert) hat den Status `sicher` (Treffer in den bestätigten Zuordnungen oder exakter Treffer im Konferenzsatz ohne Beachtung von Groß-/Kleinschreibung), `vorschlag` (automatisch abgeleitet, noch nicht bestätigt) oder `unbekannt` (kein Vorschlag).
- **FR-05 (Vorschläge):** Vorschläge entstehen nur aus eindeutigen Mustern: Trennung an „/", „,", „;" oder Leerzeichen in Teile; Teil = eindeutiges Präfix eines Konferenznamens (z. B. „Mathe" → Mathematik), oder ein Konferenzname als erstes Wort („Deutsch im Wechsel" → Deutsch), oder ein bekanntes Synonym (z. B. „Philosophie" → PPL), sofern das Ziel im Konferenzsatz liegt. Ist ein Teil nicht zuordenbar, ist der Status `unbekannt`.
- **FR-06 (Fehler bis bestätigt):** Jede Zelle mit Status `vorschlag` oder `unbekannt` ist ein Fehler (Blatt, Zeile, Spalte, Rohwert, ggf. Vorschlag); solange Fehler bestehen, wird kein Modell geliefert (SPEC-0001 FR-07).
- **FR-07 (Bestätigen):** Eine Zuordnung (Rohwert → Liste von Konferenzen) lässt sich bestätigen oder ändern; der Schlüssel des Rohwerts ignoriert Groß-/Kleinschreibung und Leerzeichen um „/" und „,". Bestätigte Zuordnungen wirken auf alle Vorkommen.
- **FR-08 (Vorsitz):** Der Wert in „Vorsitzende" ist die Konferenz, die die Person leitet (SPEC-0006). Leitet mehr als eine Person dieselbe Konferenz, ist das ein Fehler; eine Person darf mehrere leiten. Der Vorsitz muss nicht Mitglied sein.
- **FR-09 (Ohne Konferenz):** Personen, die in der Datei keine Konferenz haben (abzugrenzen von „Neu zuordnen" nach einer Abwahl, SPEC-0009 FR-04), erzeugen eine Warnung und stehen in einer Liste `ohne_konferenz`; sie nehmen an keinem Termin teil.
- **FR-10 (Persistenz):** Bestätigte Zuordnungen werden gespeichert (Einstellungsspeicher, SPEC-0005 FR-09) und beim nächsten Laden wieder angewandt. Änderungen an Themenwerten bleiben beim Neuladen erhalten.
- **FR-11 (GUI):** Die Seite „Daten" hat die Reiter „Normalisierung" (Rohwert, Vorkommen, Zuordnung bearbeitbar, Status; Schaltfläche „Alle Vorschläge übernehmen") und „Ohne Konferenz". Der Export meldet Personen ohne Konferenz im Blatt „Hinweise".
- **FR-12 (Modell):** `Person.themen` darf 0 bis n verschiedene Themen enthalten (SPEC-0002 FR-01 angepasst). Das Minimalformat aus SPEC-0001 verlangt weiterhin genau zwei.

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                                          |
|---------------|----------------------------------------------------------------------|
| Performance   | 500 Zeilen in < 2 s                                                  |
| Datenschutz   | Keine Namen im Log; Beispieldateien mit Personendaten nie ins Repo   |
| Nachvollziehbarkeit | Jede Zuordnung ist als Rohwert → Konferenz(en) einsehbar        |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Lehrerlisten-Import

  Scenario: Exakte Namen sind sicher
    Given eine Lehrerliste, deren Konferenzen exakt (ohne Beachtung der Schreibweise) den Vorsitz-Konferenzen entsprechen
    When ich importiere
    Then gibt es keinen Fehler

  Scenario: Abweichende Schreibweise ist nur ein Vorschlag
    Given eine Zelle "Mathe" und eine Vorsitz-Konferenz "Mathematik"
    When ich importiere
    Then ist die Zelle ein Fehler mit dem Vorschlag "Mathematik"
    And nach dem Bestätigen gibt es keinen Fehler mehr
```

## 7. Edge Cases & Fehlerfälle

- Zelle nur aus Leerzeichen oder leer → keine Konferenz (kein Fehler).
- Eine Person nennt dieselbe Konferenz in zwei Spalten → sie steht einmal in `Person.themen`.
- Rohwert „GL/Sowi" und „GL / Sowi" und „GL/ Sowi" → ein Schlüssel.
- Bestätigte Zuordnung nennt eine neue Konferenz → sie wird Teil des Konferenzsatzes.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                                   |
|-------------|----------|--------------------------------------------------------|
| CON-0012    | behavior | Verhalten von Lehrerlisten-Import und Normalisierung   |

Betroffener bestehender Contract: `importmodell-und-fehlerliste.schema.json` (CON-0001): Personen mit 0 bis n Themen.

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                          |
|----------|------------|--------------------------------------------------------------|
| TST-0014 | acceptance | Gherkin aus CON-0012: Import, Sitzung, GUI                   |
| TST-0015 | unit       | Normalisierung (Schlüssel, Stufen, Vorschläge), Modell 0..n Themen |

## 10. Offene Fragen

- [ ] Haupt-/Unterkonferenz (GL → Sowi/WiPo, NW → Biologie/Physik) und Zeitslots je Konferenz folgen in SPEC-0008.
- [ ] Die 20 zusammengesetzten Zellen der Beispielliste werden einzeln bestätigt (Aufgabe der Fachseite, nicht der Software).

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
| 2026-10-19 | +      | Boris Brünen | Nachtrag zu SPEC-0009 (Konferenzauswahl), Version unverändert |
