# Symmetry Tools
Dieser Bereich bietet Schaltflächen, um Aussehen und Lage der asymmetrischen Einheit zu ändern, eine Struktur auf dem Bildschirm zu vervollständigen, Basisvektoren und Elementarzelle anzuzeigen und Ähnliches.


# symmetry tools 1
Die Tools in dieser Zeile helfen, Teile einer Struktur mit mehreren Baueinheiten neu anzuordnen.

## In die Nähe schieben
Nützlich, um Baueinheiten einer Struktur nahe an ein bestimmtes Atom zu bringen.
<br>
<br>

  1. Das Atom anklicken, in dessen Nähe eine andere Baueinheit geschoben werden soll.
  2. Den Modus mit der Schaltfläche **Move Near** (oder '<c>mode move</c>') starten.
  3. Von jeder Baueinheit, die in die Nähe des zuerst ausgewählten Atoms geschoben werden soll, ein Atom anklicken.

| `mode move` | |

## In die Nähe kopieren
Ein etwas anderes Verfahren, um Baueinheiten einer Struktur nahe an einem bestimmten Atom zu sammeln.
<br>
<br>

  1. Das Atom anklicken, in dessen Nähe eine andere Baueinheit kopiert werden soll.
  2. Den Modus mit der Schaltfläche **Copy Near** (oder '<c>mode move -c</c>') starten.
  3. Von jeder Baueinheit, die in die Nähe des zuerst ausgewählten Atoms kopiert werden soll, ein Atom anklicken.

| `mode move -c` | |

## Zusammenfügen
| `compaq` | Bringt die einzelnen Fragmente einer Struktur auf dem Bildschirm so nah wie möglich zusammen. |

| `compaq -a` | Bringt die Fragmente wie oben zusammen und fügt zusätzlich "zerbrochene" Fragmente zusammen. |


# symmetry tools 2
Diese Schaltflächen zentrieren die Baueinheiten einer Struktur auf verschiedene Weise.

## Auf die Zelle zentrieren
| `move` | Alle Baueinheiten der Struktur werden in der Zelle zentriert. |

## Auf das größte Fragment zentrieren
| `move` | Alle Baueinheiten der Struktur werden auf die größte Baueinheit zentriert. |


# symmetry tools 3
Diese Tools schalten die Anzeige symmetriebezogener Elemente ein und aus.

## Basis anzeigen
| `basis` | Zeigt oder verbirgt die Basisvektoren der Struktur. |

## Zelle anzeigen
| `cell` | Zeigt oder verbirgt die Kanten der Elementarzelle. |

## Qualität
Mit dem Regler lässt sich die Qualität der Grafik von niedrig (ganz links) über mittel (Mitte) bis hoch (ganz rechts) einstellen. Eine niedrigere Qualität hilft, wenn der Rechner mit großen Strukturen Mühe hat.

| `qual -l` , `qual -m` , `qual -h` | Stellt die Grafikqualität auf niedrig, mittel oder hoch. |


# symmetry tools 4
Diese beiden wichtigen Befehle verkleinern bzw. erweitern den angezeigten Teil der Struktur.

## Fuse
| `fuse` | Zeigt nur die asymmetrische Einheit der Struktur. Alle durch Symmetrie erzeugten Atome werden entfernt. Ein grundlegend wichtiger Befehl. |

## Alles vervollständigen
| `grow` | Zeigt alle symmetrieäquivalenten Atome, die für die "vollständige" Struktur nötig sind. Bei polymeren Strukturen ist das etwas willkürlich, und es können gezieltere '<c>grow</c>'-Befehle nötig sein, um die Struktur wie gewünscht darzustellen. Weitere Möglichkeiten in der Hilfe zum Bereich **Vervollständigen**. |


[comment]: < Help text for "Growing" is now taken from toolbox_work.md. >


# Packing
Dieser Bereich bietet Möglichkeiten, die räumliche Packung einer Struktur darzustellen.


# Expand Short Contacts
Mit diesem Regler wird der Mindestabstand für "kurze Kontakte" zwischen Atomen festgelegt, etwa Wasserstoff- oder Halogenbrücken. Je weiter der Regler nach rechts geht, desto mehr anklickbare "Bindungen" erscheinen an Atomen, die das Kriterium erfüllen. Alternativ lässt sich eine Zahl in das Feld neben dem Regler eingeben. Ein Klick auf eine dieser "Bindungen" erweitert die Struktur in Richtung der Bindung.


# Pack Radius
Den Regler nach rechts schieben, um alle symmetrieäquivalenten Fragmente im angegebenen Radius um die aktuelle Struktur zu zeigen. Die Zahl lässt sich auch in das Feld neben dem Regler eingeben.


# Pack Limits
Packt eine oder mehrere Elementarzellen bis zu den angegebenen Grenzen, auch gebrochenen.

## Bis zu den Grenzen packen
Zeigt alle Fragmente der Struktur innerhalb der für die Zellkanten *a*, *b* und *c* festgelegten Grenzen. Die Zahlen im Feld sind Vielfache der Kantenlängen.

## Elementarzelle füllen
Zeigt nur die Atome innerhalb der Elementarzelle.

## Fragmente vervollständigen
Vervollständigt Fragmente, die durch die verschiedenen Packoptionen nur teilweise angezeigt werden. Oft nützlich nach dem Befehl **Elementarzelle füllen**.
