"""Verteilungsbrett: eine Spalte je Konferenz, Lehrkräfte als Karten, Verschieben per Drag and Drop (SPEC-0013)."""

from __future__ import annotations

import json
from collections.abc import Callable

from PySide6.QtCore import QMimeData, QModelIndex, QPersistentModelIndex, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QKeySequence,
    QPainter,
    QPen,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScrollArea,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from konfiplaner.anwendung import KartenAnsicht, Sitzung, SpaltenAnsicht
from konfiplaner.gui.design import DUNKEL, fachfarbe, fachpunkt
from konfiplaner.modell import ModellFehler

MIME = "application/x-konfiplaner-karte"
SPALTENBREITE = 236
KARTENHOEHE = 58
OHNE = "Ohne Zuteilung"


def _nutzdaten(item: QListWidgetItem) -> KartenAnsicht:
    return item.data(Qt.ItemDataRole.UserRole)


class KartenDelegate(QStyledItemDelegate):
    """Zeichnet eine Lehrkraft als Karte: Name, darunter die weiteren Konferenzen ihres Sets mit Fachfarbe."""

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex
    ) -> None:
        karte: KartenAnsicht = index.data(Qt.ItemDataRole.UserRole)
        t = DUNKEL
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        flaeche = QRectF(option.rect).adjusted(2, 2, -2, -2)
        gewaehlt = bool(option.state & QStyle.StateFlag.State_Selected)
        painter.setPen(QPen(QColor(t.akzent if gewaehlt else t.linie_stark), 2 if gewaehlt else 1))
        painter.setBrush(QColor(t.zebra if karte.vorsitz else t.erhoeht))
        painter.drawRoundedRect(flaeche, t.radius_klein + 2, t.radius_klein + 2)
        font = painter.font()
        font.setPixelSize(t.normal)
        font.setWeight(font.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor(t.kreide))
        x, oben = flaeche.left() + 12, flaeche.top() + 7
        name = QRectF(x, oben, flaeche.width() - 24 - (66 if karte.vorsitz else 0), 20)
        painter.drawText(
            name,
            Qt.AlignmentFlag.AlignVCenter,
            painter.fontMetrics().elidedText(karte.name, Qt.TextElideMode.ElideRight, int(name.width())),
        )
        klein = painter.font()
        klein.setPixelSize(t.klein)
        klein.setWeight(klein.Weight.Normal)
        painter.setFont(klein)
        if karte.vorsitz:
            painter.setPen(QColor(t.akzent))
            painter.drawText(
                QRectF(flaeche.right() - 74, oben, 62, 20),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                "Vorsitz",
            )
        y = oben + 24
        painter.setPen(QColor(t.gedaempft))
        if not karte.weitere:
            text = "nur diese Konferenz" if karte.hat_konferenz else "keine Konferenz im Set"
            painter.drawText(QRectF(x, y, flaeche.width() - 24, 18), Qt.AlignmentFlag.AlignVCenter, text)
        else:
            fm = painter.fontMetrics()
            cx = x
            for name_ in karte.weitere:
                breite = fm.horizontalAdvance(name_)
                if cx + 14 + breite > flaeche.right() - 10:
                    painter.drawText(QRectF(cx, y, 20, 18), Qt.AlignmentFlag.AlignVCenter, "…")
                    break
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(fachfarbe(name_))
                painter.drawEllipse(QRectF(cx, y + 5, 8, 8))
                painter.setPen(QColor(t.gedaempft))
                painter.drawText(QRectF(cx + 12, y, breite + 2, 18), Qt.AlignmentFlag.AlignVCenter, name_)
                cx += 12 + breite + 12
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QSize:
        return QSize(SPALTENBREITE - 28, KARTENHOEHE)


class SpaltenListe(QListWidget):
    """Eine Spalte des Bretts. Karten lassen sich ziehen und hier ablegen."""

    abgelegt = Signal(str, object, object)  # Lehrkraft, von (Konferenz oder None), nach (Konferenz oder None)
    ziehen_ueber = Signal(object)  # None | "imset" | "ausnahme"

    # Läuft gerade ein Ziehen, wartet die Ablage bis QDrag.exec() zurück ist: Das Brett baut sich beim
    # Verschieben neu auf und würde sonst die Quellspalte mitten im Ziehen löschen (Absturz unter macOS).
    _zieht = False
    _ausstehend: tuple[SpaltenListe, str, object, object] | None = None

    def __init__(self, konferenz: str | None) -> None:
        super().__init__()
        self.konferenz = konferenz
        self.setObjectName("karten")
        self.setAccessibleName(f"Spalte {konferenz or OHNE}")
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSpacing(0)
        self.setItemDelegate(KartenDelegate(self))
        self.setUniformItemSizes(True)

    # ── Ziehen ───────────────────────────────────────────────────────────────
    def startDrag(self, actions: Qt.DropAction) -> None:
        SpaltenListe._zieht = True
        try:
            super().startDrag(actions)
        finally:
            SpaltenListe._zieht = False
            ausstehend, SpaltenListe._ausstehend = SpaltenListe._ausstehend, None
        if ausstehend is not None:
            ziel, person, von, nach = ausstehend
            ziel.abgelegt.emit(person, von, nach)

    def mimeTypes(self) -> list[str]:
        return [MIME]

    def mimeData(self, items: list[QListWidgetItem]) -> QMimeData:
        karte = _nutzdaten(items[0])
        daten = QMimeData()
        daten.setData(
            MIME,
            json.dumps({"person": karte.name, "von": self.konferenz, "set": list(karte.weitere)}).encode(),
        )
        daten.setText(karte.name)
        return daten

    @staticmethod
    def _lese(daten: QMimeData) -> dict | None:
        if not daten.hasFormat(MIME):
            return None
        try:
            return json.loads(bytes(daten.data(MIME)).decode())
        except (ValueError, UnicodeDecodeError):
            return None

    def _zustand(self, nutz: dict) -> str | None:
        """„imset“, „ausnahme“ oder None, wenn hier nichts abgelegt werden kann."""
        if nutz["von"] == self.konferenz:
            return None
        if self.konferenz is None:
            return None  # „Ohne Zuteilung“ ist nur Quelle
        return "imset" if self.konferenz in nutz["set"] else "ausnahme"

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        self._pruefe(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        self._pruefe(event)

    def _pruefe(self, event) -> None:
        nutz = self._lese(event.mimeData())
        zustand = self._zustand(nutz) if nutz else None
        self.ziehen_ueber.emit(zustand)
        if zustand:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.ziehen_ueber.emit(None)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        nutz = self._lese(event.mimeData())
        self.ziehen_ueber.emit(None)
        if not nutz or self._zustand(nutz) is None:
            event.ignore()
            return
        # Das Brett baut sich nach dem Verschieben neu auf; Qt soll die Karte nicht selbst umhängen
        event.setDropAction(Qt.DropAction.IgnoreAction)
        event.accept()
        if SpaltenListe._zieht:
            SpaltenListe._ausstehend = (self, nutz["person"], nutz["von"], self.konferenz)
        else:
            self.abgelegt.emit(nutz["person"], nutz["von"], self.konferenz)


class SpaltenFeld(QFrame):
    """Kopf und Karten einer Konferenz."""

    def __init__(self, spalte: SpaltenAnsicht) -> None:
        super().__init__()
        self.spalte = spalte
        self.setObjectName("spalte")
        self.setFixedWidth(SPALTENBREITE)
        self.setProperty("ziel", "")
        self.liste = SpaltenListe(spalte.konferenz)
        titel = QLabel(spalte.konferenz or OHNE)
        titel.setObjectName("spaltentitel")
        kopf = QHBoxLayout()
        kopf.setSpacing(8)
        if spalte.konferenz:
            punkt = QLabel()
            punkt.setPixmap(fachpunkt(spalte.konferenz, 7).pixmap(14, 14))
            kopf.addWidget(punkt)
        kopf.addWidget(titel, 1)
        if spalte.konferenz is None:
            zeile = f"{spalte.teilnehmer} Lehrkräfte"
        else:
            zeile = f"{spalte.teilnehmer} Teilnehmende, mindestens {spalte.mindestanzahl}, Ziel {spalte.ziel}"
        self.zahlen = QLabel(zeile)
        self.zahlen.setObjectName("hinweis")
        self.zahlen.setWordWrap(True)
        self.warnung = QLabel("unter Mindestanzahl" if spalte.unterbesetzt and spalte.konferenz else "")
        self.warnung.setProperty("klein", True)
        if not self.warnung.text():
            self.warnung.setVisible(
                False
            )  # nie True vor dem Einhängen: ein Label ohne Eltern wäre ein eigenes Fenster
        self.ausnahme = QLabel("Ausnahme: nicht im Set dieser Lehrkraft")
        self.ausnahme.setObjectName("ausnahmehinweis")
        self.ausnahme.setWordWrap(True)
        self.ausnahme.setVisible(False)
        wurzel = QVBoxLayout(self)
        wurzel.setContentsMargins(12, 12, 12, 10)
        wurzel.setSpacing(4)
        wurzel.addLayout(kopf)
        wurzel.addWidget(self.zahlen)
        wurzel.addWidget(self.warnung)
        wurzel.addWidget(self.ausnahme)
        wurzel.addWidget(self.liste, 1)
        for karte in spalte.karten:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, karte)
            item.setSizeHint(QSize(SPALTENBREITE - 28, KARTENHOEHE))
            item.setToolTip(self._tooltip(karte))
            fl = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            item.setFlags(fl if karte.vorsitz else fl | Qt.ItemFlag.ItemIsDragEnabled)
            self.liste.addItem(item)
        self.liste.ziehen_ueber.connect(self._ziel_anzeigen)

    @staticmethod
    def _tooltip(karte: KartenAnsicht) -> str:
        if karte.vorsitz:
            return f"{karte.name} leitet diese Konferenz. Den Vorsitz im Dialog „Bearbeiten“ ändern."
        weitere = ", ".join(karte.weitere) or "keine"
        return f"{karte.name}. Weitere Konferenzen im Set: {weitere}"

    def _ziel_anzeigen(self, zustand: object) -> None:
        self.setProperty("ziel", zustand or "")
        self.ausnahme.setVisible(zustand == "ausnahme")
        self.style().unpolish(self)
        self.style().polish(self)


class Brett(QWidget):
    """Das Verteilungsbrett als Reiter im Ergebnis."""

    geaendert = Signal()
    hinweis = Signal(str)

    def __init__(self, sitzung: Sitzung) -> None:
        super().__init__()
        self.sitzung = sitzung
        # In Tests ersetzbar: wählt im Menü „Verschieben nach“ einen Eintrag (liefert Konferenz oder None)
        self.menue_ausfuehren: Callable[[QMenu], QAction | None] = lambda m: m.exec(self.cursor().pos())
        self.felder: list[SpaltenFeld] = []
        self.rueckgaengig = QPushButton("&Rückgängig")
        self.rueckgaengig.setAccessibleName("Letzte Verschiebung rückgängig")
        self.rueckgaengig.clicked.connect(self.mache_rueckgaengig)
        self.zusammenfassung = QLabel("")
        self.zusammenfassung.setWordWrap(True)
        self.pruefung = QLabel("")
        self.pruefung.setObjectName("pruefung")
        self.pruefung.setWordWrap(True)
        kopf = QHBoxLayout()
        kopf.addWidget(self.zusammenfassung, 1)
        kopf.addWidget(self.rueckgaengig)
        self.inhalt = QWidget()
        self.spaltenlayout = QHBoxLayout(self.inhalt)
        self.spaltenlayout.setContentsMargins(0, 0, 0, 0)
        self.spaltenlayout.setSpacing(12)
        self.rolle = QScrollArea()
        self.rolle.setWidgetResizable(True)
        self.rolle.setFrameShape(QFrame.Shape.NoFrame)
        self.rolle.setWidget(self.inhalt)
        self.rolle.setAccessibleName("Verteilungsbrett")
        self.leer = QLabel("Noch kein Plan. Zuerst planen, dann lassen sich Lehrkräfte hier verschieben.")
        self.leer.setObjectName("leer")
        self.leer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wurzel = QVBoxLayout(self)
        wurzel.addLayout(kopf)
        wurzel.addWidget(self.pruefung)
        wurzel.addWidget(self.rolle, 1)
        wurzel.addWidget(self.leer)
        QShortcut(QKeySequence.StandardKey.Undo, self, activated=self.mache_rueckgaengig).setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.aktualisieren()

    # ── Anzeige ──────────────────────────────────────────────────────────────
    def aktualisieren(self) -> None:
        spalten = self.sitzung.verteilung()
        for feld in self.felder:
            self.spaltenlayout.removeWidget(feld)
            feld.deleteLater()
        self.felder = []
        for sp in spalten:
            feld = SpaltenFeld(sp)
            feld.liste.abgelegt.connect(self.verschiebe)
            feld.liste.itemActivated.connect(lambda item, f=feld: self.menue(item, f.spalte.konferenz))
            feld.liste.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            feld.liste.customContextMenuRequested.connect(lambda pos, f=feld: self._kontext(f, pos))
            self.spaltenlayout.addWidget(feld)
            feld.show()  # Qt zeigt nachträglich eingehängte Widgets sonst erst verzögert
            self.felder.append(feld)
        self.spaltenlayout.addStretch(1)
        vorhanden = bool(spalten)
        self.rolle.setVisible(vorhanden)
        self.leer.setVisible(not vorhanden)
        self.rueckgaengig.setEnabled(self.sitzung.kann_rueckgaengig)
        self.rueckgaengig.setVisible(vorhanden)
        if vorhanden:
            verteilt = sum(len(sp.karten) for sp in spalten[1:])
            offen = len(spalten[0].karten)
            self.zusammenfassung.setText(
                f"{verteilt} Lehrkräfte verteilt auf {len(spalten) - 1} Konferenzen, {offen} ohne Zuteilung. "
                "Karten ziehen oder mit Enter verschieben."
            )
            hinweise = self.sitzung.pruefe_verteilung()
            self.pruefung.setText(
                "<br>".join(f"<span style='color:{DUNKEL.konflikt}'>Prüfung:</span> {h}" for h in hinweise)
            )
            self.pruefung.setVisible(bool(hinweise))
        else:
            self.zusammenfassung.setText("")
            self.pruefung.setVisible(False)

    def feld(self, konferenz: str | None) -> SpaltenFeld:
        return next(f for f in self.felder if f.spalte.konferenz == konferenz)

    # ── Verschieben ──────────────────────────────────────────────────────────
    def verschiebe(self, person: str, von: str | None, nach: str | None) -> None:
        if nach is None:
            return
        try:
            folge = self.sitzung.verschiebe(person, nach, von)
        except ModellFehler as e:
            self.hinweis.emit(str(e))
            self.aktualisieren()
            return
        text = f"{person}: {von or OHNE} → {nach}"
        if folge.ausnahme:
            text += f". Ausnahme: {nach} gehörte nicht zum Set von {person} und wurde ergänzt"
        self.aktualisieren()
        self.geaendert.emit()
        self.hinweis.emit(text)

    def mache_rueckgaengig(self) -> bool:
        if not self.sitzung.rueckgaengig():
            self.hinweis.emit("Nichts rückgängig zu machen")
            self.aktualisieren()
            return False
        self.aktualisieren()
        self.geaendert.emit()
        self.hinweis.emit("Verschiebung rückgängig gemacht")
        return True

    # ── Tastatur und Kontextmenü (SPEC-0013 FR-09) ───────────────────────────
    def _kontext(self, feld: SpaltenFeld, pos) -> None:
        item = feld.liste.itemAt(pos)
        if item is not None:
            self.menue(item, feld.spalte.konferenz)

    def menue(self, item: QListWidgetItem, von: str | None) -> None:
        karte = _nutzdaten(item)
        if karte.vorsitz:
            self.hinweis.emit(
                f"{karte.name} leitet {von}. Den Vorsitz zuerst im Dialog „Bearbeiten“ ändern, dann verschieben."
            )
            return
        menue = QMenu(self)
        menue.setTitle(f"{karte.name} verschieben nach")
        for sp in self.sitzung.verteilung()[1:]:
            if sp.konferenz == von:
                continue
            im_set = sp.konferenz in karte.weitere or sp.vorsitz == karte.name
            aktion = menue.addAction(
                fachpunkt(sp.konferenz or "", 7), sp.konferenz + ("" if im_set else " (Ausnahme)")
            )
            aktion.setData((karte.name, von, sp.konferenz))
        gewaehlt = self.menue_ausfuehren(menue)
        if gewaehlt is not None and gewaehlt.data():
            self.verschiebe(*gewaehlt.data())
