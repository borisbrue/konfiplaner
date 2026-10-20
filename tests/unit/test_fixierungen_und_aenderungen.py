"""TST-0021 – Fixierungen im Solver und Änderungen in der Sitzung (CON-0015)."""

import pytest

from konfiplaner.anwendung import Sitzung
from konfiplaner.einstellungen import YamlEinstellungen
from konfiplaner.modell import Modell, ModellFehler, Person, Thema
from konfiplaner.planer import Fixierungen, PlanerOptionen
from konfiplaner.restriktionen import standard_konfiguration
from konfiplaner.restriktionen.basis import RegelEinstellung
from konfiplaner.solver import CpSatPlaner
from konfiplaner.zuordnung import LehrerAenderung, Zuordnung
from tests.helfer import slots
from tests.xlsx_helfer import lehrer_mit_terminen, schreibe

MI = ("Mi", "14:00", "15:00")
ZEILEN = [
    ["Eins", "Anna", "", "Deutsch", "Sport", "Kunst", "Deutsch"],
    ["Zwei", "Ben", "", "Sport", None, None, "Sport"],
    ["Drei", "Cem", "", "Kunst", None, None, "Kunst"],
    ["Vier", "Dora", "", "Deutsch", None, None, None],
    ["Fünf", "Eva", "", "Sport", "Deutsch", None, None],
    ["Sechs", "Finn", "", "Kunst", "Sport", None, None],
]


def sitzung(tmp_path, einstellungen=None):
    s = Sitzung(einstellungen)
    s.lade(
        schreibe(
            tmp_path / "k.xlsx",
            lehrer_mit_terminen(ZEILEN, ("Deutsch", *MI), ("Sport", "Mi", "15:00", "16:00"), ("Kunst", *MI)),
        )
    )
    return s


def teil(plan):
    return {t.thema: set(t.teilnehmer) for t in plan.termine}


# ── Solver ──────────────────────────────────────────────────────────────────
def plane(m, fix=None, konfig=None):
    return CpSatPlaner().planen(
        m, konfig or standard_konfiguration(), PlanerOptionen(zeitlimit_s=20), fixierungen=fix
    )


def modell():
    raster = slots(4)
    themen = [Thema("A", festtermine=(raster[0],)), Thema("B", festtermine=(raster[2],))]
    return Modell(
        themen,
        [Person("P", ("A", "B")), Person("Q", ("A",)), Person("R", ("A", "B")), Person("S", ("B",))],
        raster,
    )


def test_fixierungen_leer():
    assert Fixierungen().leer() and not Fixierungen({"P": {("A", 0): True}}).leer()


def test_feste_teilnahme_nein_wird_eingehalten():
    # R darf nicht an A teilnehmen, obwohl A ihre Konferenz ist: schwerpunkte (hart) ist dann nicht erfüllbar
    plan = plane(modell(), Fixierungen({"R": {("A", 0): False}}))
    assert plan.status == "kein_plan" and "fixierung" in " ".join(plan.begruendung)
    weich = standard_konfiguration()
    weich.einstellungen["schwerpunkte"] = RegelEinstellung("schwerpunkte", "weich", 1.0)
    plan = plane(modell(), Fixierungen({"R": {("A", 0): False}}), weich)
    assert plan.status in ("optimal", "machbar") and "R" not in teil(plan)["A"]


def test_feste_teilnahme_ja_wird_eingehalten():
    plan = plane(modell(), Fixierungen({"P": {("A", 0): True, ("B", 2): True}}))
    assert "P" in teil(plan)["A"] and "P" in teil(plan)["B"]


def test_unmoegliche_feste_teilnahme_nennt_die_regel_fixierung():
    # S ist nicht Mitglied von A und soll fest teilnehmen
    plan = plane(modell(), Fixierungen({"S": {("A", 0): True}}))
    assert plan.status == "kein_plan"
    assert "Regel fixierung: S nimmt an A" in " ".join(plan.begruendung)


def test_feste_teilnahme_an_gleichzeitigen_terminen_ist_kein_plan():
    raster = slots(2)
    m = Modell(
        [Thema("A", festtermine=(raster[0],)), Thema("B", festtermine=(raster[0],))],
        [Person("P", ("A", "B")), Person("Q", ("A",)), Person("R", ("B",))],
        raster,
    )
    plan = plane(m, Fixierungen({"P": {("A", 0): True, ("B", 0): True}}))
    text = " ".join(plan.begruendung)
    assert plan.status == "kein_plan" and "A" in text and "B" in text


def test_feste_startslots_bei_variablen_terminen():
    raster = slots(6)
    m = Modell([Thema("A", wichtigkeit=5)], [Person("P", ("A",))], raster)
    frei = plane(m)
    assert frei.termine[0].start_slot == 0  # ohne Fixierung liegt das wichtige Thema vorn
    fest = plane(m, Fixierungen(termine={"A": (3,)}))
    assert [t.start_slot for t in fest.termine] == [3]


def test_startslots_die_nicht_mehr_passen_werden_ignoriert():
    raster = slots(3)
    m = Modell([Thema("A")], [Person("P", ("A",))], raster)
    plan = plane(m, Fixierungen(termine={"A": (99,)}))
    assert plan.status in ("optimal", "machbar")


def test_mehr_bisherige_termine_als_geschaetzt():
    # 2 Personen, Mindestanzahl 2 -> geschätzt 1 Termin; der bisherige Plan hatte 2 Termine
    raster = slots(4)
    m = Modell([Thema("A", mindestanzahl=1)], [Person("P", ("A",)), Person("Q", ("A",))], raster)
    plan = plane(m, Fixierungen(termine={"A": (0, 2)}))
    assert sorted(t.start_slot for t in plan.termine) == [0, 2]


# ── Zustand und Persistenz ──────────────────────────────────────────────────
def test_zuordnung_rundreise_und_toleranz():
    z = Zuordnung("d.xlsx")
    z.aenderung("A").konferenzen = ("X", "Y")
    z.aenderung("A").nicht_verfuegbar = frozenset({("X", 0)})
    z.aenderung("B").fest = frozenset({("Y", 1)})
    z.vorsitz = {"X": "A", "Y": None}
    z.markiert = {"A"}
    assert Zuordnung.aus_dict(z.als_dict()).als_dict() == z.als_dict()
    kaputt = {
        "datei": 5,
        "personen": {"A": "x", "B": {"konferenzen": "y", "fest": [[1, 2], ["K", 0], "z"]}},
        "vorsitz": [],
        "markiert": "q",
    }
    k = Zuordnung.aus_dict(kaputt)
    assert (
        k.datei is None
        and k.personen["B"].fest == frozenset({("K", 0)})
        and k.vorsitz == {}
        and k.markiert == set()
    )
    assert Zuordnung.aus_dict("quatsch").leer() and Zuordnung.aus_dict(None).leer()


def test_leere_aenderung():
    assert LehrerAenderung().leer() and not LehrerAenderung(konferenzen=()).leer()


# ── Sitzung ─────────────────────────────────────────────────────────────────
def test_konferenzen_ersetzen_markiert(tmp_path):
    s = sitzung(tmp_path)
    s.setze_konferenzen(["Anna Eins"], ["Sport", "Deutsch"])
    a = {x.name: x for x in s.lehrkraefte()}["Anna Eins"]
    assert a.konferenzen == ("Sport", "Deutsch") and a.original == ("Deutsch", "Sport", "Kunst")
    assert a.geaendert and a.markiert and s.markiert == ["Anna Eins"]


def test_gleiche_konferenzen_aendern_nichts_und_markieren_nicht(tmp_path):
    s = sitzung(tmp_path)
    s.setze_konferenzen(["Anna Eins"], ["Deutsch", "Sport", "Kunst"])
    assert s.markiert == [] and not {x.name: x for x in s.lehrkraefte()}["Anna Eins"].geaendert


def test_aenderung_gilt_vor_der_auswahl(tmp_path):
    s = sitzung(tmp_path)
    s.waehle("Sport", False)
    s.setze_konferenzen(["Anna Eins"], ["Sport", "Deutsch"])
    assert {p.name: p.themen for p in s.modell().personen}["Anna Eins"] == ("Deutsch",)
    s.waehle("Sport", True)
    assert {p.name: p.themen for p in s.modell().personen}["Anna Eins"] == ("Sport", "Deutsch")


@pytest.mark.parametrize("konferenzen", [["Latein"], ["Deutsch", "Latein"]])
def test_unbekannte_konferenz_ist_ein_fehler(tmp_path, konferenzen):
    s = sitzung(tmp_path)
    with pytest.raises(ModellFehler, match="Unbekannte Konferenz"):
        s.setze_konferenzen(["Anna Eins"], konferenzen)
    assert s.markiert == []


def test_unbekannte_lehrkraft_ist_ein_fehler(tmp_path):
    with pytest.raises(ModellFehler, match="Unbekannte Lehrkraft"):
        sitzung(tmp_path).setze_konferenzen(["Niemand"], ["Sport"])


def test_sammelaenderung_hinzufuegen_am_ende_und_an_position(tmp_path):
    s = sitzung(tmp_path)
    s.aendere_konferenzen(["Ben Zwei", "Cem Drei"], "hinzufuegen", ["Deutsch"])
    wirksam = {x.name: x.konferenzen for x in s.lehrkraefte()}
    assert wirksam["Ben Zwei"] == ("Sport", "Deutsch") and wirksam["Cem Drei"] == ("Kunst", "Deutsch")
    s.aendere_konferenzen(["Ben Zwei"], "hinzufuegen", ["Kunst"], position=1)
    assert {x.name: x.konferenzen for x in s.lehrkraefte()}["Ben Zwei"] == ("Kunst", "Sport", "Deutsch")


def test_sammelaenderung_vorhandene_wird_nicht_doppelt(tmp_path):
    s = sitzung(tmp_path)
    s.aendere_konferenzen(["Anna Eins"], "hinzufuegen", ["Sport"])
    assert s.markiert == []


def test_sammelaenderung_entfernen_und_ersetzen(tmp_path):
    s = sitzung(tmp_path)
    s.aendere_konferenzen(["Anna Eins", "Eva Fünf"], "entfernen", ["Sport"])
    wirksam = {x.name: x.konferenzen for x in s.lehrkraefte()}
    assert wirksam["Anna Eins"] == ("Deutsch", "Kunst") and wirksam["Eva Fünf"] == ("Deutsch",)
    s.aendere_konferenzen(["Anna Eins", "Eva Fünf"], "ersetzen", ["Kunst", "Sport"])
    assert {x.name: x.konferenzen for x in s.lehrkraefte()}["Eva Fünf"] == ("Kunst", "Sport")
    with pytest.raises(ModellFehler, match="Aktion"):
        s.aendere_konferenzen(["Anna Eins"], "mischen", ["Sport"])


def test_vorsitz_wechseln_markiert_alten_und_neuen(tmp_path):
    s = sitzung(tmp_path)
    s.setze_vorsitz("Deutsch", "Eva Fünf")
    assert {k.name: k.vorsitz for k in s.konferenzen()}["Deutsch"] == "Eva Fünf"
    assert {t.name: t.vorsitz for t in s.modell().themen}["Deutsch"] == "Eva Fünf"
    assert s.markiert == ["Anna Eins", "Eva Fünf"]
    ansicht = {x.name: x for x in s.lehrkraefte()}
    assert ansicht["Eva Fünf"].vorsitz_von == ("Deutsch",) and ansicht["Anna Eins"].vorsitz_von == ()


def test_vorsitz_zurueck_auf_die_datei_und_keiner(tmp_path):
    s = sitzung(tmp_path)
    s.setze_vorsitz("Deutsch", "Eva Fünf")
    s.setze_vorsitz("Deutsch", "Anna Eins")
    assert "Deutsch" not in s.zuordnung.vorsitz
    s.setze_vorsitz("Deutsch", None)
    assert {t.name: t.vorsitz for t in s.modell().themen}["Deutsch"] is None


def test_vorsitz_auf_unbekannte_person(tmp_path):
    s = sitzung(tmp_path)
    with pytest.raises(ModellFehler, match="Unbekannte Lehrkraft"):
        s.setze_vorsitz("Deutsch", "Niemand")
    with pytest.raises(ModellFehler, match="Unbekannte Konferenz"):
        s.setze_vorsitz("Latein", "Anna Eins")


def test_nicht_verfuegbar_sperrt_die_slots_des_termins(tmp_path):
    s = sitzung(tmp_path)
    s.setze_nicht_verfuegbar("Anna Eins", {("Sport", 0)})
    m = s.modell()
    slot = m.fest_bloecke("Sport")[0][0]
    assert not m.verfuegbar("Anna Eins", slot) and m.verfuegbar("Ben Zwei", slot)
    assert m.verfuegbar("Anna Eins", m.fest_bloecke("Deutsch")[0][0])


def test_nicht_verfuegbar_mit_ungueltigem_termin(tmp_path):
    with pytest.raises(ModellFehler, match="keinen Termin"):
        sitzung(tmp_path).setze_nicht_verfuegbar("Anna Eins", {("Sport", 5)})


def test_fest_verlangt_eine_konferenz_der_lehrkraft(tmp_path):
    s = sitzung(tmp_path)
    with pytest.raises(ModellFehler, match="keine Konferenz von"):
        s.setze_fest("Ben Zwei", {("Deutsch", 0)})
    s.waehle("Kunst", False)
    with pytest.raises(ModellFehler, match="abgewählt"):
        s.setze_fest("Anna Eins", {("Kunst", 0)})


def test_zuruecksetzen_ohne_neuplanung_entmarkiert(tmp_path):
    s = sitzung(tmp_path)
    s.planen()
    s.setze_konferenzen(["Anna Eins"], ["Sport"])
    s.zuruecksetzen("Anna Eins")
    a = {x.name: x for x in s.lehrkraefte()}["Anna Eins"]
    assert a.konferenzen == ("Deutsch", "Sport", "Kunst") and not a.geaendert and not a.markiert


def test_zuruecksetzen_nach_neuplanung_markiert_wieder(tmp_path):
    s = sitzung(tmp_path)
    s.planen()
    s.setze_konferenzen(["Dora Vier"], ["Sport"])
    s.teil_neu_planen()
    s.zuruecksetzen("Dora Vier")
    assert s.markiert == ["Dora Vier"]  # der Plan enthält noch die verworfene Änderung


def test_zuruecksetzen_stellt_vorsitz_wieder_her(tmp_path):
    s = sitzung(tmp_path)
    s.setze_vorsitz("Deutsch", "Eva Fünf")
    s.zuruecksetzen("Eva Fünf")
    assert {k.name: k.vorsitz for k in s.konferenzen()}["Deutsch"] == "Anna Eins"


def test_aenderungen_ueberstehen_das_neuladen_derselben_datei(tmp_path):
    speicher = tmp_path / "e.yaml"
    s = sitzung(tmp_path, YamlEinstellungen(speicher))
    s.setze_konferenzen(["Anna Eins"], ["Sport"])
    s.setze_vorsitz("Deutsch", "Eva Fünf")
    s.setze_nicht_verfuegbar("Ben Zwei", {("Sport", 0)})
    neu = Sitzung(YamlEinstellungen(speicher))
    neu.lade(tmp_path / "k.xlsx")
    a = {x.name: x for x in neu.lehrkraefte()}
    assert a["Anna Eins"].konferenzen == ("Sport",) and a["Ben Zwei"].nicht_verfuegbar == (("Sport", 0),)
    assert {k.name: k.vorsitz for k in neu.konferenzen()}["Deutsch"] == "Eva Fünf"
    assert set(neu.markiert) == {"Anna Eins", "Eva Fünf", "Ben Zwei"}


def test_aenderungen_gelten_nicht_fuer_eine_andere_datei(tmp_path):
    speicher = tmp_path / "e.yaml"
    s = sitzung(tmp_path, YamlEinstellungen(speicher))
    s.setze_konferenzen(["Anna Eins"], ["Sport"])
    anders = schreibe(
        tmp_path / "anders.xlsx",
        lehrer_mit_terminen(ZEILEN, ("Deutsch", *MI), ("Sport", *MI), ("Kunst", *MI)),
    )
    neu = Sitzung(YamlEinstellungen(speicher))
    neu.lade(anders)
    assert {x.name: x for x in neu.lehrkraefte()}["Anna Eins"].konferenzen == ("Deutsch", "Sport", "Kunst")
    assert neu.markiert == []


def test_neuladen_behaelt_die_aenderungen(tmp_path):
    s = sitzung(tmp_path)
    s.setze_konferenzen(["Anna Eins"], ["Sport"])
    s.neu_laden()
    assert {x.name: x for x in s.lehrkraefte()}["Anna Eins"].konferenzen == ("Sport",) and s.markiert == [
        "Anna Eins"
    ]


def test_unbekannte_gespeicherte_namen_werden_ignoriert(tmp_path):
    speicher = tmp_path / "e.yaml"
    pfad = tmp_path / "k.xlsx"
    sitzung(tmp_path, YamlEinstellungen(speicher))
    speicher.write_text(
        f"zuordnung:\n  datei: {pfad}\n  personen:\n    Niemand: {{konferenzen: [Sport]}}\n    Anna Eins: {{konferenzen: [Latein, Sport]}}\n  markiert: [Niemand]\n",
        encoding="utf-8",
    )
    neu = Sitzung(YamlEinstellungen(speicher))
    neu.lade(pfad)
    assert {x.name: x.konferenzen for x in neu.lehrkraefte()}["Anna Eins"] == ("Sport",)
    assert neu.markiert == [] and neu.planbar


# ── Teilneuplanung ──────────────────────────────────────────────────────────
def test_teilneuplanung_aendert_nur_markierte(tmp_path):
    s = sitzung(tmp_path)
    vorher = teil(s.planen())
    s.setze_konferenzen(["Dora Vier"], ["Sport"])
    plan = s.teil_neu_planen()
    nachher = teil(plan)
    assert plan.status in ("optimal", "machbar") and s.markiert == []
    geaendert = {n for k in vorher for n in vorher[k] ^ nachher[k]}
    assert (
        geaendert == {"Dora Vier"}
        and "Dora Vier" in nachher["Sport"]
        and "Dora Vier" not in nachher["Deutsch"]
    )


def test_teilneuplanung_ohne_plan_plant_vollstaendig(tmp_path):
    s = sitzung(tmp_path)
    s.setze_konferenzen(["Dora Vier"], ["Sport"])
    plan = s.teil_neu_planen()
    assert plan.status in ("optimal", "machbar") and s.plan is plan and s.markiert == []


def test_teilneuplanung_ohne_markierung_plant_vollstaendig(tmp_path):
    s = sitzung(tmp_path)
    s.planen()
    assert s.teil_neu_planen().status in ("optimal", "machbar")


def test_teilneuplanung_unloesbar_laesst_plan_und_markierung(tmp_path):
    s = sitzung(tmp_path)
    s.planen()
    alt = s.plan
    # Ben ist der Einzige mit Sport als erster Konferenz und Vorsitz; ohne ihn fehlt Sport der Vorsitz-Teilnehmer
    s.setze_nicht_verfuegbar("Ben Zwei", {("Sport", 0)})
    plan = s.teil_neu_planen()
    assert plan.status == "kein_plan" and s.plan is alt and s.markiert == ["Ben Zwei"]
    assert "Ben Zwei" in " ".join(plan.begruendung)


def test_vorsitzwechsel_bei_teilneuplanung(tmp_path):
    s = sitzung(tmp_path)
    s.planen()
    s.setze_vorsitz("Deutsch", "Eva Fünf")
    plan = s.teil_neu_planen()
    assert plan.status in ("optimal", "machbar") and "Eva Fünf" in teil(plan)["Deutsch"]


def test_feste_teilnahme_gilt_in_jedem_plan(tmp_path):
    zeilen = [
        ["Eins", "Anna", "", "Deutsch", "Sport", None, None],
        ["Zwei", "Ben", "", "Sport", None, None, "Sport"],
        ["Drei", "Cem", "", "Deutsch", None, None, "Deutsch"],
    ]
    s = Sitzung()
    s.lade(schreibe(tmp_path / "f.xlsx", lehrer_mit_terminen(zeilen, ("Deutsch", *MI), ("Sport", *MI))))
    assert "Anna Eins" in teil(s.planen())["Deutsch"]  # Rang 1
    s.setze_fest("Anna Eins", {("Sport", 0)})
    plan = s.planen()
    assert plan.status in ("optimal", "machbar")
    assert "Anna Eins" in teil(plan)["Sport"] and "Anna Eins" not in teil(plan)["Deutsch"]


def test_feste_teilnahme_an_zwei_gleichzeitigen_termine_ist_kein_plan(tmp_path):
    s = sitzung(tmp_path)
    s.setze_fest("Anna Eins", {("Deutsch", 0), ("Kunst", 0)})  # beide Mi 14:00–15:00
    plan = s.planen()
    assert (
        plan.status == "kein_plan"
        and "Deutsch" in " ".join(plan.begruendung)
        and "Kunst" in " ".join(plan.begruendung)
    )
    assert s.markiert == ["Anna Eins"]  # nur erfolgreiche Planung löscht Markierungen


def test_alles_neu_planen_loescht_markierungen(tmp_path):
    s = sitzung(tmp_path)
    s.setze_konferenzen(["Anna Eins"], ["Sport"])
    s.planen()
    assert s.markiert == []


def test_konferenz_ohne_festtermine_behaelt_startslots(tmp_path):
    zeilen = [
        ["Eins", "Anna", "", "Deutsch", None, None, "Deutsch"],
        ["Zwei", "Ben", "", "Deutsch", None, None, None],
        ["Drei", "Cem", "", "Deutsch", None, None, None],
    ]
    blaetter = lehrer_mit_terminen(zeilen, ("Deutsch", *MI))
    del blaetter["Konferenzen"]
    blaetter["Zeitslots"] = [
        ["Tag", "Start", "Ende"],
        *[["Mi", f"{14 + i}:00", f"{15 + i}:00"] for i in range(5)],
    ]
    s = Sitzung()
    s.lade(schreibe(tmp_path / "v.xlsx", blaetter))
    s.setze_thema(0, wichtigkeit=5)
    erster = s.planen()
    s.setze_konferenzen(["Cem Drei"], ["Deutsch"])  # keine echte Änderung
    s.zuordnung.markiert.add("Cem Drei")
    starts = sorted(t.start_slot for t in erster.termine)
    plan = s.teil_neu_planen()
    assert sorted(t.start_slot for t in plan.termine) == starts


def test_lehrkraefte_zeigen_teilnahmen_aus_dem_plan(tmp_path):
    s = sitzung(tmp_path)
    s.planen()
    a = {x.name: x for x in s.lehrkraefte()}["Anna Eins"]
    assert "Deutsch (Mi 14:00–15:00)" in a.teilnahmen
    assert s.termin_text("Sport", 0) == "Sport: Mi 15:00–16:00"
