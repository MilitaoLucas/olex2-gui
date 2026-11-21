# settings-target
Die wichtigsten Einstellungen von Olex2.


# Atom Settings
Einige Eigenschaften der Atomdarstellung lassen sich innerhalb eines Stils ändern.

## Atomradius
Dieser Regler ändert den Radius der ausgewählten Atome (im *Kugel-Stab*- bzw. '<c>pers</c>'-Modus). Ein Klick auf **Setzen** macht ihn zum Standardradius. Der Atomradius lässt sich auch mit den Befehlen '<c>arad</c>' und '<c>azoom</c>' einstellen, wie unten beschrieben.

### arad
Dieser Parameter bestimmt den Radius der ausgewählten Atome (oder aller Atome, wenn keine ausgewählt sind), und zwar nur im *Kugel-Stab*-Modus ('<c>pers</c>'). Normalerweise stammt der Radius im '<c>pers</c>'-Modus aus einer Definitionsdatei (und ist je nach Element verschieden). **arad** setzt diese Werte außer Kraft. Ein typischer Wert für H-Atome wäre:

| `arad 0.2` | Setzt den Radius der ausgewählten Atome auf 0.2. |

### azoom
Damit wird die angezeigte Atomgröße *skaliert*, gleich ob die Atome im *Kugel-Stab*- ('<c>pers</c>') oder im *Ellipsoid*-Modus ('<c>telp</c>') dargestellt werden. Der Wert wird in Prozent angegeben und skaliert die ausgewählten Atome.

| `azoom 120` | Skaliert die ausgewählten Atome auf 120 Prozent der normalen Größe. |

| `azoom 100` | Setzt die ausgewählten Atome auf die normale Größe. |

Beim Befehl '<c>azoom</c>' bedeutet "100" die ursprüngliche Atomgröße; größere oder kleinere Werte ändern die Darstellung entsprechend.

Hinweis: Diese Einstellung kann die ORTEP-Konvention der "50 Prozent Aufenthaltswahrscheinlichkeit" durcheinanderbringen. Damit alle Atome mit der üblichen Wahrscheinlichkeit dargestellt werden:

| `telp 50` | Stellt die Ellipsoide auf 50 Prozent Aufenthaltswahrscheinlichkeit ein. |

Die Größe der Ellipsoide auf dem Bildschirm lässt sich über eine andere Wahrscheinlichkeit ändern, z.B. etwas kleiner als der Standardwert:

| `telp 30` | Stellt die Ellipsoide auf 30 Prozent Aufenthaltswahrscheinlichkeit ein. |


# Bond Settings

## Bindungsbreite
Ändert den Radius der ausgewählten Bindungen. Ein Klick auf **Setzen** macht ihn zum Standardradius. Achtung: Damit ändert sich der Radius *aller Bindungen desselben Typs*.

| `individualise` | Um den Radius einer einzelnen Bindung zu ändern, die Bindung auswählen und zuerst diesen Befehl eingeben, dann den Radius auf den gewünschten Wert setzen. |

## Stil
Im Auswahlmenü einen Gesamtstil für alle Atome wählen.

## Bindungsfarbe
Hier wird die Farbe der Bindungen gewählt. Standard ist *elements*: Jede Bindungshälfte hat die Farbe des jeweiligen Atoms. Weitere Möglichkeiten stehen im Auswahlmenü.

# Background
Olex2 bietet verschiedene Hintergründe. Je nach Situation passt mal ein dunkler, mal ein heller und mal ein abgestufter Hintergrund am besten. Zwischen ihnen lässt sich schnell umschalten.

## Farbe/Weiß
**F2** schaltet zwischen dem einfarbigen Hintergrund (festgelegt in den Szeneneinstellungen: Rechtsklick in den Anzeigebereich, dann *Draw style* und *Scene Properties...*) und einem weißen Hintergrund um.

## Abgestufter Hintergrund
**F4** schaltet zwischen dem einfarbigen und dem abgestuften Hintergrund um.

| `grad` | Legt die Farben der vier Ecken des abgestuften Hintergrunds fest. Doppelklick in eines der Farbfelder setzt die Farbe der jeweiligen Ecke. |

Hinweis: Mit **grad -p=dateiname.png** lässt sich ein Hintergrundbild setzen. Das ist z.B. nützlich, um zwei Ansichten einer Struktur oder zwei verschiedene Strukturen nebeneinander auf dem Bildschirm zu vergleichen:

1. Zuerst ein Bild der ersten Ansicht erzeugen: **pict 3.png 3** in die Konsole eingeben (eine größere/kleinere Zahl ergibt ein Bild mit höherer/niedrigerer Auflösung; **help pict** zeigt mehr zum Befehl pict). Damit entsteht die Datei "3.png" im aktuellen Arbeitsordner. (Welcher Ordner das ist, zeigt der Befehl **user**.)

2. Dann die Ansicht verschieben oder drehen oder eine andere Struktur öffnen und **grad -p=3.png** eingeben. Das erste Bild (hier 3.png) erscheint als fester Hintergrund hinter der aktuellen Struktur, die sich weiterhin normal verschieben und drehen lässt.

3. Mit **grad -p** wird das Bild entfernt und der normale abgestufte Hintergrund wiederhergestellt.


# GUI Width
Die Breite der GUI (also des Bereichs mit allen Olex2-Tool-Bereichen und Befehlen, siehe Bild unten) lässt sich beliebig einstellen.

![0.6 Die Olex2-GUI](images/gui.jpg)

<br>
<br>

Einen der Links (**Standard**, **Schmal** oder **Breit**) anklicken oder einen beliebigen Wert eingeben. Die Schriftgröße in der GUI passt sich automatisch an.

## Wert < 1
| `panel 0.33` | Ist der eingegebene Wert kleiner als 1, nimmt die GUI diesen Anteil der Gesamtbreite ein. Mit **0.33** z.B. belegt die GUI 1/3 der Breite und die Struktur 2/3. |

## Wert > 100
| `panel 520` | Ist der eingegebene Wert größer als 100, wird die Breite der GUI auf diesen Wert in Pixeln gesetzt. |


# Swap HTML Panel
Diese Schaltfläche verschiebt die GUI zwischen der rechten und der linken Seite des Olex2-Fensters.


# GUI Links
Legt fest, ob manche Links der GUI als Schaltflächen oder als Hyperlinks erscheinen.


# Tooltips
Ist dies angehakt, erscheinen Tooltips, wenn die Maus über Elementen der GUI steht.


# Legend
Ist dieses Feld angehakt, erscheint im Hauptfenster eine Übersicht aller vorhandenen Atomtypen. Mit gedrückter linker Maustaste und UMSCHALTTASTE lässt sich diese Legende an jede Stelle verschieben.

| `legend` | Schaltet die Legende ein oder aus. |

| `legend -r` | Setzt die Legende zurück. Sehr nützlich, wenn eine versehentlich verschobene oder gelöschte Legende wieder oben links im Anzeigebereich erscheinen soll. |


# Info Bar
| `showwindow info` | Ist dies gewählt, erscheinen weitere Angaben zur Struktur in einer schmalen Leiste am oberen Rand des Anzeigebereichs. |


# Reset Alerts
Alle ausgeblendeten Warnungen werden zurückgesetzt.


# Console Lines
Damit die GUI übersichtlich bleibt, erscheint die Konsolenausgabe hinter dem Molekül. Hier lässt sich die Zahl der angezeigten Zeilen beliebig einstellen. Die Befehle:

| `lines 10` | Zeigt in der Konsole nur 10 Zeilen. Eine andere Zahl ist möglich. |

| `lines -1` | Zeigt alle Ausgabezeilen im Anzeigebereich. |


# Auto MORE
Die hier eingetragenen Schlüsselwörter steuern die Ausgabe der Verfeinerung, z.B. legt **MORE -1** fest, wie viel Information zur Verfeinerung in die .lst-Datei geschrieben wird; **CONF** erzeugt eine Tabelle der Torsionswinkel; **BOND DOLLARH** liefert Bindungslängen und -winkel (einschließlich der Bindungen zu H-Atomen); und **ACTA** schreibt eine CIF-Datei in den aktuellen Arbeitsordner.


# Save View
Ist dies angehakt, werden Zeichnungseinstellungen wie Stile und Hintergründe mit der Struktur gespeichert. Das ist noch etwas experimentell; wenn etwas schiefgeht, muss der gewählte Stil für diese Struktur eventuell neu geladen werden.
<br>
<br>

Ist das Feld **nicht** angehakt, wird eine Struktur mit demselben Stil geladen wie die vorherige.


# Start Olex2 In
Beim Start öffnet Olex2 den hier gewählten Bereich. Das wirkt sich beim nächsten Neustart von Olex2 aus.


# Solo Mode
Beim Öffnen eines Tools werden alle anderen offenen Tools automatisch geschlossen.


# Modules Update
Gibt es Updates für Erweiterungsmodule, erscheint beim Start von Olex2 jedes Mal ein Hinweisfenster. Das lässt sich hier abschalten.


# Unit Cell Style
Die Elementarzelle lässt sich auf verschiedene Weise darstellen. Zuerst muss sie sichtbar sein:

| `cell` | Schaltet die Anzeige der Elementarzelle ein. |

## Zylinder
Die Zelle wird aus Zylindern (also 3D-Objekten) gezeichnet.

## Linien
Die Zelle wird aus einfachen Linien gezeichnet.

## Breite
Legt die Dicke der Zylinder oder Linien fest.

## Farbe
Mit der rechten Maustaste auf die Zylinder oder Linien klicken und **Draw Styles** wählen. Bei den Linien gibt es nur ein Objekt zu ändern; bei den Zylindern lassen sich die kleinen Kugeln in den Ecken und die Zylinder selbst getrennt einstellen.


# User Database
Olex2 unterstützt eine Datenbank mit Personen und ihren Institutionen. Hier wird der Speicherort dieser sqlite-Datenbank festgelegt (Neustart erforderlich). Die Datenbank lässt sich von hier aus auch verwalten.


# Enable Network
Ist dieses Feld nicht angehakt, verbindet sich Olex2 überhaupt nicht mit dem Internet, außer für die Suche nach Updates beim Start.


# Debug Mode
Diese Einstellung ist nur für Entwickler gedacht. Normale Benutzer lassen sie *aus*.


# PATH
Durch Semikolon getrennte Einträge in diesem Feld werden dem **Systempfad** *vor* allen vorhandenen Ordnern hinzugefügt. Kristallographische Programme in den hier genannten Ordnern findet Olex2 also *zuerst* und verwendet sie.


# OpenMP
Ermöglicht Mehrprozessorbetrieb bei der Verfeinerung mit olex2.refine über die OpenMP-Schnittstelle.

Hinweis: Diese Funktion ist noch in Entwicklung und kann instabil sein.
