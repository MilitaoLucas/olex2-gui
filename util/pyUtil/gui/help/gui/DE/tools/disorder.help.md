# Fragment Library
Dieser Link öffnet Ilia Guzeis *Idealized Molecular Geometry Library* (IMGL) im Standard-Webbrowser. Fragmente aus dieser Bibliothek lassen sich direkt von der Webseite in Olex2 kopieren: die Atomkoordinaten des gewünschten Fragments einschließlich der Zeilen *FRAG* und *FEND* auf der IMGL-Webseite kopieren und direkt in die Befehlszeile einfügen, um das Fragment in die Struktur einzusetzen. Eine genaue Schritt-für-Schritt-Anleitung mit Beispielen steht in **Ilia Guzeis Handbuch**, verlinkt im Olex2-Bereich **Start**. Mehr zum Befehl *FRAG* im URL[https://shelx.uni-goettingen.de/shelxl_html.php, SHELX-Handbuch].

Hinweis: Auf das eingefügte Fragment werden keine Constraints, Restraints oder Besetzungen angewendet! Diese müssen eigens eingegeben werden.

## Eingefügte Fragmente
Im Überlagerungsmodus erscheinen die eingefügten Fragmente leicht grünlich auf dem Bildschirm. Fragmente lassen sich an Elektronendichte-Peaks anpassen: zuerst ein Atom im importierten Fragment und dann den passenden Q-Peak anklicken, dann mit weiteren Atom/Q-Paaren wiederholen, bis das Fragment in der gewünschten Lage und Orientierung ist.

## Überlagerungsmodus beenden
Mehrmals '<c>Esc</c>' drücken, den Link **Esc** im orangen Modusfeld anklicken oder '<c>mode off</c>' eingeben.


# Link Selected
Zwei Atome auswählen, die in der Verfeinerung "gekoppelt" werden sollen, wie unten beschrieben.

## Besetzungen
**Occupancies** koppelt die Besetzungen der beiden Atome so, dass ihre Summe eins ergibt. Dasselbe bewirkt der Befehl '<c> fvar sel</c>'.

## PARTs und Besetzungen
Die Besetzungen werden wie oben so gekoppelt, dass ihre Summe eins ergibt, und die ausgewählten Atome kommen zusätzlich in verschiedene PARTs. Entspricht dem Befehl '<c>part -p=2 -lo sel</c>'. Der Schalter "-p=2" verteilt die Atome auf zwei PARTs, "-lo" steht für "link occupancy" (Besetzungen koppeln).


# Link Constraints
Koppelt PARTs und Besetzungen der ausgewählten Atome und wendet dann entweder einen *EADP*-Constraint oder einen *ISOR*-Restraint auf sie an.


# Link Parts 1
Setzt die ausgewählten Atome in die PART-Nummer aus dem Auswahlfeld am Ende dieser Zeile.


# Link Parts 2
Setzt die ausgewählten Atome der Reihe nach in zwei PART-Nummern.


# Show Parts
Enthält eine Struktur Atome in PARTs, ist es manchmal nützlich, nur die Atome bestimmter PARTs anzuzeigen.

| `showP 0 1` | Zeigt nur Atome der PARTs 0 und 1. |

| `showP 0 2` | Zeigt nur Atome der PARTs 0 und 2. |

| `showP 0 -1` | Zeigt nur Atome der PARTs 0 und -1. |

| `showP 0 -2` | Zeigt nur Atome der PARTs 0 und -2. |

| `showP 1 2` | Zeigt nur Atome der PARTs 1 und 2. |

| `showP 1` | Zeigt nur Atome von PART 1. |

| `showP 2` | Zeigt nur Atome von PART 2. |

| `showP` | Zeigt alle Atome aller PARTs. |


# Split Group
Die Tools in dieser Zeile *teilen* jedes der nächsten angeklickten Atome vollständig in zwei Atome.

## Aufteilen
Diese Schaltfläche startet einen Modus, in dem jedes angeklickte Atom zwei Atome erzeugt (in den Brennpunkten der Ellipsoide). Die Besetzung jedes *geteilten* Atoms wird zunächst auf 0.5 gesetzt; ein Atom kommt in PART 1, das andere in PART 2. Nach dem Teilen lassen sich die neu "erzeugten" Atome mit gedrückter '<c>UMSCHALTTASTE</c>' und der Maus an jede gewünschte Stelle ziehen. Der Befehl für das Tool **Aufteilen** ist '<c>mode split</c>'. '<c>ESC</c>' beendet den Modus.

## EADP
Teilt die Atome wie oben, belegt aber beide Atome mit einem Constraint auf gleiche ADPs. Nützlich am Anfang der Verfeinerung; sobald das Fehlordnungsmodell nahezu fertig ist, sollte er aber besser entfernt und stattdessen ein *DELU*-Restraint verwendet werden. Entspricht dem Befehl '<c>mode split -r=EADP</c>'.

## ISOR
Teilt die Atome wie oben und wendet auf jedes der beiden Atome einen *ISOR*-Restraint an. Der entsprechende Befehl ist '<c>mode split -r=ISOR</c>'.

## SIMU
Wie oben, aber mit einem *SIMU*-Restraint. Der Befehl dafür ist '<c>mode split -r=SIMU</c>'.


[comment]: < Help text for "Fit and Split Group" is now taken from toolbox_work.md. >
