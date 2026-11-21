#  Reflection File
In Olex2 lässt sich festlegen, gegen welche Reflexdatei das Modell verfeinert wird.

## hkl-Datei
Im Auswahlmenü die .hkl-Datei für die Verfeinerung wählen.

## Themenfarben verwenden
Ist dieses Feld angehakt, werden die Diagramme in den Farben und Schriften des aktuellen Themas gezeichnet. Nicht angehakt ergibt sich unabhängig vom Thema das ursprüngliche Olex2-Aussehen (weißer Hintergrund, dunkle Schrift, Olex2-eigene Schriften): am besten für Berichte und Publikationen.

## Diagramm speichern
Ist dieses Feld angehakt, werden die im Menü unten erzeugten Diagramme der Reflexstatistik gespeichert, als .png-Dateien im aktuellen Arbeitsordner der Struktur.


# Reflection Graph
Die Diagramme in diesem Menü helfen, Probleme bei der Strukturbestimmung zu erkennen. Manche hängen nur von den Beugungsdaten ab, andere vom Strukturmodell; der Name **Reflexstatistik** ist also nicht ganz genau.
<br>
<br>

Im Auswahlmenü die gewünschte Diagrammart wählen und auf **go** klicken. Mehr **Bins** teilen die Reflexe in mehr Datengruppen und ergeben ein feineres Diagramm; ist **Output csv** angehakt, werden die Daten des aktuellen Diagramms als .csv-Textdatei in den Arbeitsordner geschrieben. Zeigt ein Diagramm die Auflösung auf der *x*-Achse, kann diese als 2&theta;, *d*-Wert, Quadrat des reziproken Gitterabstands *d*\*, sin(&theta;)/&lambda; oder (sin(&theta;)/&lambda;)<sup>2</sup> angegeben werden, auswählbar im Menü. Ist oben **Diagramm speichern** angehakt, wird das Diagramm als .png-Datei im Arbeitsordner gespeichert.

## Wilson-Plot
Dieser Plot vergleicht die gemessenen Intensitäten statistisch mit der theoretischen Verteilung für eine zufällige Atomanordnung, unter Berücksichtigung der mit 2&theta; abnehmenden Atomstreuung. Er ist meist linear. Aus ihm ergeben sich der Gesamt-Auslenkungsparameter *B* der Struktur und der Skalenfaktor *K* der Daten. Der Wert <|*E*<sup>2</sup> - 1|> unter dem Plot hilft, zentrosymmetrische (zentrische) von nicht zentrosymmetrischen (azentrischen) Strukturen zu unterscheiden. Ist <|*E*<sup>2</sup> - 1|> &asymp; 0.968, ist die Struktur wahrscheinlich zentrosymmetrisch, liegt er näher bei 0.736, wahrscheinlich nicht zentrosymmetrisch. Wahlweise mit der Olex2-eigenen Methode oder mit der Methode aus URL[https://cci.lbl.gov/docs/cctbx/,cctbx].

## Kumulative Intensität
Dieses Diagramm hilft zu entscheiden, ob die Struktur zentrosymmetrisch ist. Liegen die Daten meist auf der oberen schwarzen Linie, ist sie wahrscheinlich zentrosymmetrisch; auf der mittleren blauen Linie wahrscheinlich nicht zentrosymmetrisch. Liegen die Daten auf der unteren roten Linie, ist die Struktur wahrscheinlich nicht zentrosymmetrisch und verzwillingt.

## Systematische Auslöschungen
Zeigt die Intensitätsverteilung der Reflexe, die systematisch ausgelöscht sein sollten. Ihre Intensitäten sollten sehr klein und im Vergleich zur Standardunsicherheit jedes Reflexes unbedeutend sein.

## Fobs-Fcalc
Diese Auftragung von Fobs gegen Fcalc ist normalerweise eine Gerade mit Fobs etwa gleich Fcalc über den ganzen Bereich, d.h. mit einer Steigung von etwa 1 und einem Achsenabschnitt von etwa 0. Ausgelassene Reflexe erscheinen grau. Steht die Maus über einem gelben Reflex, erscheint "OMIT h k l". Ein Klick auf den Reflex fügt für ihn eine **OMIT**-Anweisung in die Instruktionsdatei ein, und er wird grau. So lässt sich ein Ausreißer aus der Verfeinerung nehmen, z.B. wenn der Reflex vom Beamstop verdeckt war. Ein Klick auf einen grauen Reflex entfernt seine **OMIT**-Anweisung und nimmt ihn wieder in die Verfeinerung auf.
<br>
<br>

Krümmt sich der Plot bei großen Fcalc deutlich nach unten, kann eine Extinktionskorrektur nötig sein: im Bereich **Verfeinern** das Feld **EXTI** anhaken und das Modell erneut verfeinern.

## I/sigma gegen Auflösung
Mit diesem Diagramm lässt sich die Qualität der Beugungsdaten beurteilen. I/&sigma; erscheint als größere grüne und rote Quadrate (grün bei I/&sigma; &ge; 3&sigma;, sonst rot), die kumulative Zahl der unabhängigen Reflexe als kleinere graue Quadrate. Wünschenswert ist natürlich ein hohes I/&sigma; bis zu hohen 2&theta;. In der Praxis sollte I/&sigma; > 3 mindestens bis zu dem von der IUCr empfohlenen 2&theta;-Wert sein, damit die Struktur mit einer akzeptierten Mindestauflösung bestimmt werden kann.

## cc half gegen Auflösung
Zeigt den Pearson-Korrelationskoeffizienten zwischen zufälligen Datenhälften, CC<sub>1/2</sub>, als Funktion der Auflösung. Im Wesentlichen prüft diese Methode, wie gut die eine Datenhälfte die andere vorhersagt, und ist damit ein Maß für die "Auflösung" des gesamten Datensatzes. CC<sub>1/2</sub> liegt bei niedriger Auflösung (kleinen 2&theta;) meist nahe 1 und nimmt bei hoher Auflösung (großen 2&theta;) etwas ab.

## Rmerge gegen Auflösung
Rmerge misst, wie gut mehrfache Messungen desselben Reflexes übereinstimmen. Rmerge erscheint als größere grüne und rote Quadrate (grün bei Rmerge &le; 0.15, sonst rot), die kumulative Zahl der unabhängigen Reflexe als kleinere graue Quadrate. Daten mit einem Rmerge über 0.15 gelten als fragwürdig. Optimal sind Daten mit Rmerge < 0.15 mindestens bis zur von der IUCr empfohlenen Auflösungsgrenze.

## Fobs über Fcalc
Am Ende der Verfeinerung sollte Fcalc möglichst nahe bei Fobs liegen, ihr Verhältnis also nahe 1. Dieses hier als Funktion der Auflösung aufgetragene Verhältnis sollte daher überall nahe 1 sein, wobei bei hoher Auflösung Abweichungen auftreten können. Um Fobs/Fcalc für einzelne Reflexe ohne Einteilung in Gruppen aufzutragen, das Feld **Binning** abhaken.

## Vollständigkeit
Trägt die Vollständigkeit der Beugungsdaten in Prozent (Laue- und Punktgruppen-Vollständigkeit) gegen die Auflösung auf. Gute Daten sind über den ganzen Auflösungsbereich nahezu 100% vollständig.

## Normalwahrscheinlichkeit
Trägt die geordneten gewichteten Abweichungen w(Fobs<sup>2</sup> - k * Fcalc<sup>2</sup>) gegen die Abweichungen auf, die bei normalverteilten Fehlern zu erwarten wären. Sind die Fehler tatsächlich normalverteilt, ist der Plot linear mit Steigung 1 und Achsenabschnitt 0. Deutliche Abweichungen davon können auf Probleme mit den Beugungsdaten, dem Modell oder dem Wichtungsschema hinweisen.

## Fraktale Dimension
Dieser Plot ist im Idealfall eine symmetrische, nach unten geöffnete Parabel; Rauschen in den Daten oder systematische Fehler verformen sie. Je schmaler die Kurve, desto flacher ist die Verteilung der Restelektronendichte; Minimum und Maximum der Restelektronendichte erscheinen als linker und rechter Schnittpunkt mit der *x*-Achse. Mehr zu diesem Plot: K. Meindl & J. Henn, Acta Cryst. A64, 404 (2008).

Hinweis: Dieser Plot braucht etwas länger als die anderen.

## Skalenfaktor gegen Auflösung
Bei guten Beugungsdaten sollte der Skalenfaktor über den ganzen Datenbereich etwa konstant bei 1 liegen. Ein kleiner Skalenfaktor bei großen 2&theta; kann bedeuten, dass die Daten bei hohen Winkeln schwach sind oder fehlen.

## R1 gegen Auflösung
R1 nimmt mit steigendem 2&theta; allmählich zu. Plötzliche Sprünge in R1 weisen auf Probleme mit den Beugungsdaten hin.

## Bijvoet-Differenzen: Wahrscheinlichkeitsplot
Trägt die Abweichungen der gemessenen von den berechneten Bijvoet-Differenzen auf, analog zum Plot **Normalwahrscheinlichkeit** oben. Dieser Plot weicht oft von einer Geraden ab, d.h. die experimentellen Fehler sind nicht normalverteilt. Hooft et al. (J. Appl. Cryst. 43, 665 (2010)) schlagen vor, dass eine Student-"t"-Verteilung die Fehler der Bijvoet-Differenzen besser beschreibt, besonders bei schlechter Datenqualität. Standardmäßig wird der Plot unter der Annahme normalverteilter (Gauß-)Fehler erzeugt. Ist **Student's t** angehakt, wird er mit der Student-"t"-Verteilung neu gezeichnet. Der Vergleich beider Plots zeigt, welche Verteilung die Fehler der Daten am besten beschreibt.

## Bijvoet-Differenzen: Streudiagramm
Hier werden die gemessenen Bijvoet-Differenzen &Delta;Fobs<sup>2</sup> = Fobs<sup>2</sup>(+) - Fobs<sup>2</sup>(-) gegen die berechneten &Delta;Fcalc<sup>2</sup> = Fcalc<sup>2</sup>(+) - Fcalc<sup>2</sup>(-) aufgetragen, mit Fehlerbalken für die Unsicherheit der gemessenen Differenzen. Bei richtig bestimmter absoluter Struktur hat das Diagramm eine positive Steigung nahe 1. Wie beim **Wahrscheinlichkeitsplot** oben lässt es sich mit der Normalverteilung (Standard) oder mit der Student-"t"-Verteilung (Feld **Student's t** anhaken) erzeugen. Eine negative Steigung kann auf eine falsch bestimmte absolute Struktur hinweisen, die dann mit folgendem Befehl invertiert werden muss:

| `inv -f` | Invertiert die aktuelle Struktur (der Schalter '<c>-f</c>' erzwingt die Inversion). |
