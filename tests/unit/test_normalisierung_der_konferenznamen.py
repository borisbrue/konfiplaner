"""TST-0015 – Normalisierung der Konferenznamen (CON-0012)."""

import pytest

from konfiplaner.normalisierung import SICHER, UNBEKANNT, VORSCHLAG, Normalisierung, schluessel

KANON = [
    "Deutsch",
    "DuG",
    "Englisch",
    "Mathematik",
    "Biologie",
    "NW",
    "GL",
    "Sowi",
    "Wipo",
    "PPL",
    "HW",
    "Geschichte",
]


def loese(roh: str, n: Normalisierung | None = None):
    return (n or Normalisierung()).loese(roh, KANON)


@pytest.mark.parametrize(
    "a,b",
    [
        ("GL/Sowi", "GL / Sowi"),
        ("GL/Sowi", "gl/ sowi"),
        ("GL, Sowi", "gl,sowi"),
        (" Mathe ", "mathe"),
        ("NW  Biologie", "nw biologie"),
    ],
)
def test_schluessel_ignoriert_schreibweise_und_leerzeichen_um_trenner(a, b):
    assert schluessel(a) == schluessel(b)


def test_schluessel_unterscheidet_verschiedene_werte():
    assert schluessel("GL/Sowi") != schluessel("GL/Wipo")


@pytest.mark.parametrize("roh", ["Deutsch", "deutsch", " DEUTSCH ", "Sowi", "SoWi", "wipo", "WiPo"])
def test_exakte_treffer_sind_sicher(roh):
    a = loese(roh)
    assert a.status == SICHER and len(a.konferenzen) == 1


def test_exakter_treffer_nennt_den_namen_des_konferenzsatzes():
    assert loese("sowi").konferenzen == ("Sowi",)


@pytest.mark.parametrize(
    "roh,ziel",
    [
        ("Mathe", ["Mathematik"]),  # eindeutiges Präfix
        ("Bio", ["Biologie"]),
        ("Philosophie", ["PPL"]),  # Synonym
        ("Hauswirtschaft", ["HW"]),
        ("GL/GE", ["GL", "Geschichte"]),
        ("GL/Sowi", ["GL", "Sowi"]),
        ("GL, Sowi", ["GL", "Sowi"]),
        ("GL/WiPo/Sowi", ["GL", "Wipo", "Sowi"]),
        ("Bio, NW", ["Biologie", "NW"]),
        ("NW Biologie", ["NW", "Biologie"]),  # Leerzeichen als Trenner
        ("DuG / Deutsch im Wechsel", ["DuG", "Deutsch"]),  # erstes Wort ist die Konferenz
        ("Geschichte/GL", ["Geschichte", "GL"]),
        ("PPL/Philo", ["PPL"]),  # Duplikate entfallen
    ],
)
def test_abgeleitete_zuordnungen_sind_nur_vorschlaege(roh, ziel):
    a = loese(roh)
    assert a.status == VORSCHLAG and list(a.konferenzen) == ziel


@pytest.mark.parametrize("roh", ["TC", "E", "Quatsch", "GL/Quatsch", "", "Mathe/Quatsch"])
def test_nicht_zuordenbares_ist_unbekannt_ohne_vorschlag(roh):
    a = loese(roh) if roh else Normalisierung().loese(" ", KANON)
    assert a.status == UNBEKANNT and a.konferenzen == ()


def test_mehrdeutiges_praefix_ist_unbekannt():
    a = Normalisierung().loese("Bio", ["Biologie", "Biochemie"])
    assert a.status == UNBEKANNT


def test_synonym_gilt_nur_wenn_das_ziel_im_konferenzsatz_liegt():
    assert Normalisierung().loese("Philosophie", ["Deutsch"]).status == UNBEKANNT


def test_bestaetigte_zuordnung_ist_sicher_und_hat_vorrang():
    n = Normalisierung()
    n.bestaetige("Mathe", ["Mathematik"])
    n.bestaetige("E", ["Englisch"])
    assert loese("Mathe", n).status == SICHER and loese("E", n).konferenzen == ("Englisch",)
    n.bestaetige("Deutsch", ["DuG"])  # darf auch einen exakten Treffer überstimmen
    assert loese("Deutsch", n).konferenzen == ("DuG",)


def test_bestaetigung_gilt_fuer_alle_schreibweisen_des_schluessels():
    n = Normalisierung()
    n.bestaetige("GL/Sowi", ["GL", "Sowi"])
    for roh in ("GL / Sowi", "gl/ sowi", "GL/ Sowi"):
        assert loese(roh, n).status == SICHER


def test_bestaetigung_darf_neue_konferenzen_nennen():
    n = Normalisierung()
    n.bestaetige("TC", ["Technik/Chemie"])
    assert loese("TC", n).konferenzen == ("Technik/Chemie",)
    assert n.konferenzen_aus_bestaetigungen() == ["Technik/Chemie"]


@pytest.mark.parametrize("roh,ziele", [("X", []), ("X", ["", "  "]), ("", ["A"]), ("  ", ["A"])])
def test_bestaetigen_verlangt_rohwert_und_konferenz(roh, ziele):
    with pytest.raises(ValueError):
        Normalisierung().bestaetige(roh, ziele)


def test_bestaetigung_entfernen():
    n = Normalisierung({"mathe": ["Mathematik"]})
    n.entferne("Mathe")
    assert loese("Mathe", n).status == VORSCHLAG


def test_serialisierung_rundreise_und_toleranz():
    n = Normalisierung()
    n.bestaetige("GL/Sowi", ["GL", "Sowi"])
    assert Normalisierung.aus_dict(n.bestaetigt()).bestaetigt() == {"gl/sowi": ["GL", "Sowi"]}
    kaputt = {"a": 5, "b": [], "c": ["ok"], "d": "Einzeln", "": ["x"], "e": [1, 2]}
    assert Normalisierung.aus_dict(kaputt).bestaetigt() == {"c": ["ok"], "d": ["Einzeln"]}
    assert Normalisierung.aus_dict("quatsch").bestaetigt() == {}
    assert Normalisierung.aus_dict(None).bestaetigt() == {}
