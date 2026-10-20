"""TST-0027 – Verschieben, Prüfung und Rückgängig in der Sitzung (CON-0018)."""

import pytest

from konfiplaner.anwendung import MANUELL, PRUEFPRAEFIX, Sitzung, pruefe_plan
from konfiplaner.einstellungen import YamlEinstellungen
from konfiplaner.modell import Modell, ModellFehler, Person, Plan, Termin, Thema
from tests.helfer import slots
from tests.xlsx_helfer import lehrer_mit_terminen, lehrerliste, schreibe

EIN_SLOT = [["Tag", "Start", "Ende"], ["Sa", "09:00", "09:45"]]
ZEILEN = [
    ["Eins", "Anna", "", "Deutsch", "Sport", None, "Deutsch"],
    ["Zwei", "Ben", "", "Sport", "Kunst", None, "Sport"],
    ["Drei", "Cem", "", "Kunst", "Deutsch", None, "Kunst"],
    ["Vier", "Dora", "", "Deutsch", "Sport", None, None],
    ["Fünf", "Eva", "", "Sport", "Kunst", None, None],
    ["Sechs", "Finn", "", "Kunst", "Deutsch", None, None],
    ["Sieben", "Gil", "", "Sport", None, None, None],
    ["Acht", "Hanna", "", None, None, None, None],
]


def sitzung(tmp_path, einstellungen=None, zeilen=ZEILEN):
    blaetter = lehrerliste(zeilen, zeitslots=False)
    blaetter["Zeitslots"] = EIN_SLOT
    s = Sitzung(einstellungen)
    s.lade(schreibe(tmp_path / "k.xlsx", blaetter))
    s.planen()
    return s


def teil(s):
    return {t.thema: set(t.teilnehmer) for t in s.plan.termine}


def wo(s, person):
    return {t.thema for t in s.plan.termine if person in t.teilnehmer}


def spalte(s, konferenz):
    return next(sp for sp in s.verteilung() if sp.konferenz == konferenz)


def frei_beweglich(s, name="Sport"):
    """Eine Lehrkraft ohne Vorsitz in `name` mit mindestens einer weiteren Konferenz im Set."""
    for karte in spalte(s, name).karten:
        if not karte.vorsitz and karte.weitere:
            return karte
    raise AssertionError("keine bewegliche Lehrkraft")


# ── Lesen ───────────────────────────────────────────────────────────────────
def test_verteilung_hat_eine_spalte_je_konferenz_und_ohne_zuteilung(tmp_path):
    s = sitzung(tmp_path)
    spalten = s.verteilung()
    assert [sp.konferenz for sp in spalten] == [None, "Deutsch", "Sport", "Kunst"]
    assert [k.name for k in spalten[0].karten] == ["Hanna Acht"]
    assert spalten[0].karten[0].hat_konferenz is False and spalten[0].vorsitz is None


def test_karten_haben_den_vorsitz_zuerst_und_zeigen_das_set(tmp_path):
    s = sitzung(tmp_path)
    sport = spalte(s, "Sport")
    assert sport.karten[0].name == "Ben Zwei" and sport.karten[0].vorsitz and sport.vorsitz == "Ben Zwei"
    assert all(not k.vorsitz for k in sport.karten[1:])
    cem = next(k for sp in s.verteilung()[1:] for k in sp.karten if k.name == "Cem Drei")
    assert cem.weitere == ("Deutsch",)  # Kunst ist die aktuelle Spalte, Deutsch die weitere


def test_kopfzahlen(tmp_path):
    s = sitzung(tmp_path)
    for sp in s.verteilung()[1:]:
        assert (
            sp.teilnehmer == len(sp.karten) and sp.mindestanzahl == 1 and sp.ziel == 2 and not sp.unterbesetzt
        )
    assert sum(sp.teilnehmer for sp in s.verteilung()) == 8


def test_ohne_plan_ist_das_brett_leer(tmp_path):
    s = Sitzung()
    s.lade(schreibe(tmp_path / "k.xlsx", lehrerliste(ZEILEN)))
    assert s.verteilung() == [] and s.pruefe_verteilung() == [] and not s.kann_rueckgaengig
    with pytest.raises(ModellFehler, match="Kein Plan"):
        s.verschiebe("Anna Eins", "Sport")


# ── Verschieben ─────────────────────────────────────────────────────────────
def test_verschieben_im_set_aendert_den_plan_und_merkt_die_zuweisung(tmp_path):
    s = sitzung(tmp_path)
    karte = frei_beweglich(s)
    ziel = karte.weitere[0]
    folge = s.verschiebe(karte.name, ziel, "Sport")
    assert not folge.ausnahme
    assert wo(s, karte.name) == {ziel}
    assert s.zuordnung.personen[karte.name].zuweisung == (ziel,)
    assert MANUELL in s.plan.warnungen
    assert karte.name not in {k.name for k in spalte(s, "Sport").karten}
    assert karte.name in {k.name for k in spalte(s, ziel).karten}


def test_verschieben_markiert_nicht_zum_neu_verplanen(tmp_path):
    s = sitzung(tmp_path)
    karte = frei_beweglich(s)
    s.verschiebe(karte.name, karte.weitere[0], "Sport")
    assert s.markiert == []  # die Änderung ist im Plan schon enthalten


def test_ausnahme_ergaenzt_das_set_ans_ende(tmp_path):
    s = sitzung(tmp_path)
    gil = "Gil Sieben"  # nur Sport im Set
    assert s.konferenzen_von(gil) == ("Sport",)
    folge = s.verschiebe(gil, "Kunst", "Sport")
    assert folge.ausnahme and s.konferenzen_von(gil) == ("Sport", "Kunst")
    assert wo(s, gil) == {"Kunst"}


def test_aus_ohne_zuteilung_in_eine_konferenz(tmp_path):
    s = sitzung(tmp_path)
    folge = s.verschiebe("Hanna Acht", "Deutsch", None)
    assert folge.ausnahme and wo(s, "Hanna Acht") == {"Deutsch"}  # kein Set: Ausnahme
    assert spalte(s, None).karten == ()


def test_gleiche_spalte_aendert_nichts(tmp_path):
    s = sitzung(tmp_path)
    karte = frei_beweglich(s)
    vorher = s.plan
    s.verschiebe(karte.name, "Sport", "Sport")
    assert s.plan is vorher and not s.kann_rueckgaengig


def test_vorsitz_laesst_sich_nicht_verschieben(tmp_path):
    s = sitzung(tmp_path)
    with pytest.raises(ModellFehler, match="Vorsitz von Sport.*Bearbeiten"):
        s.verschiebe("Ben Zwei", "Kunst", "Sport")
    assert wo(s, "Ben Zwei") == {"Sport"}


def test_unbekanntes_ziel_und_unbekannte_lehrkraft(tmp_path):
    s = sitzung(tmp_path)
    with pytest.raises(ModellFehler, match="findet nicht statt"):
        s.verschiebe("Anna Eins", "Latein")
    with pytest.raises(ModellFehler, match="Unbekannte Lehrkraft"):
        s.verschiebe("Niemand", "Sport")
    s.waehle("Kunst", False)
    s.planen()
    with pytest.raises(ModellFehler, match="findet nicht statt"):
        s.verschiebe("Anna Eins", "Kunst")


def test_ueberschneidung_wird_verhindert(tmp_path):
    s = sitzung(tmp_path)
    karte = frei_beweglich(s)
    s.verschiebe(karte.name, karte.weitere[0], "Sport")
    assert not any("gleichzeitig" in h for h in s.pruefe_verteilung())
    zeiten = [t for t in s.plan.termine if karte.name in t.teilnehmer]
    assert len(zeiten) == 1


def test_getrennte_konferenzen_bleiben_erhalten(tmp_path):
    zeilen = [
        ["Eins", "Anna", "", "Deutsch", "Sport", "Kunst", None],
        ["Zwei", "Ben", "", "Deutsch", None, None, "Deutsch"],
        ["Drei", "Cem", "", "Sport", None, None, "Sport"],
        ["Vier", "Dora", "", "Kunst", None, None, "Kunst"],
    ]
    blaetter = lehrer_mit_terminen(
        zeilen,
        ("Deutsch", "Sa", "09:00", "10:00"),
        ("Sport", "Sa", "10:00", "11:00"),
        ("Kunst", "Sa", "10:00", "11:00"),
    )
    s = Sitzung()
    s.lade(schreibe(tmp_path / "g.xlsx", blaetter))
    s.planen()
    assert wo(s, "Anna Eins") >= {"Deutsch"}  # Deutsch liegt getrennt von Sport und Kunst
    s.verschiebe("Anna Eins", "Kunst", "Sport")
    assert (
        "Deutsch" in wo(s, "Anna Eins")
        and "Kunst" in wo(s, "Anna Eins")
        and "Sport" not in wo(s, "Anna Eins")
    )


def test_mehrere_termine_waehlt_den_ohne_ueberschneidung(tmp_path):
    zeilen = [
        ["Eins", "Anna", "", "Deutsch", "Sport", None, None],
        ["Zwei", "Ben", "", "Deutsch", None, None, "Deutsch"],
        ["Drei", "Cem", "", "Sport", None, None, "Sport"],
        ["Vier", "Dora", "", "Sport", None, None, None],
    ]
    blaetter = lehrer_mit_terminen(
        zeilen,
        ("Deutsch", "Sa", "09:00", "10:00"),
        ("Sport", "Sa", "09:00", "10:00"),
        ("Sport", "Sa", "10:00", "11:00"),
    )
    s = Sitzung()
    s.lade(schreibe(tmp_path / "m.xlsx", blaetter))
    s.planen()
    s.setze_zuweisung("Anna Eins", set())
    s.verschiebe("Anna Eins", "Deutsch", None)
    s.verschiebe("Anna Eins", "Sport", "Deutsch")
    sport = [t for t in s.plan.termine if t.thema == "Sport" and "Anna Eins" in t.teilnehmer]
    assert len(sport) == 1


# ── Prüfung ─────────────────────────────────────────────────────────────────
def test_pruefe_plan_mindestanzahl_vorsitz_und_ueberschneidung():
    modell = Modell(
        [Thema("A", mindestanzahl=3, vorsitz="V"), Thema("B")],
        [Person("V", ()), Person("P", ("A", "B")), Person("Q", ("A", "B"))],
        slots(1),
    )
    plan = Plan(
        "optimal",
        [Termin("A", 0, 1, ("P", "Q")), Termin("B", 0, 1, ("P",))],
    )
    hinweise = pruefe_plan(plan, modell)
    assert "A hat 2 von mindestens 3 Teilnehmenden" in hinweise
    assert "Vorsitz V fehlt in A" in hinweise
    assert "P hat zwei Termine gleichzeitig: A und B" in hinweise
    assert pruefe_plan(Plan("optimal", [Termin("A", 0, 1, ("V", "P", "Q"))]), modell) == []


def test_pruefhinweise_stehen_im_plan_und_im_export(tmp_path):
    s = sitzung(tmp_path)
    s.setze_thema(next(i for i, t in enumerate(s.themen) if t.name == "Kunst"), mindestanzahl=3)
    s.planen()
    karte = frei_beweglich(s, "Kunst")
    s.verschiebe(karte.name, karte.weitere[0], "Kunst")
    hinweise = [w for w in s.plan.warnungen if w.startswith(PRUEFPRAEFIX)]
    assert any("Kunst hat" in w and "mindestens 3" in w for w in hinweise)
    export = s.tabellen()["Hinweise"]
    assert ["Warnung", MANUELL] in export
    assert any(r[0] == "Warnung" and "mindestens 3" in r[1] for r in export)


def test_export_stimmt_mit_dem_brett_ueberein(tmp_path):
    s = sitzung(tmp_path)
    karte = frei_beweglich(s)
    ziel = karte.weitere[0]
    s.verschiebe(karte.name, ziel, "Sport")
    zeilen = [z for z in s.tabellen()["Personen"] if z[0] == karte.name]
    assert [z[4] for z in zeilen] == [ziel]
    assert {z[3] for z in s.tabellen()["Termine"] if z[3] == ziel}
    ausgabe = tmp_path / "plan.xlsx"
    s.exportiere(ausgabe)
    assert ausgabe.exists()


# ── Rückgängig ──────────────────────────────────────────────────────────────
def test_rueckgaengig_stellt_plan_set_und_zuweisung_wieder_her(tmp_path):
    s = sitzung(tmp_path)
    vorher = s.plan
    gil = "Gil Sieben"
    s.verschiebe(gil, "Kunst", "Sport")
    assert s.kann_rueckgaengig and s.konferenzen_von(gil) == ("Sport", "Kunst")
    assert s.rueckgaengig()
    assert s.plan is vorher and s.konferenzen_von(gil) == ("Sport",)
    assert gil not in s.zuordnung.personen and not s.kann_rueckgaengig


def test_mehrere_rueckgaengig(tmp_path):
    s = sitzung(tmp_path)
    ausgang = s.plan
    karte = frei_beweglich(s)
    s.verschiebe(karte.name, karte.weitere[0], "Sport")
    s.verschiebe("Gil Sieben", "Kunst", "Sport")
    assert s.rueckgaengig() and s.rueckgaengig()
    assert s.plan is ausgang and not s.rueckgaengig()


def test_rueckgaengig_ist_nach_neuer_planung_ungueltig(tmp_path):
    s = sitzung(tmp_path)
    karte = frei_beweglich(s)
    s.verschiebe(karte.name, karte.weitere[0], "Sport")
    s.planen()
    assert not s.kann_rueckgaengig and not s.rueckgaengig()


def test_rueckgaengig_stellt_die_markierungen_wieder_her(tmp_path):
    s = sitzung(tmp_path)
    s.setze_konferenzen(["Anna Eins"], ["Deutsch"])
    assert s.markiert == ["Anna Eins"]
    karte = frei_beweglich(s)
    s.verschiebe(karte.name, karte.weitere[0], "Sport")
    s.rueckgaengig()
    assert s.markiert == ["Anna Eins"]


# ── Zuweisung bleibt ────────────────────────────────────────────────────────
def test_zuweisung_gilt_bei_jeder_neuplanung_und_nach_dem_neuladen(tmp_path):
    speicher = tmp_path / "e.yaml"
    s = sitzung(tmp_path, YamlEinstellungen(speicher))
    karte = frei_beweglich(s)
    ziel = karte.weitere[0]
    s.verschiebe(karte.name, ziel, "Sport")
    assert ziel in wo(s, karte.name)
    s.planen()
    assert wo(s, karte.name) == {ziel}
    neu = Sitzung(YamlEinstellungen(speicher))
    neu.lade(tmp_path / "k.xlsx")
    neu.planen()
    assert wo(neu, karte.name) == {ziel}


def test_zuruecksetzen_loest_die_zuweisung_und_laesst_den_plan(tmp_path):
    s = sitzung(tmp_path)
    karte = frei_beweglich(s)
    s.verschiebe(karte.name, karte.weitere[0], "Sport")
    plan = s.plan
    s.zuruecksetzen(karte.name)
    assert s.plan is plan  # der Plan bleibt bis zur Neuplanung
    assert not s.zuordnung.personen.get(karte.name)
    assert s.markiert == [karte.name]  # der Plan enthält noch die verworfene Zuweisung
