"""TST-0006 – Restriktions-Schnittstelle (CON-0006)."""

import pytest

from konfiplaner.modell import Thema
from konfiplaner.planer import PlanerOptionen
from konfiplaner.restriktionen import (
    STANDARD_REGISTRY,
    Konfiguration,
    KonfigurationsFehler,
    RegistrierungsFehler,
    Registry,
    Restriktion,
    standard_konfiguration,
)
from konfiplaner.restriktionen.basis import RegelEinstellung
from konfiplaner.solver import CpSatPlaner
from tests.helfer import NichtZusammen, mit_regeln, modell, registry_mit_plugins

PAAR = {"person_a": "Anna", "person_b": "Ben"}


def plane(m, konfig):
    return CpSatPlaner(registry_mit_plugins()).planen(m, konfig, PlanerOptionen(zeitlimit_s=30))


def personen():
    return modell([Thema("A"), Thema("B")], [("Anna", "A", "B"), ("Ben", "A", "B")], 4)


def test_neue_regel_per_dekorator():
    reg = STANDARD_REGISTRY.kopie()

    @reg.registriere
    class Neu(Restriktion):
        name = "neu"

    assert "neu" in reg and "neu" not in STANDARD_REGISTRY


def test_neue_regel_wirkt_im_plan():
    plan = plane(personen(), mit_regeln(RegelEinstellung("nicht_zusammen", "hart", parameter=PAAR)))
    assert plan.status in ("optimal", "machbar")
    for t in plan.termine:
        assert not {"Anna", "Ben"} <= set(t.teilnehmer)


def test_entry_point_registrierung(monkeypatch):
    class EP:
        def load(self):
            return NichtZusammen

    monkeypatch.setattr("konfiplaner.restriktionen.basis.metadata.entry_points", lambda group: [EP()])
    reg = Registry()
    reg.lade_entry_points()
    assert reg.hole("nicht_zusammen") is NichtZusammen


def test_grundregel_deaktivieren_akzeptiert_ueberschneidung():
    # eine Person, zwei Themen, nur ein Slot: nur ohne Überschneidungsregel lösbar
    m = modell([Thema("A"), Thema("B")], [("P", "A", "B")], 1)
    assert plane(m, mit_regeln()).status == "kein_plan"
    plan = plane(m, mit_regeln(keine_ueberschneidung=("aus", 1)))
    assert plan.status in ("optimal", "machbar")
    assert not [v for v in plan.verstoesse if v.restriktion == "keine_ueberschneidung"]


def test_gewicht_entscheidet_bei_konflikt():
    # P1 und P2 können je nur in Slot 0 (beide Themen) – nur eine der beiden Teilnahmen ist erfüllbar
    m = modell([Thema("A"), Thema("B")], [("P1", "A", "B"), ("P2", "A", "B")], 3, {"P1": {0}, "P2": {0}})
    schwer = mit_regeln(RegelEinstellung("schwerpunkte", "weich", 5.0))
    plan = plane(m, schwer)
    assert plan.status in ("optimal", "machbar")
    assert all(v.restriktion == "schwerpunkte" for v in plan.verstoesse)


def test_gleiche_konfigurationsform_fuer_grund_und_plugin_regel():
    reg = registry_mit_plugins()
    k = Konfiguration.aus_dict(
        {
            "restriktionen": {
                "mindestanzahl": {"typ": "hart"},
                "nicht_zusammen": {"typ": "weich", "gewicht": 2, "parameter": PAAR},
            }
        },
        reg,
    )
    assert set(k.einstellungen) == {"mindestanzahl", "nicht_zusammen"}


def test_unbekannte_regel_vor_dem_solverlauf():
    k = standard_konfiguration()
    k.einstellungen["gibt_es_nicht"] = RegelEinstellung("gibt_es_nicht", "hart")
    with pytest.raises(KonfigurationsFehler, match="gibt_es_nicht"):
        plane(personen(), k)


@pytest.mark.parametrize(
    "parameter,meldung",
    [
        ({"person_a": "Anna"}, "person_b"),
        ({"person_a": "Anna", "person_b": 5}, "person_b"),
        ({**PAAR, "extra": 1}, "extra"),
    ],
)
def test_fehlerhafte_parameter(parameter, meldung):
    k = mit_regeln(RegelEinstellung("nicht_zusammen", "hart", parameter=parameter))
    with pytest.raises(KonfigurationsFehler, match=meldung) as e:
        plane(personen(), k)
    assert e.value.regel == "nicht_zusammen"


def test_doppelter_regelname_bei_registrierung():
    reg = registry_mit_plugins()
    with pytest.raises(RegistrierungsFehler, match="nicht_zusammen"):
        reg.registriere(NichtZusammen)


def test_weiche_regel_ohne_gewicht_hat_gewicht_eins():
    k = Konfiguration.aus_dict(
        {"restriktionen": {"nicht_zusammen": {"typ": "weich", "parameter": PAAR}}}, registry_mit_plugins()
    )
    assert k.einstellungen["nicht_zusammen"].gewicht == 1.0


def test_wichtigkeit_kennt_nur_weich_oder_aus():
    with pytest.raises(KonfigurationsFehler, match="wichtigkeit"):
        Konfiguration.aus_dict({"restriktionen": {"wichtigkeit": {"typ": "hart"}}}, STANDARD_REGISTRY)


def test_regeln_arbeiten_nur_gegen_den_abstrakten_kontext():
    """Eine Grundregel läuft gegen einen Fake-Kontext, ohne dass OR-Tools beteiligt ist."""
    aufrufe = []

    class Fake:
        modell = modell([Thema("A", mindestanzahl=2)], [("P", "A", "A2")][:0], 2)

        def termine(self, thema):
            return range(1)

        def aktiv(self, thema, j):
            return ("aktiv", thema, j)

        def bedingung(self, terme, untergrenze, obergrenze, text):
            aufrufe.append((terme, untergrenze, obergrenze, text))

    STANDARD_REGISTRY.hole("themenabdeckung")().anwenden(Fake(), {})
    assert aufrufe == [([(1, ("aktiv", "A", 0))], 1, None, "Thema A findet nicht statt")]
