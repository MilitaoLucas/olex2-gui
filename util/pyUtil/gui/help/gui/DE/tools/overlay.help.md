# Match 1
Tools zum Überlagern von Fragmenten in derselben oder in zwei verschiedenen Strukturen. Mehr dazu in der Online-Dokumentation, verlinkt im Bereich **Start**.

## Alle Fragmente überlagern
Ein Klick auf **Alle Fragmente überlagern** überlagert automatisch alle gleichen Fragmente, die gerade angezeigt werden. Sie können in derselben Struktur liegen oder in verschiedenen Strukturen (z.B. verschiedenen CIF-Dateien), die mit dem Tool **Struktur überlagern** unten geöffnet wurden. Die berechnete RMS-Abweichung der überlagerten Fragmente (mit und ohne Inversion) erscheint im Grafikfenster. Der Befehl '<c>match</c>' kann auch in die Befehlszeile eingegeben werden.

## Überlagerung aufheben
**Überlagerung aufheben** (oder '<c>fuse</c>') kehrt zu den nicht überlagerten Fragmenten zurück.


# Match 3
Drei Atome (etwa A, B und C) im ersten Fragment und dann drei Atome (etwa X, Y und Z) im zweiten Fragment in der Reihenfolge auswählen, in der sie überlagert werden sollen (A auf X, B auf Y, C auf Z). **Ausgewählte Atome überlagern** überlagert die Fragmente in der Reihenfolge der Auswahl. Zurück zur nicht überlagerten Struktur mit **Überlagerung aufheben** oder '<c> fuse</c>'.


# Match 4
## Struktur überlagern
Mit diesem Link lässt sich eine zweite Struktur laden; die aktuelle und die neu geladene Struktur erscheinen nebeneinander auf dem Bildschirm im Modus **Match**. In diesem Modus überlagert ein Klick auf ein Atom der ursprünglichen und auf ein Atom der neuen Struktur die beiden Strukturen. Durch abwechselndes Anklicken von Atomen der ersten und zweiten Struktur lässt sich die Überlagerung verbessern (insgesamt drei Atompaare). Das erste Paar wird direkt übereinandergelegt, das zweite Paar dreht eine Struktur so, dass der Abstand seiner Atome minimal wird, und das dritte Paar dreht eine Struktur um die durch das erste und zweite Paar gebildete Gerade, sodass der Abstand der Atome des dritten Paars minimal wird. Die beiden überlagerten Strukturen erscheinen mit roten und grünen Bindungen, damit sie sich unterscheiden lassen. '<c>Esc</c>' beendet den Modus, '<c> fuse</c>' stellt wieder normale statt rote und grüne Bindungen her.

## Modus Überlagern
Startet den Modus **Match**, in dem Fragmente einer Struktur (oder zweier Strukturen) überlagert werden können. Genaueres unter **Struktur überlagern** oben.

## Überlagerung entfernen
Entfernt die zweite Struktur, die mit dem Link **Struktur überlagern** hinzugefügt wurde.
