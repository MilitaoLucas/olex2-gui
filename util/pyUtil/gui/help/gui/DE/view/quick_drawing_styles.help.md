# Quick Drawing Styles
# cell-target
Elementarzelle zeichnen


# base-target
Basisvektoren anzeigen


# Quick Drawing Styles
Mit den Schaltflächen in diesem Bereich lassen sich voreingestellte Zeichenstile wählen. Der neue Stil gilt nur für die aktuelle Auswahl; sind keine Atome ausgewählt, gilt er für alle Atome.

## Kugel-Stab
| `pers` | Atome erscheinen als Kugeln. Ihre Größe hängt vom Atomradius des jeweiligen Elements ab. |

## Ellipsoide
| `telp 50` (n = 50 ist der Standard) | Anisotrope Atome erscheinen als Ellipsoide, isotrope als Kugeln, deren Größe vom Uiso-Wert des jeweiligen Atoms abhängt. |

## Ellipsoide mit Wasserstoff
Anisotrope Atome erscheinen als Ellipsoide, Wasserstoffatome als Kugeln mit Radien proportional zu ihren Uiso-Werten.

## Drahtmodell
| `proj` | Das Strukturmodell wird als Drahtmodell gezeigt. |

## Kugelpackung
| `sfil` | Atome erscheinen als raumfüllende Kugeln. |

## Röhren
| `tubes` | Das ganze Modell wird als zusammenhängende Röhren dargestellt. |

## Polyeder
| `mask atoms 37` | Zeigt die Struktur als Polyeder. |

## Def
| `default` | Setzt alle Anzeigeeinstellungen auf ihre Standardwerte zurück. |

## Licht
Ein Darstellungsstil mit hellen Kohlenstoffatomen vor dunklem Hintergrund.


[comment]: < Help text for "Atom r" and "Bond r" is now taken from settings.md. >


# Graphical objects
Hier gibt es mehrere Tools, die die Darstellung einer Struktur verbessern.

## Zelle
Schaltet die Anzeige der Elementarzelle ein oder aus.

Hinweis: Liegt die Struktur nicht in der angezeigten Elementarzelle, verschiebt der Befehl '<c>move</c>' sie in die Zelle.

## Basis
Schaltet die Anzeige der Basisvektoren ein oder aus.

## Box-Funktion 1
Schaltet eine durchscheinende Box von Größe und Form der Elementarzelle ein oder aus. Die Box lässt sich unabhängig von Struktur und Zelle verschieben und drehen.

## Box-Funktion 2
Zwei oder mehr Atome auswählen. Ein Klick auf diese Schaltfläche schaltet einen Quader um diese Atome ein oder aus. Auch diese Box lässt sich unabhängig von Struktur und Zelle drehen und verschieben.


[comment]: < The help text given below for "Align and Lock" is the same as in images.md. >


# Align and Lock

## Ansicht und Ebene
Diese Links richten die Struktur im Anzeigefenster aus und zentrieren sie, was vor dem Erstellen von Bildern nützlich sein kann. **View** zentriert und orientiert die Struktur anhand ihrer Hauptträgheitsachsen. **Plane** berechnet eine beste Ebene durch die ganze Struktur, stellt die Struktur senkrecht zu dieser Ebene und zentriert sie. Keine der beiden Methoden ändert die Vergrößerung. '<c>mpln -r<c>' zeigt die beste Ebene und gibt ihre Gleichung im Ausgabefenster aus. Zum Löschen der Ebene diese anklicken und '<c>Entf</c>' drücken.
<br>
<br>

Weitere nützliche Befehle zum Ausrichten der Struktur auf dem Bildschirm:

| `center` | Zentriert die Struktur, ohne Orientierung oder Vergrößerung zu ändern. |

| `compaq -a` | Zentriert die Struktur ebenfalls ohne Änderung der Orientierung, passt aber ihre Größe an den Anzeigebereich an. |

## Sperren
Bei der Arbeit an Bildern ist es manchmal hilfreich, bestimmte Mausfunktionen zu sperren, damit Orientierung oder Vergrößerung nicht versehentlich verändert werden. Zoom, Drehung und Verschiebung lassen sich einzeln über die entsprechenden Felder sperren. Ist z.B. nur **Translation** angehakt, bleibt die Struktur an ihrer Stelle auf dem Bildschirm, lässt sich aber weiter drehen und zoomen. Alle drei Funktionen sperrt das Feld **Alle sperren**.

# Legend Settings
Die Standardposition der Legende (die Atomtypen werden als Kugeln dargestellt) lässt sich auf oben/unten und links/rechts einstellen, ebenso der Abstand zum Rand des Anzeigebereichs.

Hinweis: Die Atomlegende lässt sich an jede beliebige Stelle auf dem Bildschirm verschieben, z.B. näher an die Struktur: '<c>Umschalt</c>' gedrückt halten und mit der Maus ziehen. Mit dem Befehl '<c>legend</c>' lässt sich die Legende aus- und einschalten. Zum Zurücksetzen (z.B. wenn sie verschwunden ist) '<c>legend -r</c>' eingeben.

# Add Fog
Mit der Schaltfläche **Nebel hinzufügen** lässt sich ein künstlicher "Nebel" über die Anzeige legen. Das kann z.B. den räumlichen Eindruck der Struktur verstärken oder ihren vorderen Teil hervorheben. Die Regler **Vorne** und **Back** bestimmen die Dicke des Nebels. **Nebel entfernen** nimmt ihn wieder weg.


[comment]: < The text below is legacy help documentation that doesn't seem to be used anywhere. >


# Atom Styles
Das Aussehen der Atome lässt sich anpassen. Ein Klick auf den Link zeigt ein Periodensystem, von dem aus die Stile angepasst werden können.

## Stile und Szenen
Olex2 kennt zwei Arten von Stilvorlagen: eine für die Atomobjekte (Stile) und eine für Beleuchtung und Hintergrund (Szene). Beide müssen sorgfältig aufeinander abgestimmt sein, damit gute Ergebnisse entstehen. Zum Laden oder Speichern eines Stils oder einer Szene mit der rechten Maustaste auf den Hintergrund klicken und den entsprechenden Links folgen.

## Atomstil ändern
Mit der rechten Maustaste auf das Atom klicken und 'Graphics>Draw Styles' wählen. Das Formular ist recht umfangreich; man muss etwas experimentieren, bis man weiß, was alles möglich ist.

## Anisotrope Atome
Standardmäßig zeigt das Periodensystem anisotrope Atome. Sie bestehen aus 'Kugel' und 'Rändern', deren Aussehen sich getrennt einstellen lässt (siehe das Auswahlfeld oben rechts im Formular 'Draw Styles').

## Isotrope Atome
Beim Periodensystem 'pers' eingeben – dann erscheinen die Atome als Kugeln, und die Einstellungen für die isotrope Darstellung lassen sich ändern.

# Bonds
TBI
