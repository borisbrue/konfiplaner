"""Tagesplan für die Einladung zu einer Fortbildung (SPEC-0014)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, time
from typing import Any

ZEITARTEN = ("bereich", "ab", "um")
BLOCKARTEN = ("frei", "konferenzen")
WOCHENTAGE = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")


def _uhr(t: time) -> str:
    return f"{t.hour}.{t.minute:02d}"


def _zeit_aus_text(text: Any) -> time | None:
    try:
        stunde, minute = str(text).split(":")
        return time(int(stunde), int(minute))
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True)
class Block:
    """Eine Zeile der Ablauftabelle."""

    beginn: time
    ende: time | None = None
    zeitart: str = "bereich"
    titel: str = ""
    inhalt: str = ""
    wer: str = ""
    art: str = "frei"

    @property
    def zeit_text(self) -> str:
        """„8.30 – 8.40 Uhr“, „ab 8.00 Uhr“ oder „15.00 Uhr“."""
        if self.zeitart == "bereich" and self.ende is not None:
            return f"{_uhr(self.beginn)} – {_uhr(self.ende)} Uhr"
        if self.zeitart == "ab":
            return f"ab {_uhr(self.beginn)} Uhr"
        return f"{_uhr(self.beginn)} Uhr"

    def als_dict(self) -> dict[str, Any]:
        return {
            "beginn": self.beginn.strftime("%H:%M"),
            "ende": self.ende.strftime("%H:%M") if self.ende else None,
            "zeitart": self.zeitart,
            "titel": self.titel,
            "inhalt": self.inhalt,
            "wer": self.wer,
            "art": self.art,
        }

    @classmethod
    def aus_dict(cls, d: dict[str, Any]) -> Block | None:
        beginn = _zeit_aus_text(d.get("beginn"))
        if beginn is None:
            return None
        zeitart = d.get("zeitart") if d.get("zeitart") in ZEITARTEN else "bereich"
        art = d.get("art") if d.get("art") in BLOCKARTEN else "frei"
        return cls(
            beginn=beginn,
            ende=_zeit_aus_text(d.get("ende")) if d.get("ende") else None,
            zeitart=zeitart,
            titel=str(d.get("titel") or ""),
            inhalt=str(d.get("inhalt") or ""),
            wer=str(d.get("wer") or ""),
            art=art,
        )


@dataclass(frozen=True)
class Pruefhinweis:
    block: int  # Index in `Tagesplan.bloecke`
    text: str
    fehler: bool  # Fehler verhindern den Export, Warnungen nicht


def standard_bloecke() -> list[Block]:
    return [
        Block(time(8, 0), None, "ab", "Stehkaffee im Foyer"),
        Block(time(8, 30), time(8, 40), "bereich", "Begrüßung", "Organisation", "Schulleitung"),
        Block(time(8, 40), time(9, 30), "bereich", "Einstieg", "", "Alle"),
        Block(time(9, 30), time(9, 45), "bereich", "Kaffeepause"),
        Block(time(9, 45), time(12, 0), "bereich", "Arbeit in den Fachkonferenzen", "", "", "konferenzen"),
        Block(time(12, 0), time(13, 0), "bereich", "Mittagspause", "Gemeinsames Mittagessen"),
        Block(time(13, 0), time(14, 30), "bereich", "Gruppenarbeit"),
        Block(time(14, 30), time(15, 0), "bereich", "Austausch in den Fachkonferenzen"),
        Block(time(15, 0), None, "um", "Ende der Veranstaltung"),
    ]


@dataclass(frozen=True)
class Tagesplan:
    datum: date | None = None
    titel: str = "Schulinterne Lehrkräftefortbildung"
    thema: str = ""
    ziele: tuple[str, ...] = ()
    arbeitsformen: str = ""
    vorbereitung: str = ""
    verschriftlichung: str = ""
    bloecke: tuple[Block, ...] = field(default_factory=lambda: tuple(standard_bloecke()))

    @property
    def wochentag(self) -> str | None:
        return WOCHENTAGE[self.datum.weekday()] if self.datum else None

    @property
    def datum_text(self) -> str | None:
        return self.datum.strftime("%d.%m.%Y") if self.datum else None

    def mit(self, **felder: Any) -> Tagesplan:
        return replace(self, **felder)

    def block_inhalt(self, block: Block, konferenzen: list[str]) -> str:
        """Inhalt des Blocks; Konferenzblöcke tragen die gewählten Konferenzen vor dem eigenen Inhalt ein."""
        if block.art != "konferenzen" or not konferenzen:
            return block.inhalt
        liste = ", ".join(konferenzen)
        return f"{liste}\n{block.inhalt}" if block.inhalt else liste

    def pruefe(self) -> list[Pruefhinweis]:
        hinweise: list[Pruefhinweis] = []
        for i, b in enumerate(self.bloecke):
            if b.zeitart == "bereich" and b.ende is not None and b.ende <= b.beginn:
                hinweise.append(
                    Pruefhinweis(
                        i, f"„{b.titel or b.zeit_text}“: Das Ende liegt nicht nach dem Beginn.", True
                    )
                )
        bereiche = [(i, b) for i, b in enumerate(self.bloecke) if b.zeitart == "bereich" and b.ende]
        for n, (i, a) in enumerate(bereiche):
            for j, b in bereiche[n + 1 :]:
                if a.ende > a.beginn and b.ende > b.beginn and a.beginn < b.ende and b.beginn < a.ende:
                    hinweise.append(
                        Pruefhinweis(
                            j,
                            f"„{b.titel or b.zeit_text}“ überschneidet sich mit „{a.titel or a.zeit_text}“.",
                            False,
                        )
                    )
        return hinweise

    def als_dict(self) -> dict[str, Any]:
        return {
            "datum": self.datum.isoformat() if self.datum else None,
            "titel": self.titel,
            "thema": self.thema,
            "ziele": list(self.ziele),
            "arbeitsformen": self.arbeitsformen,
            "vorbereitung": self.vorbereitung,
            "verschriftlichung": self.verschriftlichung,
            "bloecke": [b.als_dict() for b in self.bloecke],
        }

    @classmethod
    def aus_dict(cls, d: Any) -> Tagesplan:
        """Unlesbare oder fehlende Angaben fallen auf den Standard zurück."""
        if not isinstance(d, dict):
            return cls()
        try:
            datum = date.fromisoformat(d["datum"]) if d.get("datum") else None
        except (ValueError, TypeError):
            datum = None
        roh = d.get("bloecke")
        if isinstance(roh, list):
            bloecke = tuple(b for b in (Block.aus_dict(x) for x in roh if isinstance(x, dict)) if b)
        else:
            bloecke = tuple(standard_bloecke())
        ziele = d.get("ziele")
        text = lambda k: str(d.get(k) or "")
        return cls(
            datum=datum,
            titel=str(d["titel"]) if isinstance(d.get("titel"), str) else cls().titel,
            thema=text("thema"),
            ziele=tuple(str(z) for z in ziele) if isinstance(ziele, list) else (),
            arbeitsformen=text("arbeitsformen"),
            vorbereitung=text("vorbereitung"),
            verschriftlichung=text("verschriftlichung"),
            bloecke=bloecke,
        )
