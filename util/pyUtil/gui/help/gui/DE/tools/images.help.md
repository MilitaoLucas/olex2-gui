# Images
Olex2 kann Bilder einer Struktur in vielen Formaten exportieren; dieser Bereich bietet dafür zahlreiche Optionen. Auch das Beschriften der Atome geschieht hier.

## Dateiname und Format
Hier einen Namen für die Bilddatei eingeben oder den vorgegebenen verwenden. Hier wird auch festgelegt, was bei schon vorhandenen Dateinamen geschieht. Das **Standard**-Format für gespeicherte Bilder ist **Bitmap**, andere Formate lassen sich im Auswahlmenü wählen.

## Atombeschriftungen
Damit werden einzelne Atome der Struktur mit anpassbaren Beschriftungen versehen. Diese sind etwas anderes als die normalen Atomnamen aus der Verfeinerung oder aus dem Bereich **Benennung**. Die Schaltfläche **selected** beschriftet nur die im Grafikfenster hervorgehobenen Atome, **non-H** alle Nicht-Wasserstoffatome und **hetero** alle Atome außer Kohlenstoff und Wasserstoff. Um *alle* Atome zu beschriften, mit '<c>sel atoms</c>' alle Atome auswählen und **selected** anklicken.

## Symmetriebezeichnung und Stil
Das Auswahlmenü **Symmetriebezeichnung** bietet mehrere Möglichkeiten, an die Beschriftungen symmetrieverwandter Atome ein beschreibendes Suffix anzuhängen. Im Menü **Stil** lässt sich wählen, wie der Teil der Beschriftung nach dem Elementsymbol formatiert wird.

## Beschriftungen verschieben und löschen
'<c>Umschalt</c>' gedrückt halten und eine Beschriftung mit der linken Maustaste ziehen, um sie zu verschieben. Zum Löschen zuerst sicherstellen, dass keine Atome, Bindungen usw. hervorgehoben sind (''<c>Esc<c>' hebt die Auswahl auf). Die zu löschenden Beschriftungen mit links anklicken und '<c>Entf</c>' drücken. Alle Beschriftungen wählt man aus, indem man eine anklickt und '<c>CTRL+A</c>' drückt. Alle Atombeschriftungen löscht der Link **alle Beschriftungen LÖSCHEN**.

## Beschriftungsfarbe und -box
Um Farbe und Aussehen der Atombeschriftungen zu ändern, öffnet der Link **Choose the label colour** ein Menü für die Farbeigenschaften. Der Link **Label Box** passt die Box um jede Beschriftung an.


[comment]: < The help text given below for "Align and Lock" is the same as in quick_drawing_styles.md. >


## Ausrichten und Sperren
### Ansicht und Ebene
Diese Links richten die Struktur im Anzeigefenster aus und zentrieren sie, was vor dem Erstellen von Bildern nützlich sein kann. **View** zentriert und orientiert die Struktur anhand ihrer Hauptträgheitsachsen. **Plane** berechnet eine beste Ebene durch die ganze Struktur, stellt die Struktur senkrecht zu dieser Ebene und zentriert sie. Keine der beiden Methoden ändert die Vergrößerung. '<c>mpln -r<c>' zeigt die beste Ebene und gibt ihre Gleichung im Ausgabefenster aus. Zum Löschen der Ebene diese anklicken und '<c>Entf</c>' drücken.
<br>
<br>

Weitere nützliche Befehle zum Ausrichten der Struktur auf dem Bildschirm:

| `center` | Zentriert die Struktur, ohne Orientierung oder Vergrößerung zu ändern. |

| `compaq -a` | Zentriert die Struktur ebenfalls ohne Änderung der Orientierung, passt aber ihre Größe an den Anzeigebereich an. |

Hinweis: Die Atomlegende lässt sich an jede beliebige Stelle auf dem Bildschirm verschieben, z.B. näher an die Struktur: '<c>Umschalt</c>' gedrückt halten und mit der Maus ziehen. Mit dem Befehl '<c>legend</c>' lässt sich die Legende aus- und einschalten. Zum Zurücksetzen (z.B. wenn sie verschwunden ist) '<c>legend -r</c>' eingeben.

### Sperren
Bei der Arbeit an Bildern ist es manchmal hilfreich, bestimmte Mausfunktionen zu sperren, damit Orientierung oder Vergrößerung nicht versehentlich verändert werden. Zoom, Drehung und Verschiebung lassen sich einzeln über die entsprechenden Felder sperren. Ist z.B. nur **Translation** angehakt, bleibt die Struktur an ihrer Stelle auf dem Bildschirm, lässt sich aber weiter drehen und zoomen. Alle drei Funktionen sperrt das Feld **Alle sperren**.


# Bitmap Images
Olex2 erzeugt Bitmap-Bilder von Strukturen in vielen Formaten, ohne Grenze für die Dateigröße. Alle Bilder sind im RGB-Farbraum. Werden CMYK-Bilder gebraucht, z.B. für eine Publikation, ist ein eigenes Umwandlungsprogramm von RGB nach CMYK nötig. Im Internet gibt es viele solche Dienste, bei denen man eine RGB-Datei hochlädt und eine CMYK-Datei zurückerhält.


# Bitmap Image Attributes
## Dateiformat
In diesem Auswahlmenü das Format der Bilddatei wählen, etwa .png oder .jpg. Standard ist .png (empfohlen): verlustfrei komprimiert, mit recht kleinen Dateien.

## Transparenz
Der Hintergrund der Struktur lässt sich transparent machen, dann werden aber auch rein weiße Teile der Struktur transparent. Abhilfe: den Hintergrund des Bildes auf eine Farbe setzen, die in der Struktur nicht vorkommt (Rosa eignet sich meist gut), und dann alle Pixel dieser Farbe in PowerPoint oder einem anderen Grafikprogramm transparent machen. Professionelle Bildbearbeitungsprogramme bieten viele Wege zu einem transparenten Hintergrund.

## Bild erstellen
Die Schaltfläche **Los!** speichert ein Bild der Struktur im aktuellen Arbeitsordner. Das Bild enthält außer Atombeschriftungen und Legende keinen angezeigten Text, wohl aber den aktuellen Hintergrund. Für einen weißen Hintergrund ein- oder zweimal '<c>F2</c>' drücken.


# Bitmap Image Attributes1
## Auflösung
Die Bildauflösung in DPI im Auswahlmenü wählen oder einen eigenen Wert eingeben.

## Breite
Die Bildbreite in Zoll oder Zentimetern im Auswahlmenü wählen oder eine eigene Breite eingeben. Die Breite in Pixeln passt sich je nach gewählter Auflösung automatisch an.

## Größe
Im Auswahlmenü **Größe (px)** die Bildbreite in Pixeln wählen. Die Breite passt sich je nach gewählter Auflösung automatisch an. Man kann auch einen eigenen Wert in das Feld **Größe (px)** eingeben. Ein Wert ab 100 gilt als Bildbreite in Pixeln, ein Wert unter 100 als Prozentsatz der Anzeigegröße. 1000 im Feld **Größe (px)** ergibt also ein 1000 Pixel breites Bild, 85 ein Bild mit dem 0.85-fachen der Anzeigegröße. Die Größe der Bitmap-Datei ist nicht begrenzt.

| `pict molecule.png 300` | Erzeugt im Arbeitsordner eine 300 Pixel breite PNG-Datei **molecule.png**. |


# Bitmap Image Trim
## Zuschneiden
Ist dieses Feld angehakt, erhält das Bild den angegebenen Abstand und Rand. In alle unten beschriebenen Auswahlmenüs lassen sich eigene Werte eingeben.

### Abstand
Fügt um das Bild einen weißen Rand der angegebenen Breite in Prozent hinzu.

### Rand
Fügt dem Bild einen Rahmen der im Menü **Rand (%)** angegebenen Dicke in der Farbe hinzu, die der Hexadezimalcode im Menü **Farbe** angibt. Die Farbe zu diesem Code erscheint im Quadrat neben dem Menü **Farbe**.


[comment]: < Help text for "Add Fog" is now taken from quick_drawing_styles.md. >


# Bitmap Atom Label Fonts
Hinweis: Dieser Abschnitt betrifft die selbst angelegten Atombeschriftungen aus dem Bereich **Bilder** oben, *nicht* die Atomnamen aus der Verfeinerung oder aus dem Bereich **Benennung**.
<br>
<br>

Hier werden die Schriften für Atom- und Bindungsbeschriftungen festgelegt. Der Link **Beschriftungsschrift (Olex2)** ändert die Einstellungen der Olex2-Standardschrift für Atombeschriftungen. Um statt der eingebauten Olex2-Schrift eine Systemschrift wie Courier oder Arial zu verwenden, den Link **(Systemschrift)** daneben anklicken und die gewünschte Schrift im Menü wählen. Entsprechend ändert **Bond Label Font (Olex2)** die Olex2-Standardschrift für Bindungsbeschriftungen, und der Link **(Systemschrift)** daneben wählt eine Systemschrift dafür.


# Postscript Images
Manche meinen, es gebe keine bessere Darstellung einer Kristallstruktur auf Papier als eine klare schwarz-weiße ORTEP-Zeichnung. Solche Zeichnungen kann Olex2 erzeugen. Für ORTEP-Zeichnungen gibt es sehr viele Optionen. Viele lassen sich in dieser GUI einstellen; für ausgefallenere Optionen bitte im Olex2-Handbuch nachsehen (Tool **Start** im Bereich **Start**).


# PS Row 1
Mit **Farbige Atome** und **Farbige Bindungen** erscheinen Atomumrisse bzw. Bindungen farbig. Ist **Gefüllte Atome** angehakt, werden alle farbigen Atome mit ihrer Farbe gefüllt. **Pers** ergibt eine perspektivische Ansicht der Struktur.
<br>
<br>

Sind alle PostScript-Optionen eingestellt, erzeugt die Schaltfläche **Los!** eine .ps-Bilddatei im Arbeitsordner.


# PS Row 2
In diesen Auswahlmenüs werden die Linienbreiten für Atomumrisse und Oktanten festgelegt.


# PS Row 3
Hier wird festgelegt, in wie viele Abschnitte jede Oktantenfläche geteilt wird und wie breit die Trennlinien der Oktanten sind.


# PS Row 4
Hier wird die Breite der Bindungen zu Wasserstoffatomen als Anteil der normalen Bindungsbreite festgelegt. Die Breite aller anderen Bindungen steuert der Regler **Bond r** im Bereich **Schnelle Zeichenstile** unter **View** oder der Befehl '<c>brad</c>'.


# PS Row 5
In diesen Auswahlmenüs werden Strichstärke und Größe der Schrift für Atom- und Bindungsbeschriftungen festgelegt. Eine größere Strichstärke lässt die Schrift fetter erscheinen.


# PS Row 6
In diesem Auswahlmenü wird die Größe der Bindungsschrift eingestellt.


# PS Row 7
Standardmäßig erhalten reitend gesetzte und als gleichmäßige Kugeln dargestellte Wasserstoffatome keine ausgeschnittenen Oktanten. Auch Kohlenstoffatome erhalten keine, weil diese Zeile standardmäßig die Anweisung **-$C** enthält. Alle anderen Atome werden standardmäßig mit ausgeschnittenen Oktanten dargestellt. Mit **+$C** in diesem Menü erhalten auch Kohlenstoffatome ausgeschnittene Oktanten.


# Povray Images
Eine Struktur lässt sich im verbreiteten POVRAY-Format als 3D-Objekt exportieren. POVRAY erzeugt anspruchsvolle Bilder mit berechneten Schatten und Hintergründen sowie 3D-Animationen, setzt aber gute Kenntnisse in POVRAY voraus. Optionen gibt es hier keine: Olex2 erzeugt nur eine .pov-Datei zur Weiterverarbeitung mit POVRAY.

| `pictPR dateiname.pov` | Speichert die POVRAY-Ausgabedatei 'dateiname.pov'. |


# PR row 1
Die Schaltfläche **Los!** erzeugt ein POVRAY-Bild im aktuellen Arbeitsordner.


# Image Series
Erzeugt eine Reihe von Bitmap-Bildern der Struktur, die sich um die *x*-, *y*- oder *z*-Achse dreht.


# IS row 1
Die Schaltfläche **GO** erzeugt eine Reihe von Einzelbildern der sich drehenden Struktur. Die Bilder, nummeriert 000, 001, 002 usw., werden im Ordner **movie** im aktuellen Arbeitsordner gespeichert. Hintereinandergesetzt ergeben sie eine Animation der sich drehenden Struktur.


# IS row 2
Das Feld **Drehung um Achse** gibt die Drehachse an (**1** = *x*, **2** = *y*, **3** = *z*). **Grad** gibt an, um wie viel Grad die Struktur vor jedem weiteren Bild der Reihe gedreht wird.


# IS row 3
**Anzahl der Bilder** gibt an, wie viele Einzelbilder aufgenommen werden, und **Größe** bestimmt die Größe jedes Bildes der Reihe.
