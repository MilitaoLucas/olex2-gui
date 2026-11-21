# toolbox work-target
Eine Sammlung nützlicher Tools
- Alle Peaks zu Kohlenstoff machen
- Atome verschieben
- Peaks anzeigen/ausblenden
- Kurze Kontakte erweitern
- Peak-Regler
- Fehlordnungs-Tools

# change_element-target
Atomtypen ändern in&nbsp;


# anis-target
Ausgewählte Atome anisotrop machen. Ist nichts ausgewählt, werden alle Atome umgewandelt.


# isot-target
Ausgewählte Atome isotrop machen. Ist nichts ausgewählt, werden alle Atome umgewandelt.


# QC-target
Alle Q-Peaks in C umwandeln


# QH-target
Alle Q-Peaks in H umwandeln


# tidy-target
Die Struktur aufräumen. Nur am Anfang der Verfeinerung empfohlen!


# killH-target
Löscht alle H-Atome aus dem Modell. Rückgängig mit CTRL+Z.


# Q-target
Zwischen drei Zuständen umschalten: Q-Peaks anzeigen, Q-Peaks mit Bindungen anzeigen oder Q-Peaks ausblenden


# H-target
Zwischen drei Zuständen umschalten: Wasserstoffatome anzeigen, Wasserstoffatome mit Wasserstoffbrücken anzeigen oder Wasserstoffatome ausblenden


# center-target
Die Struktur auf dem Bildschirm zentrieren und die Vergrößerung anpassen


# ok-target
Die chemische Formel an das Modell anpassen. Der Wert von Z' wird berücksichtigt, also prüfen!


# disorder tools-target
Tools für fehlgeordnete Strukturen


# peak & Uiso sliders-target
Regler zur Auswahl von Q-Peaks und Atomen


# growing-target
Die Struktur auf dem Bildschirm vervollständigen


# finishing-target
Tools zum schnellen Sortieren der Atome und Erstellen von Bildern


# Labels
Die Beschriftungen in der Modellanzeige lassen sich anpassen. Trifft eine Eigenschaft auf kein Atom zu, erscheint keine Beschriftung; wird z.B. '<c>labels -o</c>' (siehe unten) eingegeben und alle Atome haben die Besetzung 1, wird kein Atom beschriftet.

| `help labels` | Zeigt alle Optionen des Befehls '<c>labels</c>'. |

### Atomnamen
| `labels -l` | Die Namen aller *Nicht-Wasserstoffatome* erscheinen neben den Atomen. |

### Kristallographische Besetzung
| `labels -o` | Zeigt die kristallographische Besetzung aller Atome, die nicht zu 100% besetzt sind, deren Besetzung also nicht 1 ist. |

### Chemische Besetzung
| `labels -co` | Beschriftet Atome mit ihrer "chemischen Besetzung", wenn sie kleiner als 1 ist. Im Grunde wie **Kristallographische Besetzung** oben, nur ohne die Besetzungen von Atomen auf Symmetrieelementen. |

### PARTs
| `labels -p` | Zeigt die PART-Nummern aller Atome, die nicht in PART 0 sind. |

### Kopplungscode
| `labels -lo` | Sind die Besetzungen von Atomen gekoppelt, erscheinen ihre Kopplungscodes (FVAR 21/-21 in der Sprache von ShelXL). |

### Fixierte Parameter
| `labels -f` | Beschriftet alle Atome mit fixierter Besetzung, gleich welchen Wert die Besetzung hat. |

### Variablen
| `labels -v` | Zeigt alle Atome, deren Besetzung an eine Variable gekoppelt ist. |

### AFIX-Befehle
| `labels -a -h` | Nützlich, um die auf die Struktur angewendeten AFIX-Befehle zu prüfen. |

### Intensitäten der Q-Peaks
| `labels -qi` | Die relativen Intensitäten der Q-Peaks erscheinen an der Struktur. |

### Ueq
| `labels -u` | Beschriftet Atome mit ihren Ueq-Werten. |

### Atomname + Residuennummer
| `labels -l -rn` | Zeigt Atomname und Residuennummer. |

### Residuennummern
| `labels -rn` | Zeigt die Nummer des Residuums, zu dem ein Atom gehört. |

### Residuenklasse
| `labels -rc` | Zeigt die Klasse des Residuums, zu dem ein Atom gehört. |

## H benennen
Ist dieses Feld angehakt, werden *nach* einer Wahl im Auswahlmenü **Atomnamen** auch Wasserstoffatome beschriftet (standardmäßig nicht).

### Namen der H-Atome
| `labels -h -l` | Beschriftet alle Atome einschließlich der Wasserstoffatome sowie die Q-Peaks mit ihren Namen. |

## Ausblenden
Blendet die Beschriftungen von Atomen und Q-Peaks aus. Auch andere Beschriftungen (z.B. Besetzungen, AFIX-Codes) werden abgeschaltet. '<c>F3</c>' schaltet die Beschriftungen von Atomen und Q-Peaks ein und aus.


# Toolbar Model
Drei grundlegende Tools für den Modellbau.

## Atomtypen zuweisen
Jedes Element der aktuellen Formel hat eine kleine Schaltfläche.

### Über die GUI
| $spy.MakeElementButtonsFromFormula('mode') | Alle Atome des Modells werden gezeigt. Die Schaltfläche '...' öffnet das Periodensystem, wenn weitere Elemente gebraucht werden. |

Ein Klick auf eine Elementschaltfläche startet den Zuweisungsmodus für dieses Element. In diesem Modus werden alle angeklickten Atome oder Q-Peaks in dieses Element umgewandelt. '<c>ESC</c>' beendet den Modus. Alternativ zuerst Atome auswählen und dann eine Elementschaltfläche anklicken: alle ausgewählten Atome werden zu diesem Element. Die Schaltflächen dieser Zeile sind rot oder blau, wenn die Zahl der Atome dieses Elements im Modell nicht mit der Summenformel übereinstimmt, und grün, wenn sie stimmt.

### Über die Befehlszeile
Meist ist es viel effizienter, Elemente über die Tastatur zuzuweisen. Drei häufig verwendete Befehle:

| `name sel C` | Macht alle ausgewählten Atome zu Kohlenstoff. |
| `mode name C` | Startet den Benennungsmodus; in diesem Modus werden alle angeklickten Atome zu Kohlenstoff. |
| `name \$Q C` | Macht alle Q-Peaks zu Kohlenstoff. |

Hinweis: Ist das Feld in dieser Zeile angehakt, wird beim Klick auf eine der folgenden Schaltflächen sofort ein Verfeinerungszyklus ausgeführt:

## H hinzufügen – Wasserstoffatome geometrisch setzen
Diese Schaltfläche setzt Wasserstoffatome geometrisch an die ausgewählten Atome. Ist nichts ausgewählt, werden Wasserstoffatome an alle möglichen Atome gesetzt, um die Struktur zu vervollständigen.

| `hadd` | Fügt Wasserstoffatome an die ausgewählten Atome an (oder an alle, wenn keine ausgewählt sind). |
| `hadd 137` | Verwendet das angegebene AFIX, **wenn möglich**. (137 fügt z.B. drei Wasserstoffatome an eine Methylgruppe an.) |
| `hadd -137` | Lässt die Konnektivität das angegebene AFIX nicht zu, kann man die Atome trotzdem so setzen: *zuerst* das Atom auswählen, an das Wasserstoffatome kommen sollen, dann ein zweites Atom, das einen Vektor festlegt. |

## Atome anisotrop machen
Die Ellipsoid-Schaltfläche macht die ausgewählten Atome anisotrop. Ist nichts ausgewählt, gilt das für alle Atome.

| `anis` | Alle ausgewählten Atome werden **anisotrop** verfeinert (es entstehen Ellipsoide). |

## Atome isotrop machen
Die Kugel-Schaltfläche macht die ausgewählten Atome isotrop. Ist nichts ausgewählt, gilt das für alle Atome.

| `isot` | Alle ausgewählten Atome werden **isotrop** verfeinert (es entstehen Kugeln). |


# Quicktools
Weitere nützliche Tools für den Modellbau.

## Typ und Anzeige von Atomen ändern
| `name \$Q C` | $spy.MakeHoverButton('toolbar-QC','name \$Q C') | Macht alle angezeigten Elektronendichte-Peaks (Q-Peaks) unabhängig von ihrer Höhe zu Kohlenstoffatomen. |

| `name \$Q H` | $spy.MakeHoverButton('toolbar-QH','name \$Q H') | Alle sichtbaren Q-Peaks werden zu Wasserstoff. |

| `clean` | $spy.MakeHoverButton('toolbar-tidy','clean') | Räumt die Struktur auf: kleine und geometrisch unmögliche Peaks werden entfernt, alle übrigen werden zu Kohlenstoff. |

| `kill \$H` | $spy.MakeHoverButton('toolbar-killH','kill \$H')  | Löscht alle ausgewählten Wasserstoffatome aus der Struktur. Sind keine Wasserstoffatome ausgewählt, werden alle gelöscht. Rückgängig mit '<c>CTRL+Z</c>'. |

| `showQ` | $spy.MakeHoverButton('toolbar-Q','showQ') | '<c>CTRL+Q</c>'. Schaltet zwischen drei Zuständen um: Elektronendichte-Peaks anzeigen, mit Bindungen zu benachbarten Atomen anzeigen oder ausblenden. |

| `showH` | $spy.MakeHoverButton('toolbar-H','showH') | '<c>CTRL+H</c>'. Schaltet zwischen drei Zuständen um: H-Atome anzeigen, mit Wasserstoffbrücken anzeigen oder ausblenden. Die Wasserstoffatome bleiben unabhängig von der Anzeige im Modell. |

| `compaq>>compaq-a>>center` | $spy.MakeHoverButton('toolbar-center','compaq>>compaq -a>>center') | Fragmente werden zusammengefügt und die Struktur auf dem Bildschirm zentriert. |

## Die Formel der Struktur festlegen
| *Z*'= | Hier den Wert von *Z*' setzen. (*Z*' ist die Zahl der Formeleinheiten in der asymmetrischen Einheit.) Bei einer Molekülstruktur ist *Z*' meist 1. Sind zwei unabhängige Moleküle auf dem Bildschirm, muss *Z*' auf 2 gesetzt werden. Liegt das Molekül auf einem Symmetrieelement und muss "vervollständigt" werden (also durch Symmetrieoperationen erweitert, siehe Bereich **Vervollständigen** unten), ist *Z*' kleiner als 1, oft 0.5. |

| `fixunit` | $spy.MakeHoverButton('toolbar-OK','fixunit') | Passt die Summenformel an die Atome an, die gerade im Modell sind, unter Berücksichtigung von *Z*'. |


# Electron Density Quick Maps
Dieser Bereich bietet die Berechnung verschiedener Elektronendichtekarten, die sich mit den Tools hier in verschiedenen 2D- oder 3D-Formen darstellen lassen. Nähert sich das **Niveau** (siehe Hilfe zum Bereich **Maps**) null, werden die Karten allerdings sehr unübersichtlich und langsam, daher zeigt Olex2 diese Bereiche nicht.

## Verfügbare Karten
### diff
Zeigt die Differenzkarte Fobs-Fcalc. Damit sie richtig erscheint, im Auswahlmenü **View** des Bereichs **Maps** (über **Karteneinstellungen** in diesem Bereich) **surface**, **wire** oder **points** wählen. Der entsprechende Befehl ist '<c>CalcFourier -diff -r=0.1 -m</c>' oder einfach '<c>CTRL+M</c>'. Ein äußerst wichtiges Tool, um die Gültigkeit eines Modells zu prüfen. Rote Bereiche der Karte stehen für fehlende, grüne für überschüssige Elektronendichte. Bei einem genauen Strukturmodell sind rote wie grüne Bereiche sehr klein.

### Fcalc
Zeigt die berechnete Elektronendichte.

### 2Fo-Fc
Zeigt die Karte 2Fobs-Fcalc.

### Fobs
Zeigt die Karte der gemessenen Elektronendichte.

### Deformation
Zeigt eine Deformationsdichtekarte (Abweichungen vom Modell sphärischer Atome).

### PDF
Zeigt eine Karte der Wahrscheinlichkeitsdichtefunktion, um die Qualität einer anharmonischen Verfeinerung zu beurteilen.

## Karte anzeigen
Schaltet die Anzeige der gewählten Karte ein.

## Karte ausblenden
Schaltet die Anzeige der gewählten Karte aus.

## Karteneinstellungen
Öffnet den Bereich **Maps** unter **Tools**, um die Kartenanzeige weiter anzupassen.


# Disorder Tools
Äußerst nützliche Befehle für kristallographische Fehlordnung.


# PART Links
Tools, um ausgewählte PARTs der Struktur anzuzeigen. Die entsprechenden Befehle sind ebenfalls sehr nützlich:

| `showp 0 1` | Zeigt alle Atome ohne bestimmten PART (also in PART 0) und alle Atome in PART 1. |

| `showp 0 2` | Zeigt alle Atome ohne bestimmten PART (also in PART 0) und alle Atome in PART 2. |

| `showp 1` | Zeigt nur die Atome von PART 1. |

| `showp` | Zeigt alle Atome aller PARTs. |

| `sel part 1` | Wählt alle Atome in PART 1 aus. |
<br>
<br>

Für jeden PART der Struktur gibt es eine Schaltfläche **0&#124;n**: zuerst die positiven PARTs, dann die negativen (spezielle Lagen), z.B. **0&#124;1**, **0&#124;2**, **0&#124;-1**. Ein Klick zeigt PART 0 zusammen mit diesem PART.
<br>
<br>

Ist beim Klick auf eine Schaltfläche **0&#124;n** das Feld **Sel** angehakt, werden die Atome dieses PARTs in der Anzeige ausgewählt. Ist **Col** angehakt, erhält jeder PART eine eigene Farbe, und die Schaltflächen zeigen dieselben Farben (siehe **PART-Farben**). Ist **Unique** angehakt, erscheint eine Liste der unabhängigen Atome der Struktur in der Ausgabe. Die Atome werden mit der im Auswahlmenü gewählten Größe markiert: **Occupancy** zeigt die Besetzung teilweise besetzter Lagen als Dezimalzahl, **Chem Occ.** die chemische Besetzung jeder teilweise besetzten Lage, **Link-Code** den Kopplungscode gekoppelter Besetzungen im SHELX-Format, **PART No** die PART-Nummern ungleich null und **Labels** die Atomnamen.
<br>
<br>

Besonders nützlich ist hier die Pfeiltaste **NACH OBEN**, um zuletzt eingegebene Befehle zu wiederholen!
<br>
<br>

Verwendet die Struktur mehr PARTs als nötig (z.B. 1/2, 3/4, 5/6 für Fehlordnungen, die sich nie berühren), kann die Schaltfläche **Sanitise** neben den freien Variablen sie neu nummerieren; siehe die Hilfe zur Zeile der freien Variablen.

## PART-Farben
Ist **Col** angehakt, erhält jeder PART eine eigene Farbe, in der 3D-Ansicht und auf seiner Schaltfläche **0&#124;n**. Jede PART-Nummer hat eine Farbe, auch PARTs über 6 und negative PARTs. Die Farben stammen aus einer *Palette*; die Wahl bleibt über Sitzungen hinweg erhalten. Ein Klick legt die Palette fest:

| `spy.part_palette contrast` | **Contrast** (Standard): jedes PART-Paar in einer anderen Farbfamilie: 1/2 Himmelblau und Bernstein, 3/4 Jade und Himbeere, 5/6 Violett und Petrol, 7/8 Terrakotta und Pistazie; negative PARTs in dunkleren, ruhigeren Farben (Pflaume, Oliv, Waldgrün, Orchidee). Am besten bei vielen PARTs. |

| `spy.part_palette blues` | **Blues**, Ton in Ton: jedes Paar ein Blau, dunkel und hell; das nächste Paar ein benachbartes Blau (Himmelblau, Indigo, Petrol). |

| `spy.part_palette greens` | **Greens**, Ton in Ton: Jade, Moos, Minze, Oliv. |

| `spy.part_palette warm` | **Warm**, Ton in Ton: Terrakotta, Bernstein, Koralle, Ocker. |

| `spy.part_palette berry` | **Berry**, Ton in Ton: Himbeere, Pflaume, Rosé, Violett. |

| `spy.part_palette earth` | **Earth**, Ton in Ton und ruhig: Sand, Salbei, Ton, Oliv. Gut für Abbildungen, die gedruckt werden. |
<br>
<br>

Alle Paletten folgen denselben Regeln:
- Die beiden PARTs eines Paars (1/2, 3/4, ...) unterscheiden sich in Helligkeit und Farbe, sodass sie auch im Graudruck und von Farbenblinden unterschieden werden können.
- Kein PART sieht aus wie die Atome um ihn herum: Kohlenstoff grau, Wasserstoff weiß, Stickstoff blau, Sauerstoff rot.
- Ein negativer PART sieht nie aus wie der positive PART derselben Nummer.
<br>
<br>

Die Ton-in-Ton-Paletten sind ruhig und wirken gut in Abbildungen, ihre Paare sind aber absichtlich ähnlich; sie passen daher zu Strukturen mit ein oder zwei PART-Paaren. Bei mehr PARTs **Contrast** verwenden.


# Free Variables
Diese Zeile zeigt die freien Variablen des Modells (**FVAR** in SHELX): **2:** ist die zweite freie Variable usw. (die erste ist der Gesamt-Skalenfaktor). Eine freie Variable koppelt meist die Besetzungen der beiden PARTs einer Fehlordnung so, dass ihre Summe 1 ist: Atome in einem PART verweisen auf sie als '21' (Besetzung = FV 2), Atome im anderen als '-21' (Besetzung = 1 - FV 2).

## Sanitise
Eine Schaltfläche **Sanitise** erscheint, wenn sich das Modell aufräumen lässt: wenn freie Variablen denselben Wert haben, wenn eine das Komplement einer anderen ist (z.B. 0.8 und 0.2: nur die Reihenfolge der PARTs ist verschieden) oder wenn andere PARTs als 1/2 verwendet werden. Das aktuelle Modell wird zuerst in die Datei geschrieben und als Sicherung im Ordner **olex2** der Struktur aufbewahrt (*name*_before_sanitise_1.res, dann _2 ...); dann folgen zwei Fenster.
<br>
<br>

**Freie Variablen.** Variablen, die innerhalb von 0.03 übereinstimmen, erscheinen als Gruppe, jede mit ihrem Wert und ihrer Verwendung (Residuum, PARTs, Zahl der Atome). Die anhaken, die eine einzige Variable werden sollen; die niedrigste angehakte Nummer bleibt, und bei einem Komplement wechselt das Vorzeichen seiner Verweise ('81' wird zu '-21'). Variablen, die kein Atom verwendet, werden entfernt, die übrigen neu nummeriert. Um eine Gruppe als zwei getrennte Paare zusammenzuführen, ein Paar anhaken und dann für das andere erneut **Sanitise** drücken.
<br>
<br>

Ähnliche Werte beweisen nicht, dass zwei Fehlordnungen gekoppelt sind: das Zusammenführen besagt, dass sie sich gemeinsam bewegen, und das kann R1 nicht zeigen. Nur zusammenführen, wo es chemisch sinnvoll ist; z.B. Variablen verschiedener Moleküle abhaken, wenn deren Fehlordnungen unabhängig sind.
<br>
<br>

**PARTs.** Jedem Fehlordnungspaar wird PART 1/2 angeboten (der PART mit dem positiven Verweis wird 1). Zwei Paare können nur dann dieselben PART-Nummern teilen, wenn ihre Atome nicht miteinander binden würden, denn Atome binden innerhalb desselben PARTs; wo sie es würden, behält oder erhält das Paar die nächsten freien Nummern, 3/4, und das Fenster sagt, warum. Ein Paar abhaken, um es so zu lassen, wie es ist. **Leave PARTs** übernimmt die Änderungen der freien Variablen ohne Neunummerierung.
<br>
<br>

Unverändert bleiben: PART 0, negative PARTs, PARTs mit fixierter Besetzung, in *BIND* genannte PARTs und freie Variablen, die außerhalb von Besetzungen verwendet werden (in Koordinaten, U-Werten, *DFIX*, *SUMP* ...). Nach **Sanitise** verfeinern.


# Fit and Split Group
Die Tools *Anpassen* und *Aufteilen* wirken auf ein oder mehrere ausgewählte Atome. Ein Atom (oder eine Atomgruppe) *anpassen* heißt, es an eine gewünschte Stelle im Modell zu verschieben. Ein Atom (oder eine Gruppe) *aufteilen* heißt, es durch ein Duplikat in zwei Teile zu teilen, das dann an eine gewünschte Stelle verschoben werden kann, z.B. um eine Fehlordnung zu modellieren.

## Ein Atom anpassen oder aufteilen
Ein Atom mit links anklicken, um es hervorzuheben. Zum *Anpassen* die Schaltfläche **Anpassen** anklicken. Die Farbe des Atoms ändert sich. Dann mit gedrückter '<c>UMSCHALTTASTE</c>' das Atom mit der linken Maustaste an die gewünschte Stelle ziehen. '<c>ESC</c>' beendet den Modus **Anpassen/Aufteilen**; das *angepasste* Atom bleibt an seiner neuen Stelle.
<br>
<br>

Zum *Aufteilen* in zwei Atome die Schaltfläche **Aufteilen** anklicken. Die Farbe des Atoms ändert sich wie zuvor, beim Ziehen mit gedrückter '<c>UMSCHALTTASTE</c>' bewegt sich aber nur EINES der beiden durch **Aufteilen** erzeugten Atome (das andere lässt sich wie oben mit einem eigenen **Anpassen** verschieben). Die Besetzungen der beiden Atome sind gekoppelt, und die Atome haben nun verschiedene PART-Nummern. '<c>ESC</c>' beendet den Modus **Anpassen/Aufteilen**; das verschobene Atom bleibt an seiner Stelle.

## Zwei Atome anpassen oder aufteilen
Zwei Atome auswählen und dann **Anpassen** oder **Aufteilen** anklicken. **Aufteilen** erzeugt ein Duplikat-Paar, **Anpassen** nicht. Die Farbe der Atome ändert sich. Die Atome mit gedrückter '<c>UMSCHALTTASTE</c>' mit der Maus ziehen, um sie gemeinsam an die gewünschte Stelle zu verschieben.
<br>
<br>

Um die Atome um ihren Mittelpunkt zu drehen statt sie zu verschieben, beim Ziehen die '<c>CTRL</c>'-Taste gedrückt halten. '<c>ESC</c>' beendet den Modus **Anpassen/Aufteilen**; das verschobene Atompaar bleibt an seiner Stelle.

## Drei oder mehr Atome anpassen oder aufteilen
Drei oder mehr Atome auswählen und dann **Anpassen** oder **Aufteilen** anklicken. Wie zuvor erzeugt **Aufteilen** eine Duplikat-Gruppe, **Anpassen** nicht, und die Atome ändern ihre Farbe. Die ganze Gruppe lässt sich mit gedrückter '<c>UMSCHALTTASTE</c>' an jede gewünschte Stelle ziehen (oder mit gedrückter '<c>CTRL</c>'-Taste drehen).
<br>
<br>

Die Gruppe lässt sich auch um eine ihrer Bindungen drehen. Dazu zuerst die Bindung, um die gedreht werden soll, mit einem *Rechtsklick* *aktivieren*. Dann dreht Ziehen mit gedrückter '<c>CTRL</c>'-Taste die Gruppe um diese aktivierte Bindung. '<c>ESC</c>' beendet den Modus; verschobene Atome bleiben an ihren neuen Stellen.

## Aufteilen mit SAME
Eines der mächtigsten Tools in Olex2. Ist eine Atomgruppe fehlgeordnet und lässt sich einer der Teile modellieren (gleich wie schlecht), ist die Schaltfläche **Aufteilen** mit dem Restraint **SAME** sehr nützlich. ('<c>mode fit -s same</c>' entspricht einem Klick auf **Aufteilen** mit diesem Restraint.) Beim Aufteilen einer Gruppe wendet Olex2 standardmäßig den Restraint **SAME** an; andere Restraints lassen sich im Auswahlmenü wählen. Alles wird mit Restraints belegt; lässt sich die Fehlordnung modellieren, löst die Verfeinerung sie also automatisch auf, auch wenn manchmal viele Verfeinerungszyklen nötig sind.

## Aufteilen mit RIGU
Wie **Aufteilen mit SAME**, nur wird beim Aufteilen einer Gruppe stattdessen der "Rigid-Bond"-Restraint *RIGU* angewendet. Mehr zu *RIGU* in der Hilfe zum Bereich **SHELX-kompatible Restraints**.

## Aufteilen mit SAME, RIGU
Wie oben, nur werden beim Aufteilen einer Gruppe die Restraints *SAME* und *RIGU* angewendet.


[comment]: < Help text for "Show/Hide the list of restraints" is now taken from FragmentDB.md. >


# Peak & Uiso Sliders
Tools, um Q-Peaks und Atome nach ihren Eigenschaften auszuwählen.


# Electron Density Peak Slider
Mit diesem Tool lassen sich Q-Peaks nach ihrer Intensität auswählen.
<br>
<br>

Von der Mitte der Skala bei 100 ausgehend den Regler **Peaks** nach *links* schieben, um zuerst die schwächsten Q-Peaks auszublenden, oder nach *rechts*, um zuerst die stärksten auszublenden. Befehle nach dem Filtern wirken nur auf die noch sichtbaren Peaks. So macht der Befehl '<c>name $Q C</c>' alle sichtbaren Q-Peaks zu Kohlenstoff, und **Auswählen** oder **Löschen** wählt die Peaks aus bzw. löscht sie.


# Uiso Select Slider
Mit diesem Tool lassen sich Atome nach ihrem Uiso-Wert auswählen.

## Nach RECHTS schieben
Von der Mitte der Skala ausgehend den Uiso-Regler nach *rechts* schieben, um Atome auszuwählen, deren Uiso-Wert *größer* ist als der Wert neben dem Regler.

| `sel atoms where xatom.uiso < 0.02` | Wählt alle Atome mit einem Uiso-Wert kleiner als 0.02 aus. |

## Nach LINKS schieben
Von der Mitte der Skala ausgehend den Uiso-Regler nach **links** schieben, um Atome auszuwählen, deren Uiso-Wert KLEINER ist als der Wert neben dem Regler.

| `sel atoms where xatom.uiso > 0.04` | Wählt alle Atome mit einem Uiso-Wert größer als 0.04 aus. |


# Growing
Olex2 zeigt standardmäßig die asymmetrische Einheit. Dieser Bereich bietet sehr mächtige Techniken, um ein Strukturmodell auf dem Bildschirm genau wie gewünscht "zusammenzusetzen". Danach lässt sich das Modell in Olex2 beliebig oft verfeinern, ohne diese Anordnung aufzulösen.


# Grow
## Vervollständigen
*Vervollständigen* steht hier allgemein dafür, dem Modell auf dem Bildschirm systematisch Atome hinzuzufügen, z.B. symmetrieäquivalente Atome, um ein ganzes Molekül zu zeigen, wenn die asymmetrische Einheit wegen *Z*' < 1 nur einen Teil davon zeigt.

### Alles vervollständigen
| `grow` | Erzeugt alle "fehlenden" verbundenen symmetrieäquivalenten Atome. Meist genügt das, um eine asymmetrische Einheit zu einem vollständigen Molekül zu erweitern. |

### Schalen
| `grow -s` | Fügt Atome in konzentrischen Schalen um die gerade angezeigte Struktur hinzu. |

### Vollständig
| `grow -w` | Erzeugt alle fehlenden symmetrieäquivalenten Atome einer bereits vervollständigten Struktur, gleich ob sie an das Hauptfragment gebunden sind oder nicht. So erscheinen auch symmetrieäquivalente Lösungsmittelmoleküle und Gegenionen, die ein einfaches '<c>grow</c>' nicht erzeugt. |

### Asymmetrische Einheit
| `fuse` | Entfernt alle symmetrieäquivalenten Atome und zeigt die asymmetrische Einheit. Einer der wichtigsten Befehle in Olex2. |

### Angezeigte Vervollständigungsbindungen ausführen
| `grow -b` | Zeigt in einem Vervollständigungsmodus die anklickbaren "Bindungen" (siehe **Modus Vervollständigen** unten). Ein Klick auf eine dieser Bindungen vervollständigt die Struktur. |

## Modus Vervollständigen
| `mode grow` | Ähnlich wie '<c>grow</c>', aber der Befehl wird erst beim Anklicken eines Objekts ausgeführt. Im Vervollständigungsmodus wachsen anklickbare "Bindungen" aus den Atomen, die die gewählten Bedingungen erfüllen. |

Für diesen Befehl gibt es verschiedene Zusätze:

### Kurze Kontakte
| `mode grow -s` | Zeigt anklickbare "Bindungen" zu Atomen, die "kurze Wechselwirkungen" (z.B. Wasserstoffbrücken) mit der angezeigten Struktur eingehen. |

### Auswahl
| `mode grow -r` | Zeigt anklickbare "Bindungen" zu anderen Vorkommen der ausgewählten Atome. |

### Van-der-Waals-Radien
| `mode grow -v 2.0` | Zeigt anklickbare "Bindungen" zu anderen Vorkommen der ausgewählten Atome, die höchstens 2.0 &Aring; vom ausgewählten Atom entfernt sind. |

### Verschieben
| `mode grow -a` | Beim Klick auf eine anklickbare "Bindung" wird das symmetrieäquivalente Atom an die neue Stelle verschoben. Sehr nützlich, um bei ausgedehnten Strukturen (Polymeren) eine sinnvolle asymmetrische Einheit zusammenzusetzen. |

### Schalen
| `mode grow shells` | Zeigt anklickbare "Bindungen", mit denen die Struktur in konzentrischen Schalen nach außen vervollständigt wird. |

## Zusammenfügen
Genau genommen gehört dieses Tool nicht zur Familie **Vervollständigen**, wird aber oft zusammen mit ihr verwendet. Es ordnet die Teile der asymmetrischen Einheit für eine kompaktere oder chemisch sinnvollere Darstellung des Modells neu an, oft nach einem '<c>grow</c>'.

### Zerbrochene Fragmente
| `compaq -a` | Manchmal "zerbricht" ein Modell: Teile, die gebunden sein sollten, erscheinen als getrennte Fragmente. Dieses Tool fügt sie wieder zusammen. |

### Atom an Atom
| `compaq -c` | Wie **Zerbrochene Fragmente**, aber mit einem anderen Verfahren zum Zusammenfügen. |

### Metall zuletzt
| `compaq -m` | Metallionen werden zunächst aus dem Zusammenfügen herausgenommen (sehr nützlich beim Zusammensetzen eines Liganden!) und danach im kürzestmöglichen Abstand zu den übrigen Atomen gesetzt. |

### Peaks
| `compaq -q` | Verschiebt alle Elektronendichte-Peaks so nah wie möglich an vorhandene Atome. |


# Finishing
Die Schaltflächen in diesem Bereich bieten schnellen Zugriff auf einfache Fassungen der Sortier- und Zeichen-Tools, die es an anderer Stelle in Olex2 ausführlicher gibt.


# QuickSort
Die Schaltfläche **Mit aktuellen Einstellungen sortieren** sortiert die Atome des Modells nach den Optionen im Bereich **Sortierung**. Das Stiftsymbol öffnet den Bereich **Sortierung**, in dem sich die Sortiereinstellungen bearbeiten lassen.


# QuickImages
Die Schaltfläche **Ausgewählt** beschriftet ausgewählte Atome und Bindungen des Modells. Ist nichts ausgewählt, werden alle Atome und Bindungen beschriftet. **non-H** beschriftet alle Nicht-Wasserstoffatome, **Keine Atomnamen** entfernt alle Beschriftungen. Die Schaltfläche **Los** erstellt ein Bild des beschrifteten Modells im aktuellen Arbeitsordner. Alle Optionen für Bilddateien bearbeitet man im Bereich **Bilder**, den das Stiftsymbol neben **Los** öffnet.


[comment]: < The text below is legacy help documentation that doesn't seem to be used anywhere. >


# shift-move-target
Atome verschieben
- UMSCHALTTASTE gedrückt halten
- Atome mit der linken Maustaste verschieben
Atome aufteilen
- Ein Atom anklicken, um es aufzuteilen

# FVAR Display

Hier stehen die freien Variablen (FVAR) der Verfeinerung. Es gibt immer mindestens eine, die intern für die Gesamtskalierung verwendet wird.
<br>
<br>

Weitere freie Variablen lassen sich hinzufügen; sie dienen meist der "gekoppelten" Verfeinerung fehlgeordneter Teile. Ist z.B. eine Gruppe über zwei Lagen fehlgeordnet, muss die Gesamtzahl jedes Atoms dieser Gruppe 1 sein. Gleichzeitig müssen alle Atome jeder Lage dieselbe Besetzung haben. Mit einer freien Variablen lässt sich das recht einfach erreichen: Haben alle Atome in PART 1 die Besetzung FVAR 2, müssen alle Atome in PART 2 die Besetzung (1 - FVAR 2) haben. FVAR 2 ist einfach die zweite freie Variable der Liste.
<br>
<br>

Bei den meisten Fehlordnungen genügt eine solche zusätzliche freie Variable. Manchmal sind aber auch zwei oder drei nötig.
<br>
<br>

HINWEIS: Werden die Werte freier Variablen einander ähnlich, ist das ein Zeichen, dass zu viele verwendet wurden.
