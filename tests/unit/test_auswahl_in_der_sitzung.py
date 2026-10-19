"""TST-0019 – Auswahl der Konferenzen in der Sitzung (CON-0014)."""

import pytest

from konfiplaner.anwendung import Sitzung
from konfiplaner.einstellungen import YamlEinstellungen
from konfiplaner.modell import ModellFehler
from tests.xlsx_helfer import lehrer_mit_terminen, schreibe

MI = ("Mi", "14:00", "15:00")
ZEILEN = [
    ["Eins", "Anna", "", "Deutsch", "Sport", "Kunst", "Deutsch"],
    ["Zwei", "Ben", "", "Sport", None, None, "Sport"],
    ["Drei", "Cem", "", "Kunst", None, None, "Kunst"],
    ["Vier", "Dora", "", None, None, None, None],
    ["Fünf", "Eva", "", "Sport", "Deutsch", None, None],
]


def sitzung(tmp_path, einstellungen=None):
    s = Sitzung(einstellungen)
    s.lade(
        schreibe(
            tmp_path / "k.xlsx",
            lehrer_mit_terminen(ZEILEN, ("Deutsch", *MI), ("Sport", *MI), ("Kunst", "Mi", "15:00", "16:00")),
        )
    )
    return s


def themen(m):
    return {p.name: p.themen for p in m.personen}


def test_standard_alle_ausgewaehlt(tmp_path):
    s = sitzung(tmp_path)
    ansicht = {k.name: k for k in s.konferenzen()}
    assert all(k.ausgewaehlt for k in ansicht.values()) and not s.abgewaehlt
    assert (ansicht["Sport"].mitglieder, ansicht["Sport"].vorsitz, ansicht["Sport"].termine) == (
        3,
        "Ben Zwei",
        1,
    )
    assert [t.name for t in s.modell().themen] == ["Deutsch", "Sport", "Kunst"]


def test_abgewaehlt_entfaellt_und_der_rest_rueckt_nach(tmp_path):
    s = sitzung(tmp_path)
    s.waehle("Deutsch", False)
    m = s.modell()
    assert [t.name for t in m.themen] == ["Sport", "Kunst"]
    assert themen(m)["Anna Eins"] == ("Sport", "Kunst")  # Sport ist jetzt die erste Konferenz
    assert themen(m)["Eva Fünf"] == ("Sport",)


def test_reihenfolge_der_uebrigen_bleibt(tmp_path):
    s = sitzung(tmp_path)
    s.waehle("Sport", False)
    assert themen(s.modell())["Anna Eins"] == ("Deutsch", "Kunst")


def test_abgewaehlte_konferenz_hat_im_modell_keinen_vorsitz_und_danach_wieder(tmp_path):
    s = sitzung(tmp_path)
    s.waehle("Deutsch", False)
    assert "Deutsch" not in {t.name for t in s.modell().themen}
    assert {t.name: t.vorsitz for t in s.themen}["Deutsch"] == "Anna Eins"  # Daten bleiben
    s.waehle("Deutsch", True)
    assert {t.name: t.vorsitz for t in s.modell().themen}["Deutsch"] == "Anna Eins"


def test_neu_zuordnen_und_ohne_konferenz_sind_getrennt(tmp_path):
    s = sitzung(tmp_path)
    assert s.neu_zuordnen == [] and s.ergebnis.ohne_konferenz == ["Dora Vier"]
    s.waehle("Kunst", False)
    assert s.neu_zuordnen == ["Cem Drei"]
    assert s.ergebnis.ohne_konferenz == ["Dora Vier"]
    assert not set(s.neu_zuordnen) & set(s.ergebnis.ohne_konferenz)


def test_wiederauswahl_leert_neu_zuordnen(tmp_path):
    s = sitzung(tmp_path)
    s.waehle("Kunst", False)
    s.waehle("Kunst", True)
    assert s.neu_zuordnen == []


def test_nichts_ausgewaehlt_ist_nicht_planbar(tmp_path):
    s = sitzung(tmp_path)
    s.waehle_alle(False)
    assert not s.planbar and "Keine Konferenz ausgewählt" in s.planungshindernisse()
    with pytest.raises(ModellFehler):
        s.planen()
    s.waehle_alle(True)
    assert s.planbar and not s.abgewaehlt


def test_unbekannte_konferenz_wird_abgelehnt(tmp_path):
    with pytest.raises(ModellFehler, match="Unbekannte Konferenz"):
        sitzung(tmp_path).waehle("Latein", False)


def test_aenderung_verwirft_den_plan(tmp_path):
    s = sitzung(tmp_path)
    s.planen()
    assert s.plan is not None
    s.waehle("Sport", False)
    assert s.plan is None and s.tabellen() == {}


def test_plan_enthaelt_abgewaehlte_konferenz_nirgends(tmp_path):
    s = sitzung(tmp_path)
    s.waehle("Sport", False)
    plan = s.planen()
    assert plan.status in ("optimal", "machbar")
    assert "Sport" not in {t.thema for t in plan.termine}
    assert not any("Sport" in v.text for v in plan.verstoesse)
    assert not any("Sport" in z for tab in s.tabellen().values() for zeile in tab for z in map(str, zeile))


def test_warnungen_fuer_neu_zuordnen_und_ohne_konferenz(tmp_path):
    s = sitzung(tmp_path)
    s.waehle("Kunst", False)
    plan = s.planen()
    assert "Cem Drei hat durch die Auswahl keine Konferenz" in plan.warnungen
    assert "Dora Vier hat keine Konferenz" in plan.warnungen
    assert ["Warnung", "Cem Drei hat durch die Auswahl keine Konferenz"] in s.tabellen()["Hinweise"]


def test_abgewaehlte_hauptkonferenz_wird_nicht_mehr_referenziert(tmp_path):
    kopf = ["Konferenz", "Tag", "Start", "Ende", "Hauptkonferenz"]
    s = Sitzung()
    s.lade(
        schreibe(
            tmp_path / "h.xlsx",
            lehrer_mit_terminen(
                ZEILEN,
                ("Deutsch", "Mi", "13:00", "14:00", None),
                ("Sport", *MI, "Deutsch"),
                ("Kunst", "Mi", "15:00", "16:00", None),
                kopf=kopf,
            ),
        )
    )
    s.waehle("Deutsch", False)
    assert {t.name: t.haupt for t in s.modell().themen}["Sport"] is None
    assert s.planen().status in ("optimal", "machbar")


def test_auswahl_wird_gemerkt_und_unbekannte_ignoriert(tmp_path):
    speicher = tmp_path / "e.yaml"
    s = sitzung(tmp_path, YamlEinstellungen(speicher))
    s.waehle("Sport", False)
    neu = Sitzung(YamlEinstellungen(speicher))
    neu.lade(tmp_path / "k.xlsx")
    assert {k.name: k.ausgewaehlt for k in neu.konferenzen()} == {
        "Deutsch": True,
        "Sport": False,
        "Kunst": True,
    }
    speicher.write_text("abgewaehlte_konferenzen: [Latein, Sport]\n", encoding="utf-8")
    dritte = Sitzung(YamlEinstellungen(speicher))
    dritte.lade(tmp_path / "k.xlsx")
    assert [k.name for k in dritte.konferenzen() if not k.ausgewaehlt] == ["Sport"]
    assert dritte.planbar


def test_kaputte_gespeicherte_auswahl_wird_ignoriert(tmp_path):
    speicher = tmp_path / "e.yaml"
    speicher.write_text("abgewaehlte_konferenzen: quatsch\n", encoding="utf-8")
    assert Sitzung(YamlEinstellungen(speicher)).abgewaehlt == set()


def test_auswahl_laesst_themenwerte_unberuehrt(tmp_path):
    s = sitzung(tmp_path)
    s.setze_thema(0, mindestanzahl=2)
    s.waehle("Deutsch", False)
    s.waehle("Deutsch", True)
    assert s.themen[0].mindestanzahl == 2
