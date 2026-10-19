# language: de
Funktionalität: Restriktionen (SPEC-0003, CON-0006)
  Als Planer:in
  möchte ich Planungsregeln anpassen und erweitern
  um den Plan an wechselnde Anforderungen anzupassen

  Szenario: Neue Regel per Dekorator registrieren
    Angenommen eine Restriktion "nicht_zusammen" ist per Dekorator registriert
    Und die Konfiguration setzt sie hart mit den Parametern person_a "Anna" und person_b "Ben"
    Wenn ich plane
    Dann haben Anna und Ben keinen gemeinsamen Termin

  Szenario: Neue Regel per Entry-Point
    Angenommen ein Paket stellt eine Restriktion im Entry-Point "konfiplaner.restriktionen" bereit
    Wenn die Registry geladen wird
    Dann ist diese Restriktion unter ihrem Namen abrufbar

  Szenario: Grundregel deaktivieren
    Angenommen die Regel "keine_ueberschneidung" steht auf "aus"
    Und nur eine Planung mit Überschneidung erfüllt alle übrigen Regeln
    Wenn ich plane
    Dann wird der Plan mit Überschneidung akzeptiert
    Und "keine_ueberschneidung" erscheint nicht in den Verstößen

  Szenario: Grundregel hart bleibt hart
    Angenommen die Regel "schwerpunkte" ist hart
    Und kein Plan erfüllt alle Schwerpunkte
    Wenn ich plane
    Dann ist der Status "kein_plan"

  Szenario: Grundregel von hart auf weich
    Angenommen die Regel "schwerpunkte" ist weich mit Gewicht 5
    Und kein Plan erfüllt alle Schwerpunkte
    Wenn ich plane
    Dann erhalte ich einen Plan mit den Verstößen der Regel "schwerpunkte"

  Szenario: Gewicht entscheidet bei Konflikt
    Angenommen zwei weiche Regeln, die sich nicht gleichzeitig erfüllen lassen
    Und die erste hat Gewicht 5 und die zweite Gewicht 1
    Wenn ich plane
    Dann ist die erste Regel erfüllt und die zweite verletzt

  Szenario: Gleiche Konfiguration für Grund- und Plugin-Regel
    Angenommen dieselbe Konfigurationsform (typ, gewicht, parameter) für "mindestanzahl" und "nicht_zusammen"
    Wenn die Konfiguration geladen wird
    Dann sind beide gültig

  Szenario: Unbekannte Regel
    Angenommen die Konfiguration nennt die nicht registrierte Regel "gibt_es_nicht"
    Wenn ich plane
    Dann erhalte ich vor dem Solverlauf einen Fehler, der "gibt_es_nicht" nennt

  Szenario: Fehlerhafte Parameter
    Angenommen die Regel "nicht_zusammen" ohne den Parameter person_b
    Wenn ich plane
    Dann erhalte ich vor dem Solverlauf einen Fehler mit Regelname und fehlendem Parameter

  Szenario: Doppelter Regelname
    Angenommen zwei Restriktionen mit dem Namen "nicht_zusammen"
    Wenn ich die zweite registriere
    Dann erhalte ich bei der Registrierung einen Fehler, der den Namen nennt

  Szenario: Weiche Regel ohne Gewicht
    Angenommen eine weiche Regel ohne Gewicht
    Wenn die Konfiguration geladen wird
    Dann gilt das Gewicht 1

  Szenario: Widersprüchliche harte Regeln
    Angenommen "nicht_zusammen" für Anna und Ben und eine Regel, die beide im selben Termin verlangt
    Wenn ich plane
    Dann ist der Status "kein_plan"
    Und die Begründung nennt beide Regeln
