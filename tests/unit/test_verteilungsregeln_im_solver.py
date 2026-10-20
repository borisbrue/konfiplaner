"""TST-0025 – Verteilungsregeln, Ausgleich, Fixierungen und Profil (CON-0017)."""

import pytest

from konfiplaner.anwendung import PROFIL_NAMEN, Sitzung
from konfiplaner.einstellungen import YamlEinstellungen
from konfiplaner.modell import Modell, ModellFehler, Person, Thema
from konfiplaner.planer import Fixierungen, PlanerOptionen
from konfiplaner.restriktionen import STANDARD_REGISTRY, Konfiguration
from konfiplaner.restriktionen.basis import RegelEinstellung
from konfiplaner.restriktionen.grundregeln import AUSGLEICH_FAKTOR, RANGFAKTOREN
from konfiplaner.solver import CpSatPlaner
from konfiplaner.zuordnung import LehrerAenderung
from tests.helfer import slots
from tests.xlsx_helfer import lehrer_mit_terminen, schreibe

HART = {
    "themenabdeckung",
    "mindestanzahl",
    "keine_ueberschneidung",
    "verfuegbarkeit",
    "vorsitz",
    "verteilung",
}


def konfig(ausgleich: bool = True, rangfolge: bool = True, verteilung: bool = True) -> Konfiguration:
    """Profil „Verteilen“: alles aus dem Profil, ohne Sitzung."""
    k = Konfiguration.standard(STANDARD_REGISTRY, [n for n in STANDARD_REGISTRY.namen()])
    k.einstellungen["schwerpunkte"] = RegelEinstellung("schwerpunkte", "aus")
    k.einstellungen["verteilung"] = RegelEinstellung("verteilung", "hart" if verteilung else "aus")
    k.einstellungen["rangfolge"] = RegelEinstellung("rangfolge", "weich" if rangfolge else "aus")
    k.einstellungen["ausgleich"] = RegelEinstellung("ausgleich", "weich" if ausgleich else "aus")
    k.einstellungen["wichtigkeit"] = RegelEinstellung("wichtigkeit", "aus")
    return k


def plane(m, k=None, fix=None, **optionen):
    return CpSatPlaner().planen(m, k or konfig(), PlanerOptionen(zeitlimit_s=20, **optionen), fixierungen=fix)


def modell(themen, personen, n_slots=1, verfuegbar=None):
    return Modell(themen, [Person(n, tuple(t)) for n, t in personen], slots(n_slots), verfuegbar or {})


def teil(plan):
    return {t.thema: set(t.teilnehmer) for t in plan.termine}


def groessen(plan):
    return {t.thema: len(t.teilnehmer) for t in plan.termine}


# ── Verteilung ──────────────────────────────────────────────────────────────
def test_jede_lehrkraft_besucht_genau_eine_konferenz_im_selben_slot():
    m = modell([Thema("A"), Thema("B")], [(f"P{i}", ("A", "B")) for i in range(6)])
    plan = plane(m)
    assert plan.status in ("optimal", "machbar")
    alle = [n for t in plan.termine for n in t.teilnehmer]
    assert sorted(alle) == sorted(f"P{i}" for i in range(6))  # jede genau einmal
    assert not plan.verstoesse  # nicht besuchte Konferenzen sind kein Verstoß


def test_ausgleich_macht_die_konferenzen_gleich_gross():
    m = modell([Thema("A"), Thema("B")], [(f"P{i}", ("A", "B") if i % 2 else ("B", "A")) for i in range(10)])
    assert sorted(groessen(plane(m)).values()) == [5, 5]


def test_ohne_ausgleich_entscheidet_die_rangfolge():
    # Jede Konferenz muss stattfinden (themenabdeckung): B bekommt genau die eine nötige Lehrkraft,
    # alle übrigen gehen in ihre erste Konferenz A
    m = modell([Thema("A"), Thema("B")], [(f"P{i}", ("A", "B")) for i in range(6)])
    assert groessen(plane(m, konfig(ausgleich=False))) == {"A": 5, "B": 1}


def test_ausgleich_geht_vor_dem_rangunterschied_der_ersten_und_zweiten_konferenz():
    # A hat 8 Mitglieder mit A als erster, B nur 2 (erste Konferenz B): zum Ausgleich wechseln einige zu B? B kann nur
    # Lehrkräfte aufnehmen, die B in ihrem Set haben: hier haben 4 der A-Lehrkräfte B als zweite
    personen = [(f"P{i}", ("A", "B")) for i in range(4)] + [(f"Q{i}", ("A",)) for i in range(4)]
    personen += [("R0", ("B",)), ("R1", ("B",))]
    plan = plane(modell([Thema("A"), Thema("B")], personen))
    g = groessen(plan)
    assert abs(g["A"] - g["B"]) <= 1  # 5 und 5 statt 8 und 2


def test_mindestanzahl_hat_vorrang_vor_dem_ausgleich():
    personen = [(f"P{i}", ("A", "B")) for i in range(6)]
    plan = plane(modell([Thema("A"), Thema("B", mindestanzahl=5)], personen), konfig(ausgleich=False))
    assert plan.status in ("optimal", "machbar") and groessen(plan)["B"] >= 5


def test_mindestanzahl_nicht_erreichbar_ist_kein_plan():
    m = modell([Thema("A"), Thema("B", mindestanzahl=5)], [(f"P{i}", ("A", "B")) for i in range(3)])
    plan = plane(m)
    assert plan.status == "kein_plan" and "mindestanzahl" in " ".join(plan.begruendung)


def test_vorsitz_ist_gesetzt_auch_wenn_die_erste_konferenz_eine_andere_ist():
    themen = [Thema("A"), Thema("B", vorsitz="V")]
    m = modell(themen, [("V", ("A", "B")), ("P", ("A", "B")), ("Q", ("A", "B"))])
    plan = plane(m)
    assert "V" in teil(plan)["B"] and "V" not in teil(plan)["A"]


def test_vorsitz_in_zwei_gleichzeitigen_konferenzen_ist_kein_plan():
    themen = [Thema("A", vorsitz="V"), Thema("B", vorsitz="V")]
    plan = plane(modell(themen, [("V", ()), ("P", ("A",)), ("Q", ("B",))]))
    text = " ".join(plan.begruendung)
    assert plan.status == "kein_plan" and "Thema A" in text and "Thema B" in text


def test_getrennte_konferenzen_besucht_die_lehrkraft_beide():
    raster = slots(2)
    themen = [Thema("A", festtermine=(raster[0],)), Thema("B", festtermine=(raster[1],))]
    m = Modell(themen, [Person("P", ("A", "B")), Person("Q", ("A",)), Person("R", ("B",))], raster)
    plan = plane(m, konfig(ausgleich=False))
    assert "P" in teil(plan)["A"] and "P" in teil(plan)["B"]


def test_lehrkraft_ohne_konferenz_ist_keine_pflicht():
    plan = plane(modell([Thema("A")], [("P", ("A",)), ("Niemand", ())]))
    assert plan.status in ("optimal", "machbar") and "Niemand" not in teil(plan)["A"]


def test_verteilung_nennt_person_wenn_es_nicht_geht():
    # P ist in beiden Konferenzen nicht verfügbar
    m = modell(
        [Thema("A"), Thema("B")], [("P", ("A", "B")), ("Q", ("A",)), ("R", ("B",))], verfuegbar={"P": set()}
    )
    plan = plane(m)
    assert plan.status == "kein_plan" and "P nimmt an keiner ihrer Konferenzen teil" in " ".join(
        plan.begruendung
    )


def test_rangfolge_ist_nur_eine_vorliebe_ohne_ausgleich_und_gleich_besetzt():
    # beide Konferenzen brauchen gleich viele: P hat A zuerst und geht deshalb nach A
    themen = [Thema("A", mindestanzahl=1), Thema("B", mindestanzahl=1)]
    m = modell(themen, [("P", ("A", "B")), ("Q", ("B",)), ("R", ("A",))])
    assert "P" in teil(plane(m, konfig(ausgleich=False)))["A"]


def test_regeln_und_faktoren():
    assert list(RANGFAKTOREN) == [100, 10, 1]
    assert AUSGLEICH_FAKTOR > RANGFAKTOREN[0] - RANGFAKTOREN[1]  # Ausgleich zählt mehr als I gegen II
    for name in ("rangfolge", "ausgleich"):
        assert STANDARD_REGISTRY.hole(name).erlaubte_typen == ("weich", "aus")
    assert STANDARD_REGISTRY.hole("verteilung").standard_typ == "aus"


def test_ein_treffen_je_konferenz_mit_der_option():
    m = modell([Thema("A", mindestanzahl=2)], [(f"P{i}", ("A",)) for i in range(6)], n_slots=3)
    for grenze in (1, 3):
        plan = plane(m, max_termine_je_thema=grenze)
        assert len(plan.termine) <= grenze and plan.status in ("optimal", "machbar")
    assert len(plane(m, max_termine_je_thema=1).termine) == 1


def test_grosse_instanz_in_zeit():
    import random
    import time

    rnd = random.Random(5)
    namen = [f"K{i}" for i in range(16)]
    themen = [Thema(n) for n in namen]
    personen = []
    for i in range(101):
        k = rnd.choice([1, 2, 2, 2, 3])
        personen.append((f"P{i}", tuple(rnd.sample(namen, k))))
    t0 = time.perf_counter()
    plan = plane(modell(themen, personen), max_termine_je_thema=1)
    assert plan.status in ("optimal", "machbar") and time.perf_counter() - t0 < 30
    anzahl = {n: 0 for n, _ in personen}
    for t in plan.termine:
        for n in t.teilnehmer:
            anzahl[n] += 1
    assert all(a == 1 for a in anzahl.values())  # jede Lehrkraft genau einmal


# ── Konferenz-Fixierung ─────────────────────────────────────────────────────
def test_fixierungen_leer_und_konferenzen():
    assert Fixierungen().leer() and not Fixierungen(konferenzen={"P": ("A",)}).leer()


def test_feste_zuweisung_auf_konferenzebene():
    m = modell([Thema("A"), Thema("B")], [("P", ("A", "B")), ("Q", ("A", "B")), ("R", ("A", "B"))])
    plan = plane(m, fix=Fixierungen(konferenzen={"P": ("B",)}))
    assert "P" in teil(plan)["B"]
    plan = plane(m, fix=Fixierungen(konferenzen={"P": ("A",)}))
    assert "P" in teil(plan)["A"]


def test_unmoegliche_feste_zuweisung_nennt_fixierung():
    m = modell([Thema("A"), Thema("B")], [("P", ("A",)), ("Q", ("B",))])
    plan = plane(m, fix=Fixierungen(konferenzen={"P": ("B",)}))
    assert plan.status == "kein_plan" and "Regel fixierung: P nimmt an B teil" in " ".join(plan.begruendung)


def test_zwei_feste_zuweisungen_im_selben_slot_sind_kein_plan():
    m = modell([Thema("A"), Thema("B")], [("P", ("A", "B")), ("Q", ("A",)), ("R", ("B",))])
    plan = plane(m, fix=Fixierungen(konferenzen={"P": ("A", "B")}))
    assert plan.status == "kein_plan"


# ── Planungskontext ─────────────────────────────────────────────────────────
def test_regeln_arbeiten_gegen_den_kontext_ohne_solver():
    aufrufe: list = []

    class Fake:
        modell = Modell([Thema("A"), Thema("B")], [Person("P", ("A", "B")), Person("Q", ("A",))], slots(1))

        def termine(self, thema):
            return range(1)

        def teilnahme(self, person, thema, j):
            return (person, thema, j)

        def bedingung(self, terme, lo, hi, text, faktor=1.0):
            aufrufe.append(("bedingung", len(terme), lo, hi))

        def strafe(self, terme, text):
            aufrufe.append(("strafe", terme[0][0]))

        def abweichung(self, terme, ziel, text, faktor=1.0):
            aufrufe.append(("abweichung", len(terme), ziel, faktor))

    for name in ("verteilung", "rangfolge", "ausgleich"):
        STANDARD_REGISTRY.hole(name)().anwenden(Fake(), {})
    assert ("bedingung", 2, 1, None) in aufrufe and ("bedingung", 1, 1, None) in aufrufe  # P: A,B; Q: A
    assert ("strafe", -100) in aufrufe and ("strafe", -10) in aufrufe
    assert ("abweichung", 2, 1, AUSGLEICH_FAKTOR) in aufrufe  # Ziel: 2 Lehrkräfte / 2 Konferenzen = 1


# ── Zuordnung und Profil in der Sitzung ─────────────────────────────────────
ZEILEN = [
    ["Eins", "Anna", "", "Deutsch", "Sport", None, "Deutsch"],
    ["Zwei", "Ben", "", "Sport", "Deutsch", None, "Sport"],
    ["Drei", "Cem", "", "Deutsch", "Sport", None, None],
    ["Vier", "Dora", "", "Sport", "Deutsch", None, None],
]
EIN_SLOT = [["Tag", "Start", "Ende"], ["Sa", "09:00", "09:45"]]


def sitzung(tmp_path, einstellungen=None, zeilen=ZEILEN):
    s = Sitzung(einstellungen)
    blaetter = lehrer_mit_terminen(
        zeilen, ("Deutsch", "Sa", "09:00", "09:45"), ("Sport", "Sa", "09:00", "09:45")
    )
    s.lade(schreibe(tmp_path / "k.xlsx", blaetter))
    return s


def test_zuweisung_serialisierung():
    a = LehrerAenderung(zuweisung=("Sport", "Deutsch"))
    assert not a.leer() and LehrerAenderung.aus_dict(a.als_dict()).zuweisung == ("Sport", "Deutsch")
    assert LehrerAenderung.aus_dict({"zuweisung": "quatsch"}).zuweisung == ()
    assert LehrerAenderung.aus_dict({"zuweisung": ["A", 5, "", "A"]}).zuweisung == ("A",)


def test_auto_profil_folgt_der_datei(tmp_path):
    s = sitzung(tmp_path)
    assert s.profil == "auto" and s.wirksames_profil() == "verteilen"
    typen = {r.name: r.typ for r in s.regeln()}
    assert typen["verteilung"] == "hart" and typen["schwerpunkte"] == "aus"
    assert typen["rangfolge"] == "weich" and typen["ausgleich"] == "weich"


def test_profile_wechseln_die_regeln(tmp_path):
    s = sitzung(tmp_path)
    s.setze_profil("klassisch")
    assert {r.name: r.typ for r in s.regeln()}["schwerpunkte"] == "hart"
    assert {r.name: r.typ for r in s.regeln()}["verteilung"] == "aus"
    s.setze_profil("festtermine")
    assert {r.name: r.typ for r in s.regeln()}["schwerpunkte"] == "weich"
    s.setze_profil("auto")
    assert s.wirksames_profil() == "verteilen"
    assert set(PROFIL_NAMEN) == {"auto", "verteilen", "festtermine", "klassisch"}


def test_unbekanntes_profil(tmp_path):
    with pytest.raises(ModellFehler, match="Profil"):
        sitzung(tmp_path).setze_profil("quatsch")


def test_von_hand_gesetzte_regel_bleibt_beim_profilwechsel(tmp_path):
    s = sitzung(tmp_path)
    s.setze_regel("ausgleich", "aus", 1.0)
    s.setze_profil("klassisch")
    s.setze_profil("verteilen")
    assert {r.name: r.typ for r in s.regeln()}["ausgleich"] == "aus"


def test_profilwechsel_verwirft_den_plan(tmp_path):
    s = sitzung(tmp_path)
    s.planen()
    s.setze_profil("klassisch")
    assert s.plan is None


def test_profil_wird_gemerkt(tmp_path):
    speicher = tmp_path / "e.yaml"
    s = sitzung(tmp_path, YamlEinstellungen(speicher))
    s.setze_profil("klassisch")
    neu = Sitzung(YamlEinstellungen(speicher))
    neu.lade(tmp_path / "k.xlsx")
    assert neu.profil == "klassisch" and {r.name: r.typ for r in neu.regeln()}["schwerpunkte"] == "hart"


def test_lehrerliste_ohne_regelaenderung_planbar_im_selben_slot(tmp_path):
    s = sitzung(tmp_path)
    plan = s.planen()
    assert plan.status in ("optimal", "machbar")
    assert sorted(n for t in plan.termine for n in t.teilnehmer) == [
        "Anna Eins",
        "Ben Zwei",
        "Cem Drei",
        "Dora Vier",
    ]
    assert all(len(t.teilnehmer) == 2 for t in plan.termine)  # gleich groß
    assert "Anna Eins" in teil(plan)["Deutsch"] and "Ben Zwei" in teil(plan)["Sport"]  # Vorsitz gesetzt


def test_klassisches_profil_ist_im_selben_slot_nicht_planbar_und_der_tipp_hilft(tmp_path):
    s = sitzung(tmp_path)
    s.setze_profil("klassisch")
    plan = s.planen()
    assert plan.status == "kein_plan" and "schwerpunkte" in " ".join(plan.begruendung)
    assert s.tipp(plan) is not None and "Verteilen" in s.tipp(plan)
    s.setze_profil("auto")
    assert s.planen().status in ("optimal", "machbar") and s.tipp() is None


def test_tipp_nur_bei_hartem_schwerpunkte(tmp_path):
    s = sitzung(tmp_path)
    s.setze_profil("klassisch")
    plan = s.planen()
    s.setze_regel("schwerpunkte", "weich", 1.0)
    assert s.tipp(plan) is None  # die Regel ist schon weich


def test_ein_treffen_je_konferenz_im_profil_verteilen(tmp_path):
    s = sitzung(tmp_path)
    plan = s.planen()
    assert sorted(t.thema for t in plan.termine) == ["Deutsch", "Sport"]


def test_feste_zuweisung_wirkt_und_ueberlebt_das_neuladen(tmp_path):
    speicher = tmp_path / "e.yaml"
    s = sitzung(tmp_path, YamlEinstellungen(speicher))
    s.setze_konferenzen(["Cem Drei"], ["Deutsch", "Sport"])
    s.setze_zuweisung("Cem Drei", {"Sport"})
    assert s.markiert == ["Cem Drei"]
    assert "Cem Drei" in teil(s.planen())["Sport"]
    neu = Sitzung(YamlEinstellungen(speicher))
    neu.lade(tmp_path / "k.xlsx")
    assert neu.zuordnung.personen["Cem Drei"].zuweisung == ("Sport",)
    assert "Cem Drei" in teil(neu.planen())["Sport"]


def test_zuweisung_validiert_und_loest_sich(tmp_path):
    s = sitzung(tmp_path)
    with pytest.raises(ModellFehler, match="Unbekannte Konferenz"):
        s.setze_zuweisung("Cem Drei", {"Latein"})
    with pytest.raises(ModellFehler, match="Unbekannte Lehrkraft"):
        s.setze_zuweisung("Niemand", {"Sport"})
    s.setze_zuweisung("Cem Drei", {"Sport"})
    s.setze_zuweisung("Cem Drei", set())
    assert not s.zuordnung.personen.get("Cem Drei") or not s.zuordnung.personen["Cem Drei"].zuweisung


def test_zuweisung_ausserhalb_des_sets_ist_unmoeglich_mit_klarer_begruendung(tmp_path):
    zeilen = [*ZEILEN, ["Fünf", "Eva", "", "Deutsch", None, None, None]]
    s = sitzung(tmp_path, zeilen=zeilen)
    s.setze_zuweisung("Eva Fünf", {"Sport"})  # Sport ist nicht in Evas Set
    plan = s.planen()
    assert plan.status == "kein_plan" and "fixierung" in " ".join(plan.begruendung)
    s.setze_konferenzen(["Eva Fünf"], ["Deutsch", "Sport"])  # Set erweitern löst es
    assert s.planen().status in ("optimal", "machbar")


def test_selbst_gesetzte_regel_gilt_auch_im_profil_verteilen(tmp_path):
    s = sitzung(tmp_path)
    s.setze_regel("schwerpunkte", "hart", 1.0)
    assert s.planen().status == "kein_plan"  # der Nutzer hat „alle besuchen“ gewählt
    assert s.tipp() is not None
