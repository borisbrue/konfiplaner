"""TST-0012 – Vorsitz in der Planung (CON-0011). Die Testnamen folgen den Szenarien der .feature-Datei."""

import dataclasses

from konfiplaner.modell import Modell, Thema
from konfiplaner.planer import PlanerOptionen
from konfiplaner.restriktionen import standard_konfiguration
from konfiplaner.restriktionen.basis import RegelEinstellung
from konfiplaner.solver import CpSatPlaner
from tests.helfer import mit_regeln, modell


def plane(m: Modell, konfig=None):
    return CpSatPlaner().planen(m, konfig or mit_regeln(), PlanerOptionen(zeitlimit_s=30))


def termine(plan, thema):
    return [t for t in plan.termine if t.thema == thema]


def leiter(m: Modell, thema: str, name: str) -> Modell:
    """Setzt `name` als Vorsitz von `thema`."""
    themen = [dataclasses.replace(t, vorsitz=name) if t.name == thema else t for t in m.themen]
    return Modell(themen, m.personen, m.zeitslots, m.verfuegbarkeit)


def basis(**kw) -> Modell:
    # Meier hat Abendmahl und Gebet als Schwerpunkte, Taufe leiten ist zusätzlich
    th = [
        Thema("Taufe", mindestanzahl=2),
        Thema("Abendmahl", mindestanzahl=1),
        Thema("Gebet", mindestanzahl=1),
    ]
    pe = [("Meier", "Abendmahl", "Gebet"), ("Anna", "Taufe", "Abendmahl"), ("Ben", "Taufe", "Gebet")]
    return modell(th, pe, 6, **kw)


def test_vorsitz_ist_im_termin_auch_ohne_schwerpunkt():
    plan = plane(leiter(basis(), "Taufe", "Meier"))
    assert plan.status in ("optimal", "machbar")
    assert termine(plan, "Taufe") and all("Meier" in t.teilnehmer for t in termine(plan, "Taufe"))


def test_vorsitz_zaehlt_zur_mindestanzahl():
    # Taufe: Mindestanzahl 3, nur Anna und Ben haben den Schwerpunkt, der Vorsitz Meier ist der Dritte
    m = leiter(basis(), "Taufe", "Meier")
    m.themen[0] = dataclasses.replace(m.themen[0], mindestanzahl=3)
    t = termine(plane(m), "Taufe")
    assert len(t) == 1 and set(t[0].teilnehmer) == {"Anna", "Ben", "Meier"}


def test_ohne_vorsitz_reichen_die_schwerpunkt_personen_nicht_fuer_mindestanzahl_3():
    m = basis()
    m.themen[0] = dataclasses.replace(m.themen[0], mindestanzahl=3)
    assert plane(m).status == "kein_plan"


def test_vorsitz_in_allen_terminen_eines_themas():
    # Taufe braucht zwei Termine (Anna und Ben nie gleichzeitig verfügbar), Meier leitet beide
    verf = {"Anna": {0, 1}, "Ben": {2, 3}}
    m = leiter(basis(verfuegbar=verf), "Taufe", "Meier")
    m.themen[0] = dataclasses.replace(m.themen[0], mindestanzahl=2)
    plan = plane(m)
    taufe = termine(plan, "Taufe")
    assert plan.status in ("optimal", "machbar") and len(taufe) == 2
    assert all("Meier" in t.teilnehmer for t in taufe)
    assert len({t.start_slot for t in taufe}) == 2


def test_vorsitz_mit_schwerpunkt_im_selben_thema():
    th = [Thema("Taufe", mindestanzahl=2, vorsitz="Anna"), Thema("Gebet")]
    m = modell(th, [("Anna", "Taufe", "Gebet"), ("Ben", "Taufe", "Gebet")], 4)
    plan = plane(m)
    assert plan.status in ("optimal", "machbar") and not plan.verstoesse
    assert [t.teilnehmer.count("Anna") for t in termine(plan, "Taufe")] == [1]


def test_keine_ueberschneidung_fuer_den_vorsitz():
    plan = plane(leiter(basis(), "Taufe", "Meier"))
    belegt = [(t.start_slot, t.start_slot + t.anzahl_slots) for t in plan.termine if "Meier" in t.teilnehmer]
    assert (
        len(belegt) == 3 and len({b[0] for b in belegt}) == 3
    )  # Taufe, Abendmahl, Gebet in verschiedenen Slots


def test_vorsitz_nicht_verfuegbar_ist_kein_plan_mit_begruendung():
    # Meier kann nur in Slot 0 und muss dort schon seine beiden Schwerpunkte haben
    m = leiter(basis(verfuegbar={"Meier": {0}}), "Taufe", "Meier")
    plan = plane(m)
    assert plan.status == "kein_plan"
    text = " ".join(plan.begruendung)
    assert "Thema Taufe" in text or "Taufe" in text
    assert "verfuegbarkeit" in text or "vorsitz" in text


def test_begruendung_nennt_die_regel_vorsitz_wenn_nur_sie_kollidiert():
    # Ohne Schwerpunkt-Zwang bleibt als Konflikt nur: Vorsitz ist nicht verfügbar, Termin muss aber stattfinden
    m = leiter(basis(verfuegbar={"Meier": {0}}), "Taufe", "Meier")
    konfig = mit_regeln(schwerpunkte=("aus", 1), keine_ueberschneidung=("aus", 1))
    m = Modell(m.themen, m.personen, m.zeitslots, {"Meier": set()})
    plan = plane(m, konfig)
    assert plan.status == "kein_plan"
    assert "Regel vorsitz" in " ".join(plan.begruendung) and "Taufe" in " ".join(plan.begruendung)


def test_vorsitz_als_weiche_regel():
    m = leiter(basis(verfuegbar={"Meier": {0}}), "Taufe", "Meier")
    # Meier hat nur einen Slot: Schwerpunkte (Gewicht 5) gehen vor dem Vorsitz (Gewicht 1)
    konfig = mit_regeln(
        RegelEinstellung("vorsitz", "weich", 1.0),
        schwerpunkte=("weich", 5),
        keine_ueberschneidung=("hart", 1),
    )
    plan = plane(m, konfig)
    assert plan.status in ("optimal", "machbar")
    assert any(v.restriktion == "vorsitz" for v in plan.verstoesse)


def test_vorsitz_ausgeschaltet_ist_nicht_zwingend():
    m = leiter(basis(), "Taufe", "Meier")
    plan = plane(m, mit_regeln(vorsitz=("aus", 1)))
    assert plan.status in ("optimal", "machbar")
    # Ohne die Regel gibt es keinen Grund, dass Meier in der Taufe ist (sie ist kein Schwerpunkt-Teilnehmer)
    assert all("Meier" not in t.teilnehmer for t in termine(plan, "Taufe"))
    assert not any(v.restriktion == "vorsitz" for v in plan.verstoesse)


def test_vorsitz_ist_grundregel_mit_standard_hart():
    e = standard_konfiguration().einstellungen["vorsitz"]
    assert e.typ == "hart"
