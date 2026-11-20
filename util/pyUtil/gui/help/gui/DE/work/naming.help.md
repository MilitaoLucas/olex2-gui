# naming-help
# Naming
In diesem Tool-Bereich werden die Atome eines Modells benannt. In manchen Fällen ist es allerdings bequemer, Atome effizienter über die Befehlszeile zu benennen.

## Die Benennungs-Tools
Ein Klick auf **Name** startet den Benennungsmodus. In diesem Modus erhält das erste angeklickte Atom sein Elementsymbol gemäß den Einstellungen in dieser Zeile, und alle danach angeklickten Atome werden fortlaufend weiter nummeriert. Mit '<c>ESC</c>' wird der Modus beendet, mit '<c>CTRL+Z</c>' die Benennung rückgängig gemacht.

Hinweis: In diesem Modus zeigt der Mauszeiger an, welchen Namen das nächste angeklickte Atom erhält.

### Start
Das erste angeklickte Atom erhält sein Elementsymbol und die Zahl in diesem Feld (meist 1).

### Suffix
Hängt ein optionales Suffix (z.B. A, _, ') an den Atomnamen an.

### Typ
Steht in diesem Feld ein Element, wird jedes angeklickte Atom in dieses Element umgewandelt, und alle anderen Einstellungen dieser Zeile werden angewendet. Steht hier kein Element, erhält jedes angeklickte Atom sein eigenes Elementsymbol.

## Über die Befehlszeile
|`name sel type`| Wandelt alle ausgewählten Atome in das unter *type* angegebene Element um, z.B. wandelt '<c>name sel N</c>' die ausgewählten Atome in Stickstoff um. |

|`name sel integer`| Nummeriert alle ausgewählten Atome in der Reihenfolge ihrer Auswahl neu, beginnend mit *integer*. Werden z.B. vier Kohlenstoffatome ausgewählt und '<c>name sel 3</c>' eingegeben, heißen sie in der Reihenfolge der Auswahl C3, C4, C5 und C6. |
<br>
<br>
'<c>CTRL+Z</c>' macht diese Änderungen rückgängig.


# Automatic Hydrogen Naming
Olex2 benennt alle Wasserstoffatome automatisch nach einem festen Schema. Sollen Wasserstoffatome besondere Namen erhalten, lässt sich diese Funktion mit dem Häkchen 'Automatische Benennung der Wasserstoffatome' abschalten.


# Match Naming
Enthält die Struktur zwei oder mehr äquivalente Fragmente, muss nur eines davon benannt werden: Olex2 kann das gleiche Benennungsschema auf die anderen übertragen. Das hilft bei Strukturen mit *Z*' > 1 und bei Strukturen, in denen ein Metallzentrum von mehreren gleichartigen Liganden koordiniert ist. Im zweiten Fall muss vor dem Benennen der äquivalenten Fragmente die maximale Zahl der Bindungen des Metalls auf 0 gesetzt werden: das Metall mit der rechten Maustaste anklicken und im Menü **Bonds** auf 0 setzen.
<br>
<br>

Alle Atome der ersten Baueinheit benennen. Im Feld **Suffix** ein Suffix eingeben; es wird an die Atomnamen einer zweiten, identischen Baueinheit angehängt. **Ein beliebiges Atom** der *ersten* Baueinheit anklicken, dann das **entsprechende Atom** der *anderen* Baueinheit(en). Ein Klick auf den Link **Äquivalente Fragmente (*Z*' > 1)** benennt alle Atome der zweiten Baueinheit nach dem Schema der ersten, mit angehängtem Suffix. Ist **Für die Überlagerung invertieren** angehakt, wird die zweite Baueinheit vor dem Benennen invertiert. Dieses Übertragen des Benennungsschemas lässt sich für jede weitere identische Baueinheit der Struktur wiederholen. Danach gegebenenfalls die Zahl der Bindungen am Metallzentrum wieder zurücksetzen.
<br>
<br>

Im Folgenden einige nützliche Befehle zum Benennen. Manche davon haben keine Entsprechung in der Oberfläche.

## Suffix anhängen
|`match sel -n=suffix`| Die Benennung durch Überlagern geht auch über die Befehlszeile. Zuerst zwei entsprechende Atome zweier identischer Baueinheiten auswählen. Dieser Befehl überträgt dann das Benennungsschema der ersten Baueinheit auf die zweite; an die Atomnamen der zweiten Baueinheit wird das Zeichen *suffix* angehängt. So hängt '<c>match sel -n=A</c>' das Suffix 'A' an die Namen der zweiten Baueinheit an. |

## Suffix ersetzen
|`suffix'>match sel -n=$suffix`| Ähnlich wie *Suffix anhängen*. Statt ein Suffix anzuhängen, ersetzt dieser Befehl aber das erste Zeichen des ursprünglichen Benennungsschemas durch ein anderes Zeichen. Das ist z.B. nützlich, wenn die Kohlenstoffatome eines Liganden C101, C102, C103 ... heißen und die entsprechenden Atome des anderen Liganden C201, C202, C203 ... heißen sollen.|

## Letztes Zeichen ersetzen
|`suffix'>match sel -n=-suffix`| Wie bei *Suffix ersetzen*, nur wird das letzte Zeichen des Atomnamens ersetzt. |

