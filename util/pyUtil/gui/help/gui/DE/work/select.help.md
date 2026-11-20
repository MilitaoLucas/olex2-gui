# Select-Atoms-help
# Select Atoms
Dieses Menü bietet mehrere, unterschiedlich gezielte Möglichkeiten, Atome auszuwählen oder die Auswahl aufzuheben. Mit '<c>ESC</c>' wird jederzeit die gesamte Auswahl aufgehoben.

## Exklusiv
Wählt nur Atome des angeklickten Elements aus.

## Zusatz
Fügt alle Atome des angeklickten Elements zur Auswahl hinzu.

## Beispiele für die Befehlszeile

| `sel $c` | Wählt alle C-Atome aus. |

| `sel -u` | Hebt die gesamte Auswahl auf. |

| `sel c1` | Wählt das Atom C1 aus. |

| `sel $c $n` | Wählt alle C- und N-Atome aus. |


# Selections
Sind Atome und/oder Bindungen ausgewählt, lösen die folgenden Links bestimmte Aktionen aus:

## Invertieren
|`sel -i`| Kehrt die aktuelle Auswahl um: alle Atome und Bindungen, die gerade *nicht* ausgewählt sind, werden stattdessen ausgewählt. |

## Auswahl aufheben
|`sel -u`| Hebt die Auswahl aller ausgewählten Atome auf. |

## Löschen
|`kill sel`| Löscht alle ausgewählten Atome, wie die Taste '<c>Entf</c>'. Mit '<c>CTRL+Z</c>' lässt sich das Löschen rückgängig machen. |

## Vorherige Auswahl
|`selback`| Wählt die zuvor ausgewählten Atome erneut aus. |


# Select-Criteria-help
# Select Criteria
Um Atome nach ihrem Uiso-Wert auszuwählen, im Auswahlmenü den Operator **>**, **<** oder **=** wählen und einen Uiso-Wert in das Feld eintragen. Ein Klick auf **Auswählen** wählt dann nur die Atome aus, die dieses Kriterium erfüllen.


# Select-Rings-help
# Select Rings
Wählt alle Ringe des angegebenen Typs in der Struktur aus, z.B. C6, C5N, C5 oder C5O. Andere Ringe lassen sich direkt in das Auswahlmenü eintippen: C3N2 findet z.B. alle Fünfringe aus drei Kohlenstoff- und zwei Stickstoffatomen (Imidazole und Pyrazole). Ein Klick außerhalb des Menüs hebt den angegebenen Ring hervor. (Die Links **Phenyl** und **Pyridin** sind als Abkürzung gedacht.)
