# Map View
## Darstellungsarten
Die Optionen **plane**, **contour**, **surface**, **wire** und **points** im Auswahlmenü **View** sind verschiedene Darstellungsarten für Karten und Masken in Olex2.

### plane, contour, contour+plane
Diese drei Ansichten zeigen einen interaktiven 2D-Schnitt durch eine Karte, also eine Größe wie die berechnete Elektronendichte in der Bildschirmebene. Die Struktur lässt sich bei angezeigter Karte drehen, verschieben und zoomen; der 2D-Schnitt ändert sich entsprechend, wenn andere Teile der Struktur durch die Ebene laufen.

### Farben
In diesem Auswahlmenü die Zahl der Farben der Farbskala für die 2D-Karte in den Modi **plane** und **contour+plane** wählen.

### surface, wire, points
Diese drei Ansichten zeigen eine Größe wie die berechnete Elektronendichte in 3D über der Struktur. Ist die Elektronendichte zu gering, erscheint allerdings nur die 2D-Darstellung. Hat der Rechner Mühe mit diesen Karten, zuerst die Niveaus in der Ansicht **points** einstellen und dann **wire** oder **surface** wählen, die mehr Rechenleistung brauchen.
<br>
<br>

In den Modi **surface**, **wire** und **points** erscheint positive Elektronendichte grün und negative (Löcher) rot – ein sehr wirksames Mittel, um die Gültigkeit einer Struktur während der Verfeinerung zu prüfen. Steckt z.B. in der **diff**-Karte (Differenz zwischen Fobs und Fcalc) in der Ansicht **wire** ein Wasserstoffatom in einem roten Fleck mit einem grünen Fleck daneben, sollte dieses Wasserstoffatom wohl an die Stelle des grünen Flecks verschoben werden, sofern die neue Position chemisch sinnvoll ist. Ein nützliches Tastenkürzel für die **diff**-Karte ist '<c>CTRL+M</c>'.

### Erweitert
Ist dieses Feld angehakt, wird die Karte von einer Elementarzelle auf 27 benachbarte Zellen ausgedehnt (3 x 3 x 3). Sehr nützlich, um Form, Größe und Verteilung der Hohlräume in der Struktur zu sehen.

### Bearbeiten
Mit dieser Schaltfläche lassen sich die Farbeigenschaften der verschiedenen Kartenoberflächen bearbeiten.


# 2D Map Contours
Dieser Regler wählt entweder die größte Zahl der Konturlinien (in den Ansichten **contour** und **contour+plane**) oder die Zahl der Farben (in den Ansichten **plane** und **contour+plane**). In der Ansicht **contour** erscheinen Bereiche positiver Elektronendichte als durchgezogene Linien, Bereiche negativer Dichte (Löcher) als gestrichelte Linien. Eine Konturkarte wird in jede PostScript-Zeichnung aufgenommen, die bei angezeigter Karte erstellt wird.
<br>
<br>

~Tipp:~ Für um 0 symmetrische Karten z.B. 21 Konturen wählen: 10 über 0, 10 unter 0 und eine für das Niveau 0 selbst.


# 2D Map Scale
Legt Maximum und Minimum der Elektronendichte einer Karte fest. **Automatisch** (Standard) passt die Darstellung so an, dass Minimum und Maximum der Kartenlegende dem Minimum und Maximum der Elektronendichte im *aktuellen* Kartenschnitt entsprechen. **Statisch** hält Minimum und Maximum dagegen beim *globalen* Minimum bzw. Maximum fest, gleich welcher Schnitt gerade gezeigt wird.


# 2D Static Map Scale
## Min
Mit diesem Regler wird der kleinste dargestellte Wert der Karte festgelegt. Der Regler stellt das Minimum in Viertelschritten ein, nimmt aber auch Werte im Textfeld daneben an.

## Schritt
Dieser Regler legt den Abstand zwischen zwei benachbarten Konturen/Farben fest. Wie bei **Min** hat er vorgegebene Werte (Abstand 0.02), ein bestimmter Wert lässt sich aber auch in das Textfeld eingeben.


# 2D Map Position and Size
## Tiefe
Dieser Regler steuert, wie tief die Kartenebene "im" Bildschirm liegt. Negativere Werte schieben die Karte weiter in den Bildschirm, bis sie "hinter" dem Modell liegt; positivere Werte holen sie heraus, bis sie "vor" dem Modell liegt. Beim Ändern der **Tiefe** laufen verschiedene Teile der Struktur durch den 2D-Schnitt. Alternativ lässt sich die Karte senkrecht zum Bildschirm verschieben, indem man mit gedrückter '<c>UMSCHALTTASTE</c>' und linker Maustaste im Kartenbereich zieht. Dabei aufpassen, dass man auf der Karte selbst zieht und nicht auf der Struktur.
<br>
<br>

Drei oder mehr Atome auswählen und die Schaltfläche **Tiefe** anklicken, um die Karte an der besten Ebene durch die ausgewählten Atome auszurichten. Die Ebene wird ebenfalls angezeigt; zum Entfernen mit links anklicken und '<c>Entf<c>' drücken.

## Größe
Der Regler **Größe** steuert die Größe der gezeichneten Karte. Größere Werte *verkleinern* die Karte auf dem Bildschirm, *erhöhen* aber ihre Auflösung. Den sichtbaren Kartenbereich kann man auch mit gedrückter '<c>CTRL</c>'-Taste und rechter Maustaste im Kartenbereich verändern.


# Map 3D
Der Regler **Niveau** stellt ein, wie viele Details die Karte zeigt. Ein Wert lässt sich auch in das Feld daneben eingeben. Bei hohem Niveau erscheinen nur die markantesten Merkmale (die größten Elektronendichte-Peaks und -Löcher), bei niedrigem viel mehr. Unterhalb einer bestimmten Grenze gehen die Merkmale aber im Rauschen der Daten unter: die Karte wird überladen, nichtssagend und langsam. Deshalb wird das Niveau an dieser Grenze festgehalten.


# Electron Density
Dieser Bereich zeigt verschiedene Elektronendichtekarten. Welche Größe dargestellt wird, wählt man im Auswahlmenü **Karte**.

## Karte
Im Auswahlmenü die Art der Karte wählen.

### diff
Zeigt die Differenzkarte Fobs-Fcalc. Damit sie richtig erscheint, im Auswahlmenü **View** des Bereichs **Maps** (über **Karteneinstellungen** in diesem Bereich) **surface**, **wire** oder **points** wählen. Der entsprechende Befehl ist '<c>CalcFourier -diff -r=0.1 -m</c>' oder einfach '<c>CTRL+M</c>'. Ein äußerst wichtiges Tool, um die Gültigkeit eines Modells zu prüfen. Rote Bereiche der Karte stehen für fehlende, grüne für überschüssige Elektronendichte.

### fcalc
Zeigt eine Karte der berechneten Elektronendichte (Fcalc).

### 2Fo-Fc
Zeigt die Karte 2Fobs-Fcalc.

### fobs
Zeigt eine Karte der gemessenen Elektronendichte (Fobs).

### fcfmc
Zeigt die FCF-Karte Fc-Fc.

## Quelle
In diesem Auswahlmenü die Datenquelle für die Karte wählen.

## Aufl./&Aring;
Die gewünschte Auflösung der Karte (in &Aring;) eingeben.

## Maske
Ist das Feld **Maske** angehakt, werden alle Elektronendichte-Merkmale (Peaks oder Löcher) in der Nähe der angezeigten Struktur gezeigt. Ist es nicht angehakt, nur die Merkmale innerhalb der Elementarzelle.

## Karte anzeigen/ausblenden
Schaltet die Anzeige der Karte ein oder aus.


# Calculate Voids
Berechnet Hohlräume und Kanäle der Struktur, falls vorhanden. Die Berechnung verwendet die internen Olex2-Bibliotheken. Mehr dazu mit '<c>help calcvoid</c>' oder über die Schaltfläche unten.

| `help calcvoid` | Hilfe zum Befehl '<c>calcvoid</c>'. |

## Auflösung/&Aring;
Die Auflösung der Hohlraumkarte in &Aring;.

## Abstand/&Aring;
Ein zusätzlicher Abstand (in &Aring;) von der van-der-Waals-Oberfläche, ab dem der Hohlraum berechnet wird.

## Genau
Ist dieses Feld angehakt, werden die Hohlräume genauer berechnet.

## Hohlraum anzeigen/ausblenden
Schaltet die Anzeige der Hohlräume ein oder aus. Eine Liste der Hohlräume (falls vorhanden) erscheint außerdem im Grafikfenster. Ist oben in diesem Bereich **Erweitert** angehakt, erscheinen die Hohlräume in 3 x 3 x 3 benachbarten Elementarzellen, was ihre Form besser erkennen lässt.


# Calculate Solvent Accessible Voids
Prüft, ob die Struktur Hohlräume enthält, die groß genug für ein Lösungsmittel sind. Die Berechnung beruht auf den smtbx/cctbx-Bibliotheken von Olex2 und ist ein alternatives Verfahren zu '<c>calcvoid</c>' oben. Es entsteht keine Karte, aber eine Liste der Hohlräume im Grafikfenster.

## Sonde/&Aring;
Die Größe (in &Aring;) einer kugelförmigen "Sonde", die über die Struktur rollt, in Lücken passt und so Hohlräume abtastet. Eine kleinere Kugel passt in kleinere Lücken und ergibt daher ein größeres Hohlraumvolumen.

## Gitter/&Aring;
Bestimmt die Auflösung der Hohlraumkarte. Ein zu feines Gitter macht die Berechnung sehr langsam, ohne die Karte wesentlich zu verbessern.

## Info anzeigen
Gibt eine Liste der lösungsmittelzugänglichen Hohlräume (falls vorhanden) im Grafikfenster aus.


# Masks
Der Bereich **Masken** ist eine Alternative zur bekannten Routine ~SQUEEZE~ in ~Platon~ für fehlgeordnetes Lösungsmittel. Mehr dazu findet man online unter "modelling solvent disorder". Dieses Vorgehen sollte nur der letzte Ausweg sein, wenn sich das Lösungsmittel wegen starker Fehlordnung nicht identifizieren oder modellieren lässt. Zuerst sollte alles versucht werden, das Lösungsmittel mit den **Fehlordnungs-Tools** im Bereich **Work** und mit **FragmentDB** im Bereich **Tools** zu identifizieren und zu modellieren. Wurde sowohl mit ShelXL als auch mit olex2.refine verfeinert und erscheint die Wahl zwischen einer olex- und einer fcf-Datei, die Datei aus dem letzten Verfeinerungszyklus verwenden.
<br>
<br>

Mehr zum verwendeten Algorithmus: B. Rees et al., Acta Cryst. D61, 2005, 1299-1301.

## Reflexdatei
Eine .hkl-Datei für die Berechnung der Maske wählen.

## Satzvervollständigung verwenden
Fehlen Reflexe bei kleinen Winkeln (manchmal genügt schon einer), kann die Elektronenzahl in einem Hohlraum unterschätzt werden. Mit dieser Option werden fehlende Reflexe ergänzt und während der Fourier-Iterationen frei angepasst, was die tatsächliche Elektronenzahl genauer schätzt.

## Hohlraum anzeigen/ausblenden
Schaltet die Anzeige der Hohlräume ein oder aus. Eine Liste der Hohlräume (falls vorhanden) erscheint außerdem im Grafikfenster. Ist oben in diesem Bereich **Erweitert** angehakt, erscheinen die Hohlräume in 3 x 3 x 3 benachbarten Elementarzellen, was ihre Form besser erkennen lässt.

## Karte
Im Auswahlmenü **Karte** zeigt **mask** die lösungsmittelzugänglichen Hohlräume der Struktur. **f\_mask** zeigt die Fourier-Transformierte des Lösungsmittelbeitrags zu den Strukturfaktoren. **f\_model** zeigt die Fourier-Transformierte der Summe der Beiträge von Lösungsmittelbereich und geordnetem Teil der Struktur.

## Gitter/&Aring;
Der Parameter **Gitter** ist die Auflösung der Karte in &Aring;. Die ganze Struktur, Atome wie Hohlräume, wird zur Berechnung der Maske in Gitterpunkte dieser Auflösung geteilt.

## Lösungsmittel-R in &Aring;
Alle Gitterpunkte, die weiter als die Summe aus dem van-der-Waals-Radius eines Atoms und **Lösungsmittel-R** entfernt sind, gelten zunächst als Teil des Lösungsmittelbereichs. Der Standardwert 1.2 &Aring; ist groß genug, damit keine Hohlräume erscheinen, in die kein Atom passt.

## Schrumpf-Abschneideradius R in &Aring;
Nachdem mit **Lösungsmittel-R** der Lösungsmittelbereich bestimmt ist, wird für alle Gitterpunkte außerhalb geprüft, ob sie näher als **Schrumpf-Abschneideradius R** am Bereich liegen. Wenn ja, kommen sie zum Lösungsmittelbereich hinzu. Dieser Radius ist meist sehr nahe bei **Lösungsmittel-R** oder gleich. Im Ergebnis liegt die Maske enger am Lösungsmittelbereich an.


[comment]: < The text below is legacy help documentation that doesn't seem to be used anywhere. >


# masks-help

### Volumen wählen
Es erscheint eine Box mit verschiebbaren Seiten. Mit links auf die farbigen Flächen klicken und die Seiten bei gedrückter **UMSCHALTTASTE** verschieben. Die Karte wird nur innerhalb dieser Box berechnet. Die Box lässt sich mit der rechten Maustaste und 'Hide' löschen.
