# Twinning-help
# Twinning
Diese Tools prüfen, ob eine Struktur verzwillingt ist, und berechnen gegebenenfalls das Zwillingsgesetz. Die ersten beiden Schaltflächen dieser Zeile suchen Zwillingsgesetze, die dritte prüft, ob eine Struktur verzwillingt ist.

## 2-zählige Achse suchen
**2-zählige Achse suchen** startet eine schnelle Suche nach zweizähligen Zwillingsgesetzen für die Struktur. Wird ein brauchbares Gesetz gefunden, erscheint die zugehörige Transformationsmatrix im Ausgabefenster. Angenommen, es wird ein zweizähliges Zwillingsgesetz mit folgender Transformationsmatrix gefunden:
<br>
<br>

-1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0
<br>
0 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; -1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0
<br>
2/3 &nbsp;&nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1
<br>
<br>

Die Suche schlägt auch einen *BASF*-Wert vor (Batch-Skalenfaktor, also den Anteil einer der Zwillingskomponenten). Ist der vorgeschlagene *BASF* 0.204, berücksichtigen die folgenden beiden Anweisungen in der .ins-Datei die gefundene Verzwillingung in der weiteren Verfeinerung:
<br>
<br>

TWIN -1 0 0&nbsp;&nbsp;&nbsp;0 -1 0&nbsp;&nbsp;&nbsp;0.667 0 1&nbsp;&nbsp;&nbsp;2
<br>
BASF 0.204
<br>
<br>

(Die 2 am Ende der *TWIN*-Anweisung steht für einen Zwilling aus zwei Komponenten.)

## Alle Verzwillingungen suchen
Sucht *alle* für die Struktur möglichen Zwillingsgesetze, nicht nur die häufigen zweizähligen. Werden welche gefunden, erscheinen Transformationsmatrix und *BASF* unten in diesem Bereich.

## Kumulatives Diagramm
**Kumulatives Diagramm** öffnet die kumulative Intensitätsverteilung der gemessenen Reflexe. Liegen die Datenpunkte überwiegend auf der unteren (roten) Linie, ist die Struktur sehr wahrscheinlich verzwillingt.


# General
Diese Zeile enthält allgemeine Einstellungen, die für alle Suchverfahren nach Zwillingsgesetzen gelten.

## Erweitert
Ist dieses Feld angehakt, laufen alle Suchen im "erweiterten" Modus, also gründlicher (und damit langsamer). Findet eine normale Suche kein Zwillingsgesetz, kann die Wiederholung mit angehaktem Feld ein übersehenes Gesetz finden.

## Min. Gesetze
Die Mindestzahl brauchbarer Zwillingsgesetze, die zurückgegeben werden. Eine kleine Zahl beschleunigt die Suche, weil sie endet, sobald so viele Gesetze gefunden sind. Diese können aber schlechter sein als andere, die bei zu kleinem **Min. Gesetze** übersehen wurden. Erklären die zuerst gefundenen Gesetze die Verzwillingung nicht richtig, die Zahl erhöhen und erneut suchen.

## Schwellenwert für alle Suchen
Der Abstand, unterhalb dessen zwei Punkte im reziproken Raum (also Reflexe) als überlappend gelten. Ein größerer Wert liefert mehr mögliche Zwillingsgesetze, die die Verzwillingung aber womöglich nicht genau beschreiben; ein kleinerer Wert liefert weniger, dafür genauere Gesetze.

# Spherical Angle Axis
Dieser Bereich bietet zwei weitere Wege, Zwillingsgesetze zu suchen: **Spherical** und **Angle-Axis**.
<br>
<br>

Das Verfahren **Spherical** nutzt direkt starke Reflexe und die Punkte auf einer Kugel, auf die sie abgebildet werden könnten, um brauchbare Zwillingsgesetze zu berechnen. Es ist meist schneller, durchsucht weniger Raum, findet dabei mehr Gesetze und ist nicht auf bestimmte Drehwinkel beschränkt. **Spherical** hängt stark von der Mindestzahl der Gesetze ab; liefert es schlechte Ergebnisse, **Min. Gesetze** erhöhen und erneut suchen.
<br>
<br>

Das Verfahren **Angle-Axis** sucht dagegen Schritt für Schritt nach Drehzwillingsgesetzen, indem es mögliche Zwillingsachsen und Drehungen um sie prüft. Die Achsen stammen von ganzzahligen Punkten im direkten und im reziproken Raum.
<br>
<br>

Für das erste Verfahren die Zahl der zu prüfenden schlechten Reflexe wählen und **Spherical** anklicken. Für das zweite **Max Index** und **Rot. Fract'n** angeben und **Angle-Axis** anklicken.

## Schlechte Refl.
Die Zahl der schlechten Reflexe für das Verfahren **Spherical**. Sie stammen aus der Liste im Bereich **Schlechte Reflexe** unter **Info**.

## Spherical
Startet eine Suche nach Zwillingsgesetzen mit dem Verfahren **Spherical**.

## Max Index
Der größte Wert von *h*, *k* oder *l* für die Suche mit dem Verfahren **Angle-Axis**. Ein größerer **Max Index** findet mehr Zwillingsgesetze, die Suche dauert aber länger.

## Rot.-Anteil
Der Drehanteil *n* bestimmt den Winkel 360&deg;/<i>n</i>, die Schrittweite der Drehung um jede Achse bei der Suche **Angle-Axis**. Ein größerer Wert ergibt feinere Schritte und damit mehr Zwillingsgesetze.

## Angle-Axis
Startet eine Suche nach Zwillingsgesetzen mit dem Verfahren **Angle-Axis**.


[comment]: < Help text for "hkl file" is now taken from refine.md. >


# Set HKLF5 Reflection File
Das Dateiformat HKLF5 wird nur für verzwillingte Strukturen verwendet, ist aber auch bei Verzwillingung nicht immer nötig. Es ähnelt dem normalen HKLF4-Format, enthält aber eine zusätzliche Spalte, die angibt, zu welcher Zwillingskomponente jeder Reflex gehört. Eine solche Datei *ist* bei nicht-meroedrischer Verzwillingung nötig, wenn sich die reziproken Gitter der Zwillingskomponenten nicht genau zur Deckung bringen lassen.
