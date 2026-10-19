"""CP-SAT-Implementierung des `Planer` (SPEC-0002)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, replace

from ortools.sat.python import cp_model

from konfiplaner.modell import Modell, Plan, Termin, Verstoss
from konfiplaner.planer import Abbruchsignal, Fortschritt, PlanerOptionen
from konfiplaner.restriktionen import STANDARD_REGISTRY, Konfiguration, Registry
from konfiplaner.restriktionen.kontext import Term, Var

MAX_TERMINE_JE_THEMA = 3
GEWICHT_SKALA = 1000  # weiche Bedingungen dominieren Slot-Präferenzen (Index ≤ ~200)
TERMIN_STRAFE = 1  # Tiebreaker: lieber wenige Termine


@dataclass
class _Verletzung:
    regel: str
    text: str
    var: cp_model.IntVar


class _CpSatKontext:
    """Adapter: übersetzt `Planungskontext` auf ein CP-SAT-Modell."""

    def __init__(self, modell: Modell, mit_annahmen: bool) -> None:
        self.modell = modell
        self.cp = cp_model.CpModel()
        self._mit_annahmen = mit_annahmen
        self._k: dict[str, int] = {}
        self._aktiv: dict[tuple[str, int], cp_model.IntVar] = {}
        self._start: dict[tuple[str, int, int], cp_model.IntVar] = {}
        self._bloecke: dict[str, dict[int, int]] = {}
        self._teil: dict[tuple[str, str, int], cp_model.IntVar] = {}
        self._belegt: dict[tuple[str, int, int], cp_model.IntVar] = {}
        self._praesenz: dict[tuple[str, str, int, int], cp_model.IntVar] = {}
        self._ziel: list[cp_model.LinearExpr] = []
        self.verletzungen: list[_Verletzung] = []
        self.annahmen: list[tuple[cp_model.IntVar, str, str]] = []
        self._regel = ""
        self._typ = "hart"
        self._gewicht = 1.0
        self.keine_startslots: list[str] = []
        self._aufbau()

    # ── Struktur (nicht konfigurierbar) ──────────────────────────────────────
    def _aufbau(self) -> None:
        m, cp = self.modell, self.cp
        for t in m.themen:
            n = len(m.personen_zu(t.name))
            if t.vorsitz is None:
                moegliche = n // t.mindestanzahl
            else:  # der Vorsitz sitzt in jedem Termin: die übrigen müssen nur Mindestanzahl - 1 stellen
                moegliche = (n - 1) // max(1, t.mindestanzahl - 1)
            self._k[t.name] = max(1, min(MAX_TERMINE_JE_THEMA, moegliche))
            self._bloecke[t.name] = m.bloecke(t.name)
            if not self._bloecke[t.name]:
                self.keine_startslots.append(t.name)
            for j in range(self._k[t.name]):
                a = cp.NewBoolVar(f"aktiv_{t.name}_{j}")
                self._aktiv[t.name, j] = a
                starts = []
                for s in self._bloecke[t.name]:
                    v = cp.NewBoolVar(f"start_{t.name}_{j}_{s}")
                    self._start[t.name, j, s] = v
                    starts.append(v)
                cp.Add(sum(starts) == a)
                if j:
                    cp.Add(self._aktiv[t.name, j - 1] >= a)
                for p in m.personen_zu(t.name):
                    tv = cp.NewBoolVar(f"teil_{p.name}_{t.name}_{j}")
                    self._teil[p.name, t.name, j] = tv
                    cp.Add(tv <= a)
            for p in m.personen_zu(t.name):
                if p.name != t.vorsitz:  # der Vorsitz ist in allen Terminen des Themas
                    cp.Add(sum(self._teil[p.name, t.name, j] for j in range(self._k[t.name])) <= 1)
            self._ziel.extend(TERMIN_STRAFE * self._aktiv[t.name, j] for j in range(self._k[t.name]))

    # ── Planungskontext ──────────────────────────────────────────────────────
    def termine(self, thema: str) -> range:
        return range(self._k[thema])

    def aktiv(self, thema: str, j: int) -> Var:
        return self._aktiv[thema, j]

    def teilnahme(self, person: str, thema: str, j: int) -> Var:
        return self._teil[person, thema, j]

    def _belegung(self, thema: str, j: int, slot: int) -> cp_model.IntVar:
        key = (thema, j, slot)
        if key not in self._belegt:
            deckend = [self._start[thema, j, s] for s, n in self._bloecke[thema].items() if s <= slot < s + n]
            b = self.cp.NewBoolVar(f"belegt_{thema}_{j}_{slot}")
            self.cp.Add(b == sum(deckend))
            self._belegt[key] = b
        return self._belegt[key]

    def praesenz(self, person: str, thema: str, j: int, slot: int) -> Var:
        key = (person, thema, j, slot)
        if key not in self._praesenz:
            p = self.cp.NewBoolVar(f"praesenz_{person}_{thema}_{j}_{slot}")
            self.cp.AddMultiplicationEquality(
                p, [self._teil[person, thema, j], self._belegung(thema, j, slot)]
            )
            self._praesenz[key] = p
        return self._praesenz[key]

    def startterme(self, thema: str, j: int) -> list[tuple[int, Var]]:
        return [(s, self._start[thema, j, s]) for s in self._bloecke[thema]]

    def bedingung(
        self, terme: list[Term], untergrenze: int | None, obergrenze: int | None, text: str
    ) -> None:
        ausdruck = sum(k * v for k, v in terme)
        if self._typ == "hart":
            lit = self.cp.NewBoolVar("") if self._mit_annahmen else None
            for c in self._grenzen(ausdruck, untergrenze, obergrenze):
                (c.OnlyEnforceIf(lit) if lit is not None else c)
            if lit is not None:
                self.annahmen.append((lit, self._regel, text))
        else:
            v = self.cp.NewBoolVar("")
            for c in self._grenzen(ausdruck, untergrenze, obergrenze):
                c.OnlyEnforceIf(v.Not())
            self._ziel.append(round(self._gewicht * GEWICHT_SKALA) * v)
            self.verletzungen.append(_Verletzung(self._regel, text, v))

    def _grenzen(self, ausdruck, lo, hi):
        if lo is not None:
            yield self.cp.Add(ausdruck >= lo)
        if hi is not None:
            yield self.cp.Add(ausdruck <= hi)

    def strafe(self, terme: list[Term], text: str) -> None:
        for k, v in terme:
            koeff = round(self._gewicht * k)
            if koeff:
                self._ziel.append(koeff * v)

    # ── Adapter-intern ───────────────────────────────────────────────────────
    def setze_regel(self, name: str, typ: str, gewicht: float) -> None:
        self._regel, self._typ, self._gewicht = name, typ, gewicht

    def schliesse(self) -> None:
        self.cp.Minimize(sum(self._ziel))
        if self._mit_annahmen:
            self.cp.AddAssumptions([lit for lit, _, _ in self.annahmen])
        for thema in self.keine_startslots:
            for j in range(self._k[thema]):
                self.cp.Add(self._aktiv[thema, j] == 0)


class _Rueckruf(cp_model.CpSolverSolutionCallback):
    def __init__(self, fortschritt, abbruch) -> None:
        super().__init__()
        self._fortschritt, self._abbruch = fortschritt, abbruch
        self.aufrufe = 0

    def on_solution_callback(self) -> None:
        self.aufrufe += 1
        if self._fortschritt:
            self._fortschritt(Fortschritt(self.ObjectiveValue(), self.WallTime()))
        if self._abbruch and self._abbruch.is_set():
            self.StopSearch()


class CpSatPlaner:
    """`Planer` auf Basis von OR-Tools CP-SAT."""

    def __init__(self, registry: Registry = STANDARD_REGISTRY) -> None:
        self._registry = registry

    def planen(
        self,
        modell: Modell,
        konfiguration: Konfiguration,
        optionen: PlanerOptionen | None = None,
        fortschritt: Callable[[Fortschritt], None] | None = None,
        abbruch: Abbruchsignal | None = None,
    ) -> Plan:
        optionen = optionen or PlanerOptionen()
        start = time.perf_counter()
        aktive = konfiguration.aktive()
        regeln = [(e, self._registry.hole(e.name)()) for e in aktive]  # Fehler vor dem Solverlauf
        for e, r in regeln:
            r.pruefe_parameter(e.parameter)

        warnungen = [f"{p} hat keine Verfügbarkeit" for p, s in modell.verfuegbarkeit.items() if not s]
        ctx = self._baue(modell, regeln, mit_annahmen=False)
        # Das Zeitlimit gilt für den gesamten Aufruf, nicht nur für die Suche
        rest = max(1.0, optionen.zeitlimit_s - (time.perf_counter() - start))
        solver = self._solver(replace(optionen, zeitlimit_s=rest))
        rueckruf = _Rueckruf(fortschritt, abbruch)
        stopper = self._starte_stopper(solver, abbruch)
        try:
            status = solver.Solve(ctx.cp, rueckruf)
        finally:
            stopper.set()

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            plan = self._lese(
                modell, ctx, solver, regeln, optionen, "optimal" if status == cp_model.OPTIMAL else "machbar"
            )
        else:
            if status == cp_model.INFEASIBLE:
                gruende = self._diagnose(modell, regeln, optionen)
            elif abbruch is not None and abbruch.is_set():
                gruende = ["Abgebrochen, bevor ein Plan gefunden wurde"]
            else:
                gruende = ["Zeitlimit erreicht, bevor ein Plan gefunden wurde – Zeitlimit erhöhen"]
            plan = Plan("kein_plan", begruendung=gruende, seed=optionen.seed)
        plan.warnungen = warnungen
        return plan

    # ── intern ───────────────────────────────────────────────────────────────
    def _baue(self, modell, regeln, mit_annahmen: bool) -> _CpSatKontext:
        ctx = _CpSatKontext(modell, mit_annahmen)
        for e, r in regeln:
            ctx.setze_regel(e.name, e.typ, e.gewicht)
            r.anwenden(ctx, e.parameter)
        ctx.schliesse()
        return ctx

    @staticmethod
    def _solver(optionen: PlanerOptionen) -> cp_model.CpSolver:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = optionen.zeitlimit_s
        solver.parameters.random_seed = optionen.seed
        if optionen.arbeiter:
            solver.parameters.num_workers = optionen.arbeiter
        return solver

    @staticmethod
    def _starte_stopper(solver, abbruch) -> threading.Event:
        fertig = threading.Event()
        if abbruch is not None:

            def lauf() -> None:
                while not fertig.wait(0.05):
                    if abbruch.is_set():
                        solver.StopSearch()
                        return

            threading.Thread(target=lauf, daemon=True).start()
        return fertig

    def _lese(self, modell, ctx, solver, regeln, optionen, status) -> Plan:
        termine = []
        for t in modell.themen:
            for j in ctx.termine(t.name):
                if not solver.BooleanValue(ctx.aktiv(t.name, j)):
                    continue
                start = next(s for s, v in ctx.startterme(t.name, j) if solver.BooleanValue(v))
                teilnehmer = tuple(
                    p.name
                    for p in modell.personen_zu(t.name)
                    if solver.BooleanValue(ctx.teilnahme(p.name, t.name, j))
                )
                termine.append(Termin(t.name, start, modell.bloecke(t.name)[start], teilnehmer))
        termine.sort(key=lambda x: (x.start_slot, x.thema))
        verstoesse = [Verstoss(v.regel, v.text) for v in ctx.verletzungen if solver.BooleanValue(v.var)]
        plan = Plan(status, termine, verstoesse, seed=optionen.seed)
        for e, r in regeln:
            if e.typ == "weich":
                plan.verstoesse.extend(r.erklaere(plan, e.parameter))
        return plan

    def _diagnose(self, modell, regeln, optionen) -> list[str]:
        gruende = []
        for name in modell.bloecke_fehlen():
            t = modell.thema(name)
            gruende.append(
                f"Regel themenabdeckung: Thema {name} (Dauer {t.dauer_min} min) passt in keinen Zeitblock"
            )
        ctx = self._baue(modell, regeln, mit_annahmen=True)
        solver = self._solver(optionen)
        if solver.Solve(ctx.cp) == cp_model.INFEASIBLE:
            kern = set(solver.SufficientAssumptionsForInfeasibility())
            beteiligt = [a for a in ctx.annahmen if a[0].Index() in kern]
            for _, regel, text in self._verkleinere(ctx, beteiligt, optionen):
                gruende.append(f"Regel {regel}: {text}")
        return gruende[:15] or ["Kein gültiger Plan unter den harten Regeln"]

    @staticmethod
    def _verkleinere(ctx, kern, optionen, max_versuche: int = 60):
        """Löschbasierte Minimierung des Unlösbarkeitskerns (begrenzt, damit Diagnosen schnell bleiben)."""
        kern = list(kern)
        versuche = 0
        i = 0
        while i < len(kern) and versuche < max_versuche:
            rest = kern[:i] + kern[i + 1 :]
            ctx.cp.ClearAssumptions()
            ctx.cp.AddAssumptions([lit for lit, _, _ in rest])
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = min(5.0, optionen.zeitlimit_s)
            solver.parameters.random_seed = optionen.seed
            versuche += 1
            if solver.Solve(ctx.cp) == cp_model.INFEASIBLE:
                kern = rest
            else:
                i += 1
        return kern
