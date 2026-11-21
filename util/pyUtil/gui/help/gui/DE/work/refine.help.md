# refine-target
Die Struktur verfeinern, z.B. mit
- CTRL+R
- >>'refine'
- >>'refine 4 4'


# refine-settings-target
Die Verfeinerungseinstellungen öffnen


# draw-target
Ein Bild der Struktur mit den aktuellen Einstellungen erstellen


# draw-settings-target
Die Zeicheneinstellungen öffnen


# report-target
Einen Bericht erzeugen


# report-settings-target
Die Berichtseinstellungen öffnen


# Refinement Program
Neben dem eigenen Verfeinerungsprogramm (olex2.refine) unterstützt Olex2 alle Varianten von ShelXL. Je nach Programm stehen verschiedene Verfeinerungsmethoden zur Verfügung.

## olex2.refine
Das in Olex2 eingebaute Verfeinerungsprogramm. Es unterstützt alle ShelXL-Anweisungen und dazu eine Reihe neuer Restraints und Constraints, die ShelXL nicht kennt. Man kann zwischen diesem Programm und ShelXL wechseln; Olex2 'vergisst' die besonderen Anweisungen von olex2.refine dabei nicht, ShelXL beachtet sie aber natürlich nicht.

## Methoden für olex2.refine
Mit olex2.refine wird normalerweise das **Gauss-Newton-Verfahren (GN)** URL[https://en.wikipedia.org/wiki/Gauss-Newton\_algorithm,WIKIPEDIA] &nbsp;verwendet. Konvergiert die Verfeinerung schlecht, das stärker gedämpfte **Levenberg-Marquardt-Verfahren (LM)** URL[https://en.wikipedia.org/wiki/Levenberg-Marquardt\_algorithm,WIKIPEDIA] verwenden.

## ShelXL-20XX
Seit 2012 veröffentlicht George Sheldrick regelmäßig neue Versionen von ShelXL. Bitte auf der URL[https://shelx.uni-goettingen.de/,SHELX-Website] regelmäßig prüfen, ob die neuesten Versionen der SHELX-Programme installiert sind – nur *diese Versionen* sollten verwendet werden. Ältere Versionen funktionieren aber weiterhin, solange sie "im PATH" liegen und "shelxl" heißen. Wie man einen Ordner zum PATH hinzufügt, steht in Ilia Guzeis Handbuch im Olex2-Bereich Start. Wir empfehlen, im Wurzelverzeichnis eines Laufwerks einen Ordner 'CrystallographyPrograms' anzulegen und diesen zum PATH hinzuzufügen. Jedes bekannte Programm in diesem Ordner steht dann in Olex2 zur Verfügung.

## Methoden für ShelXL
LS steht für Kleinste-Quadrate-Verfeinerung mit voller Matrix (am besten für kleine Moleküle). CGLS ist die Kleinste-Quadrate-Verfeinerung mit konjugierten Gradienten (schneller als LS bei sehr vielen Parametern und daher am besten für frühe Phasen der Verfeinerung von Makromolekülen).

## Zyklen
Legt die größte Zahl der Verfeinerungszyklen für olex2.refine fest; konvergiert die Verfeinerung früher, endet sie automatisch. Bei anderen Programmen wie ShelXL ist dies die tatsächliche Zahl der Zyklen, unabhängig von der Konvergenz.

## Peaks
Legt fest, wie viele Restelektronendichte-Peaks (Q-Peaks) nach der Verfeinerung angezeigt werden.

## Über die Befehlszeile
| `refine 12 5` | Führt 12 Verfeinerungszyklen aus und zeigt danach fünf Restelektronendichte-Peaks. Diese Zahlen gelten für weitere Verfeinerungen, bis sie geändert werden. |


# Set Reflection File
Hier wird die Reflexdatei festgelegt; sie enthält in verdichteter Form alle Daten des Beugungsexperiments.

## hkl-Datei
Das Standardformat für die Datei mit den gemessenen Reflexen und ihren Intensitäten ist die .hkl-Datei. In diesem Auswahlmenü die Datei wählen, gegen die verfeinert werden soll. Umbenennen ist nicht nötig – einfach die Datei wählen und **Verfeinern** anklicken.

## Andere Dateiformate
Olex2 kann auch Formate wie .raw und andere verarbeiten.


# Weights, Extinction and ACTA
## Wichtung
| `weight` | Ein Wichtungsschema sollte angewendet werden, wenn das Modell nahezu fertig ist und alle Atome ihre Positionen gefunden haben. |

Alle Verfeinerungsprogramme schlagen ein passendes Wichtungsschema vor. Ein Klick auf die farbigen Zahlen in dieser Zeile übernimmt das vorgeschlagene Schema. Ist das Feld **Weight** angehakt, setzt Olex2 die Wichtung nach jedem Verfeinerungszyklus automatisch auf die vorgeschlagenen Werte. (In der Praxis heißt das: das Feld **Weight** anhaken, sobald das Modell steht, und weiter verfeinern, bis die Zahlen in den Feldern **Weight** grün werden.)

## Extinktionskorrektur
Extinktion ist ein physikalisches Phänomen, das die Intensität der Reflexe beeinflusst. Der Parameter **EXTI** soll die damit verbundenen Intensitätsänderungen erfassen; das Verfahren ist ein Kompromiss für primäre und sekundäre Extinktion. Im Allgemeinen sollte diese Korrektur erst in die Verfeinerung aufgenommen werden, wenn alle Nicht-Wasserstoffatome gefunden sind. Je nach Problem kann entweder **EXTI** oder **SWAT** (siehe unten) angehakt werden, aber nicht beide. (In der Praxis zuerst auf das **Prozentzeichen** neben R1 oben klicken, um das Diagramm Fobs gegen Fcalc zu zeigen; krümmt es sich bei großen Fcalc sichtbar nach unten, **EXTI** anhaken und bis zur Konvergenz weiter verfeinern.)

## SWAT
Ein Verfahren für diffuse Lösungsmittelbereiche (meist Wasser in Makromolekülen) mit zwei verfeinerbaren Parametern *g* und *U*. Je nach Problem kann entweder **EXTI** oder **SWAT** verwendet werden, aber nicht beide gleichzeitig.

## ACTA
Im Auswahlmenü schreibt **No ACTA** keine CIF-Datei, **ACTA NOHKL** eine CIF-Datei ohne eingebettete hkl-Datei und **ACTA** eine CIF-Datei mit eingebetteter hkl-Datei. Wir empfehlen, immer **ACTA** zu verwenden.


# Refinement Masks
Bei manchen Strukturen ist die Fehlordnung des Lösungsmittels so stark, dass ein Modell mit Atomlagen (also einzelnen, teilweise besetzten Atomen) weder möglich noch sinnvoll ist. Dann ist es besser, den fehlgeordneten Bereich gar nicht erst zu modellieren und die gemessene Elektronendichte einfach stehen zu lassen. Für diese Lösungsmittelmaske muss der Bereich berechnet werden, der von der Verfeinerung ausgenommen wird – und wie *dieser* festgelegt wird, hängt von der jeweiligen Struktur ab.
<br>
<br>

Das Video ansehen! URL[https://youtu.be/3jC2CVqSkgc,YOUTUBE]
<br>
<br>

Die Lösungsmittelmasken in Olex2 beruhen auf der **BYPASS**-Arbeit von P. van der Sluis und A. L. Spek. URL[https://doi.org/10.1107/S0108767389011189,PAPER]

## Lösungsmittelmaske verwenden
Ist dieses Feld angehakt, geht ein Lösungsmittelbeitrag zu den Strukturfaktoren in die Verfeinerung ein, als diskrete Fourier-Transformierte der Elektronendichte im Lösungsmittelbereich. Die Lösungsmittelmaske ist der Bereich, den fehlgeordnetes Lösungsmittel einnimmt. Sie lässt sich unter **Tools** > **Karten** > **Masken** berechnen und anzeigen (im Bereich **Maps** unter **View** **wire** wählen). Bei olex2.refine wird der Lösungsmittelbeitrag intern zu dem des geordneten Teils addiert; bei ShelXL wird er von den gemessenen Daten abgezogen, und das externe Verfeinerungsprogramm erhält eine veränderte hkl-Datei.

## Programm
**Olex2** berechnet die Maske aus einer Differenzkarte (smtbx.masks) und verfeinert den Lösungsmittelbeitrag mit dem Modell. **Platon** führt SQUEEZE aus und verfeinert gegen die veränderte Reflexdatei, die es schreibt. **Flat** verwendet das flache Bulk-Solvent-Modell: eine konstante Dichte im Lösungsmittelbereich, zusammen mit dem Modell skaliert; es hat ein eigenes Paar *solvent r* / *shrink r* mit den Standardwerten 1.1 und 0.9 &Aring; (die Werte für Makromoleküle), das bei Wahl von Flat anstelle von *trunc.* erscheint.

## Maske aktualisieren
Ist dies angehakt, wird die Lösungsmittelmaske vor Beginn der Verfeinerung neu berechnet. Das kann die Maske verbessern, besonders wenn der geordnete Teil der Struktur vor der ersten Maskensuche schlecht konvergiert war.

## Bes.
Besetzungswichtung. Ist dies angehakt, schließen teilweise besetzte Atome nur ihren Anteil am Lösungsmittelvolumen aus. Ohne diese Option hält eine Lage mit Viertelbesetzung das Lösungsmittel aus ihrem gesamten Volumen heraus, was den Lösungsmittelbeitrag unterschätzt. Strukturen ohne teilweise besetzte Atome sind nicht betroffen.

## Lösungsmittel-*r*
Nur Gitterpunkte in Hohlräumen, die *größer* als ein bestimmter Lösungsmittelradius (*r*) sind, werden berücksichtigt. Der Standardwert **1.2 &Aring;** verhindert, dass Hohlräume erscheinen, in die kein Atom passt.

## Trunc.
Der Abschneideradius. Mit ihm lässt sich eine enger anliegende Maske festlegen, als es mit dem Lösungsmittelradius *r* allein möglich wäre. Er liegt meist sehr nahe bei *r* oder ist gleich.


# Masking Info
Hier stehen die Angaben zum Inhalt des maskierten Bereichs. Für jeden Hohlraum zeigt die Tabelle das Volumen in &Aring;<sup>3</sup> und die Zahl der Elektronen darin. Wird eine Lösungsmittelmaske verwendet, sollte man nach Abschluss der Verfeinerung den geschätzten Inhalt der Hohlräume in diese Tabelle eintragen, damit er in die CIF-Datei kommt. Dazu in der Tabelle unter **Content/Asymmetric Unit** auf **Bearbeiten** klicken und Zahl und Namen der Lösungsmittelmoleküle im Hohlraum eintippen, z.B. '1/2 toluene' oder 'CH2Cl2'.
<br>
<br>

Sind die Inhalte eingetragen, berechnet Olex2 deren Elektronenzahl; stimmt sie gut mit der gefundenen überein, werden beide **e<sup>-</sup>**-Zahlen grün. Es erscheint ein Bereich mit den Summenformeln **Formula** und **Moiety** und einer weiteren Schaltfläche **Bearbeiten** für die Angaben, die in die CIF-Datei sollen. Im Bereich **Use & Edit** steht ein Mustertext zur Beschreibung der Lösungsmittelmaske dieser Struktur. Er sollte bei Bedarf angepasst und in den Abschnitt *edit_mask_special_details* der CIF-Datei übernommen werden.


[comment]: < Help text for "NoSpherA2" is now taken from NoSpherA2.md. >


# Refinement Settings Extra
Manche Verfeinerungsprogramme haben zusätzliche Einstellungen, die in der Olex2-GUI nicht vorkommen; sie lassen sich hier angeben.

# CGLS Options
Zwei Optionen für die Kleinste-Quadrate-Verfeinerung mit konjugierten Gradienten (CGLS-J).

**ESD**: Ist dies an, endet die Verfeinerung mit dem Aufbau der vollen Matrix, um Standardunsicherheiten zu erhalten, wie bei einer Kleinste-Quadrate-Verfeinerung. Aus überspringt diesen Schritt und ist schneller; so verhält sich CGLS in SHELXL. Sonst ändert sich an den Ergebnissen der Verfeinerung nichts. Für ein fertiges Modell anlassen, für Zwischenschritte ausschalten.

**single**: Hält die Designmatrix in einfacher Genauigkeit. Die Matrix ist dann nur halb so groß, und das Lösen mit konjugierten Gradienten, das durch die Speicherbandbreite begrenzt ist, wird schneller. Die Produkte werden weiterhin in doppelter Genauigkeit aufsummiert, die Auswirkung auf das Ergebnis ist also vernachlässigbar. Nützlich für große Strukturen.
