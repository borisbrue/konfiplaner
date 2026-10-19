"""TST-0014 – Lehrerlisten-Import und Normalisierung (CON-0012). Testnamen folgen den Szenarien der .feature-Datei."""

import pytest

from konfiplaner.anwendung import Sitzung
from konfiplaner.einstellungen import YamlEinstellungen
from konfiplaner.excel_import import importiere
from konfiplaner.normalisierung import Normalisierung
from tests.xlsx_helfer import LEHRER, lehrerliste, schreibe


def lese(tmp_path, zeilen=None, normalisierung=None, **kw):
    return importiere(schreibe(tmp_path / "l.xlsx", lehrerliste(zeilen, **kw)), normalisierung=normalisierung)


def person(erg, name):
    return next(p for p in erg.personen if p.name == name)


def test_format_wird_erkannt_und_namen_werden_zusammengesetzt(tmp_path):
    erg = lese(tmp_path)
    assert erg.lehrerliste and not erg.fehler
    assert person(erg, "Anna Meier").themen == ("Deutsch", "Englisch")  # Reihenfolge FK I, FK II
    assert len(erg.personen) == 4 and erg.modell is not None


def test_ueberschriften_sind_tolerant_dritte_konferenzspalte(tmp_path):
    zeilen = [*LEHRER, ["Berg", "Eva", "", "Sport", "Deutsch", "Mathematik", None]]
    erg = lese(tmp_path, zeilen)
    assert person(erg, "Eva Berg").themen == ("Sport", "Deutsch", "Mathematik")


def test_exakte_namen_sind_sicher(tmp_path):
    zeilen = [*LEHRER, ["Berg", "Eva", "", "deutsch", " Englisch ", None, None]]
    erg = lese(tmp_path, zeilen)
    assert not erg.fehler and person(erg, "Eva Berg").themen == ("Deutsch", "Englisch")


def test_abweichende_schreibweise_ist_nur_ein_vorschlag(tmp_path):
    zeilen = [*LEHRER, ["Berg", "Eva", "", "Mathe", "Sport", None, None]]
    erg = lese(tmp_path, zeilen)
    assert [(f.blatt, f.zeile, f.spalte) for f in erg.fehler] == [("Tabelle1", 6, "Fachkonferenz I")]
    assert "Mathematik" in erg.fehler[0].text and erg.modell is None


def test_bestaetigen_loest_den_fehler_fuer_alle_vorkommen(tmp_path):
    zeilen = [
        *LEHRER,
        ["A", "A", "", "Mathe", None, None, None],
        ["B", "B", "", "Sport", "Mathe", None, None],
        ["C", "C", "", "mathe", None, None, None],
    ]
    n = Normalisierung()
    assert len(lese(tmp_path, zeilen, n).fehler) == 3
    n.bestaetige("Mathe", ["Mathematik"])
    erg = lese(tmp_path, zeilen, n)
    assert not erg.fehler and person(erg, "A A").themen == ("Mathematik",)


def test_zusammengesetzte_zelle_muss_einzeln_bestaetigt_werden(tmp_path):
    zeilen = [*LEHRER, ["X", "Y", "", "Deutsch", "Deutsch/Englisch", None, None]]
    erg = lese(tmp_path, zeilen)
    f = erg.fehler[0]
    assert f.spalte == "Fachkonferenz II" and "Deutsch, Englisch" in f.text
    n = Normalisierung()
    n.bestaetige("Deutsch/Englisch", ["Deutsch", "Englisch"])
    assert person(lese(tmp_path, zeilen, n), "Y X").themen == ("Deutsch", "Englisch")


def test_schluessel_schreibweisen_gelten_gemeinsam(tmp_path):
    zeilen = [
        *LEHRER,
        ["A", "A", "", "Deutsch/Englisch", None, None, None],
        ["B", "B", "", "Deutsch / Englisch", None, None, None],
        ["C", "C", "", "deutsch/ englisch", None, None, None],
    ]
    erg = lese(tmp_path, zeilen)
    vorschlaege = [a for a in erg.aufloesungen if a.status == "vorschlag"]
    assert len(vorschlaege) == 1 and vorschlaege[0].vorkommen == 3


def test_unbekannter_wert_ohne_vorschlag_kann_zugeordnet_werden(tmp_path):
    zeilen = [*LEHRER, ["Berg", "Eva", "", "TC", None, None, None]]
    erg = lese(tmp_path, zeilen)
    assert "kein Vorschlag" in erg.fehler[0].text
    n = Normalisierung()
    n.bestaetige("TC", ["Technik"])
    erg = lese(tmp_path, zeilen, n)
    assert not erg.fehler and person(erg, "Eva Berg").themen == ("Technik",)
    assert "Technik" in [t.name for t in erg.themen]  # neue Konferenz im Konferenzsatz


def test_person_ohne_konferenz_ist_sichtbar(tmp_path):
    zeilen = [*LEHRER, ["Berg", "Eva", "Ku", None, "", None, None]]
    erg = lese(tmp_path, zeilen)
    assert erg.ohne_konferenz == ["Eva Berg"]
    assert [(w.zeile, w.schwere) for w in erg.warnungen] == [
        (6, "warnung")
    ] and "keine Konferenz" in erg.warnungen[0].text
    assert person(erg, "Eva Berg").themen == ()
    assert erg.modell is not None and "Eva Berg" in [p.name for p in erg.modell.personen]


def test_person_mit_einer_konferenz(tmp_path):
    erg = lese(tmp_path)
    assert person(erg, "Cem Kaya").themen == ("Mathematik",)


def test_dieselbe_konferenz_in_zwei_spalten(tmp_path):
    erg = lese(tmp_path, [*LEHRER, ["Berg", "Eva", "", "Deutsch", "deutsch", None, None]])
    assert person(erg, "Eva Berg").themen == ("Deutsch",)


def test_vorsitz_aus_der_spalte_vorsitzende(tmp_path):
    erg = lese(tmp_path)
    assert {t.name: t.vorsitz for t in erg.themen} == {
        "Deutsch": "Anna Meier",
        "Englisch": "Ben Schulz",
        "Mathematik": "Cem Kaya",
        "Sport": "Dora Roth",
    }


def test_vorsitz_ohne_mitgliedschaft(tmp_path):
    erg = lese(tmp_path, [*LEHRER, ["Berg", "Eva", "", "Sport", None, None, "Geschichte"]])
    assert {t.name: t.vorsitz for t in erg.themen}["Geschichte"] == "Eva Berg"
    assert "Geschichte" not in person(erg, "Eva Berg").themen and not erg.fehler


def test_zwei_vorsitzende_derselben_konferenz(tmp_path):
    erg = lese(tmp_path, [*LEHRER, ["Berg", "Eva", "", "Deutsch", None, None, "deutsch"]])
    assert [(f.zeile, f.spalte) for f in erg.fehler] == [(6, "Vorsitzende")] and "Vorsitz" in erg.fehler[
        0
    ].text


def test_doppelter_name(tmp_path):
    erg = lese(tmp_path, [*LEHRER, ["Meier", "Anna", "", "Sport", None, None, None]])
    assert len(erg.personen) == 4 and [w.zeile for w in erg.warnungen] == [6]
    assert person(erg, "Anna Meier").themen == ("Deutsch", "Englisch")  # erste Zeile gilt


def test_namen_werden_bereinigt(tmp_path):
    erg = lese(tmp_path, [*LEHRER, ["  von  Berg ", " Eva  ", "", "Sport", None, None, None]])
    assert "Eva von Berg" in [p.name for p in erg.personen]


def test_bestaetigte_zuordnungen_werden_gemerkt(tmp_path):
    zeilen = [*LEHRER, ["Berg", "Eva", "", "Mathe", None, None, None]]
    datei = schreibe(tmp_path / "l.xlsx", lehrerliste(zeilen))
    speicher = tmp_path / "e.yaml"
    s = Sitzung(YamlEinstellungen(speicher))
    assert s.lade(datei).fehler
    s.bestaetige("Mathe", ["Mathematik"])
    neu = Sitzung(YamlEinstellungen(speicher))
    assert not neu.lade(datei).fehler


def test_themenwerte_bleiben_beim_neuladen(tmp_path):
    datei = schreibe(tmp_path / "l.xlsx", lehrerliste())
    s = Sitzung()
    s.lade(datei)
    i = next(i for i, t in enumerate(s.themen) if t.name == "Deutsch")
    s.setze_thema(i, mindestanzahl=2, dauer_min=90)
    s.neu_laden()
    t = next(t for t in s.themen if t.name == "Deutsch")
    assert (t.mindestanzahl, t.dauer_min) == (2, 90)


def test_themenwerte_und_zeitslots_ueberleben_bestaetigen(tmp_path):
    zeilen = [*LEHRER, ["Berg", "Eva", "", "Mathe", None, None, None]]
    s = Sitzung()
    s.lade(schreibe(tmp_path / "l.xlsx", lehrerliste(zeilen, zeitslots=False)))
    from datetime import time

    s.erzeuge_zeitslots("Sa", time(9), time(10, 30), 45)
    s.setze_thema(0, wichtigkeit=5)
    s.bestaetige_vorschlaege()
    assert s.themen[0].wichtigkeit == 5 and len(s.zeitslots) == 2 and s.planbar


@pytest.mark.parametrize("zeitslots", [True])
def test_planen_mit_vorsitz_und_personen_ohne_konferenz(tmp_path, zeitslots):
    zeilen = [*LEHRER, ["Berg", "Eva", "", None, None, None, None]]
    s = Sitzung()
    s.lade(schreibe(tmp_path / "l.xlsx", lehrerliste(zeilen)))
    plan = s.planen()
    assert plan.status in ("optimal", "machbar")
    assert "Eva Berg hat keine Konferenz" in plan.warnungen
    assert all("Eva Berg" not in t.teilnehmer for t in plan.termine)
    assert all("Anna Meier" in t.teilnehmer for t in plan.termine if t.thema == "Deutsch")
    assert ["Warnung", "Eva Berg hat keine Konferenz"] in s.tabellen()["Hinweise"]


def test_minimalformat_bleibt_unveraendert(tmp_path):
    from tests.xlsx_helfer import PERSONEN, SLOTS

    erg = importiere(schreibe(tmp_path / "m.xlsx", {"Personen": PERSONEN, "Zeitslots": SLOTS}))
    assert not erg.lehrerliste and not erg.fehler and len(erg.personen) == 2


def test_importdauer_500_zeilen(tmp_path):
    import time as t

    zeilen = [
        ["N", str(i), "", "Deutsch", "Englisch", None, "Deutsch" if i == 0 else None] for i in range(500)
    ]
    datei = schreibe(tmp_path / "g.xlsx", lehrerliste(zeilen))
    t0 = t.perf_counter()
    erg = importiere(datei)
    assert t.perf_counter() - t0 < 2 and len(erg.personen) == 500
