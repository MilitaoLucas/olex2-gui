[comment]: < German translation of ../symdisorder.help.md; '#' headings are help IDs and stay English. Messages in the table stay English, as Olex2 prints them. >

# Symmetry Disorder Display
Für Bilder von Strukturen, in denen eine Gruppe durch Symmetrie fehlgeordnet ist, z.B. ein Ring auf einer Spiegelebene. Dann gibt es in der asymmetrischen Einheit nur einen Satz Atome, ohne PARTs zur Auswahl, und das Vervollständigen der Struktur zeigt alle Orientierungen auf einmal. Diese beiden Tools vervollständigen die Fragmente auf dem Bildschirm und trennen eine stimmige Orientierung von der anderen, sodass sie sich anders darstellen lässt.

Sie ändern die Anzeige, nicht das Modell: nichts hier beeinflusst die Verfeinerung.

## Ein Bild erstellen
1. Die Struktur wie gewünscht vervollständigen (oder gar nicht), dann **Fragmente vervollständigen** anklicken.
2. Ein beliebiges Atom einer fehlgeordneten Gruppe in der Orientierung anklicken, die bleiben soll. Bei mehreren Molekülen, jedes für sich fehlgeordnet, in jedem ein Atom anklicken.
3. **Andere Orientierung gruppieren** anklicken.

Die andere Orientierung hat jetzt ein eigenes Aussehen, nach dem Material der Gruppe *dp1*.

## Fragmente vervollständigen
Vervollständigt jedes Fragment auf dem Bildschirm, gleich wie die Struktur vervollständigt wurde: genau die fehlenden Atome kommen hinzu, nichts sonst, und nichts wird entfernt. Ein Molekül auf einer speziellen Lage wird ganz. Wird nur die asymmetrische Einheit gezeigt, erscheinen ihre Fragmente vollständig.

Ein Metall wird nie hinzugefügt: verbrückende Liganden sind auf der anderen Seite vollständig, das Metall dahinter bleibt weg.

Olex2 kehrt zuerst zur asymmetrischen Einheit zurück (*fuse*) und erzeugt dann genau die nötigen Atome.

## Andere Orientierung gruppieren
Ein Atom einer fehlgeordneten Gruppe auswählen. Die Orientierung dieses Atoms bleibt, wie sie ist. Die andere Orientierung kommt zusammen mit ihren Bindungen in die Gruppe *dp1*. Alles andere, auch die Atome, die beide Orientierungen teilen, bleibt unverändert.

Sind mehrere Gruppen unabhängig voneinander fehlgeordnet, z.B. in einem Packungsbild ohne enge Kontakte zwischen den Molekülen, in jeder ein Atom auswählen: nichts in der Struktur entscheidet zwischen ihren Orientierungen.

Um stattdessen die andere Orientierung zu behalten, die Struktur neu laden und eines ihrer Atome auswählen.

## Welche Atome zusammengehören
Kopien desselben Atoms, die sich zu nahe kommen, ohne gebunden zu sein (H...H unter 1.5 A, andere Atome unter 1.75 A), können nicht gleichzeitig vorhanden sein, während gebundene Atome zusammengehören; der Rest einer Gruppe folgt also den Atomen, die kollidieren. Ein Atom, das an beide Orientierungen gebunden ist, etwa das, an dem die Gruppe hängt, wird geteilt. Berühren sich benachbarte Gruppen auf diese Weise, z.B. über ihre Wasserstoffatome, entscheidet die Wahl der Orientierung für eine Gruppe auch die anderen, und ein ausgewähltes Atom genügt.

## Wenn es nicht funktioniert
| **Select one atom of each disordered group** | Nichts ist ausgewählt. |

| **Not part of the disorder** | Ein ausgewähltes Atom hat keine kollidierenden Kopien, oder eine Bindung ist ausgewählt. Nur Atome der fehlgeordneten Gruppen auswählen. |

| **Independent disordered groups** | Manche Gruppen berühren sich nicht, ein Atom kann sie also nicht alle entscheiden. In jeder ein Atom auswählen. |

| **Different orientations of the same group** | Zwei ausgewählte Atome verlangen beide Orientierungen derselben Gruppe. |

| **Contacts contradict each other** | Für diese Struktur gibt es bei diesen Abständen keine Aufteilung ohne Kollision. |

| **Selection check failed** | Höchstwahrscheinlich gibt es *dp1* schon: die Struktur neu laden und es erneut versuchen. |

| **Bonds lead on without end** | Die Struktur ist ein Netzwerk (ein Polymer) statt getrennter Fragmente und lässt sich daher nicht vervollständigen. Nichts wird geändert. |
