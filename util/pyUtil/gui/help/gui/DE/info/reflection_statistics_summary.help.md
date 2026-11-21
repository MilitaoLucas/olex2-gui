# Reflection-Statistics-Summary-help
# Reflection Statistics Summary
Diese Tabelle fasst die wichtigsten Kennzahlen für die Qualität der Beugungsdaten zusammen, gegen die verfeinert wird. Sie hängen weder vom Strukturmodell noch von der Verfeinerung ab.

## TotalReflections
Gesamtzahl der im Beugungsexperiment gemessenen Reflexe.

## UniqueReflections
Gesamtzahl der unabhängigen (nicht symmetrieverwandten) Reflexe des Beugungsexperiments.

## DataCount
Gleich der Zahl der unabhängigen Reflexe, siehe oben.

## FriedelOppositesMerged
"1" bedeutet, dass Friedel-Paare (*h*, *k*, *l*) und (-*h*, -*k*, -*l*) in den Daten gemittelt wurden, "0", dass keine gemittelt wurden.

## InconsistentEquivalents
Anzahl der Paare äquivalenter Reflexe, die im Datensatz deutlich voneinander abweichen.

## SystematicAbsencesRemoved
Gesamtzahl der systematisch ausgelöschten Reflexe, die aus dem Datensatz entfernt wurden.

## MinD
Kleinster *d*-Wert (höchste Auflösung) des Datensatzes in &Aring;.

## MaxD
Größter *d*-Wert (niedrigste Auflösung) des Datensatzes in &Aring;.

## LimDmin
Kleinster möglicher *d*-Wert (theoretische Grenze aus den Zellabmessungen) in &Aring;. Der Wert kann wegen *SHEL*- oder Bereichs-*OMIT*-Anweisungen (z.B. "SHEL 15 0.8" oder "OMIT -3 50") über der theoretischen Grenze liegen.

## LimDmax
Größter möglicher *d*-Wert in &Aring;. Er kann durch *SHEL*- oder Bereichs-*OMIT*-Anweisungen (z.B. "SHEL 15 0.8" oder "OMIT -3 50") beeinflusst sein.

## FilteredOff
Anzahl der Reflexe, die durch *SHEL*- oder Bereichs-*OMIT*-Anweisungen (z.B. "SHEL 15 0.8" oder "OMIT -3 50") aus den Daten entfernt wurden.

## OmittedByUser
Anzahl der Reflexe, die durch gezielte *OMIT*-Anweisungen wie "OMIT 1 0 0" ausgelassen wurden.

## OmittedReflections
Anzahl der Reflexe, die aus dem Datensatz entfernt und in der .hkl-Datei hinter die Zeile (*h*, *k*, *l*) = (0, 0, 0) gestellt wurden.

## IntensityTransformed
Anzahl der Reflexe, deren Intensitäten durch eine Anweisung "OMIT s" verändert wurden, d.h. deren Fobs<sup>2</sup> im ganzen Datensatz durch 0.5s&sigma;(Fobs<sup>2</sup>) ersetzt wurde.

## Rint
Ein Maß für die Genauigkeit, mit der die einzelnen Reflexe im Beugungsexperiment gemessen wurden. Ist Rint etwa zwei- bis dreimal so groß wie Rsigma (siehe unten), stimmt mit dem Datensatz möglicherweise etwas nicht.

## Rsigma
Ein Maß für das Signal-Rausch-Verhältnis des Beugungsexperiments.

## MeanIOverSigma
Mittelwert von I/&sigma;(I) über den ganzen Datensatz; ein Maß für das Signal-Rausch-Verhältnis des Beugungsexperiments.

## Completeness
Punktgruppen-Vollständigkeit des Datensatzes bis zum größten gemessenen 2&theta;.

## MaxIndices
Größte Werte der Indizes *h*, *k* und *l* in den für die Verfeinerung verwendeten Daten (also nach Anwendung der *OMIT*-Anweisungen).

## MinIndices
Kleinste Werte der Indizes *h*, *k* und *l* in den für die Verfeinerung verwendeten Daten (also nach Anwendung der *OMIT*-Anweisungen).

## FileMaxIndices
Größte Werte der Indizes *h*, *k* und *l* im Datensatz, wie ursprünglich gemessen.

## FileMinIndices
Kleinste Werte der Indizes *h*, *k* und *l* im Datensatz, wie ursprünglich gemessen.

## ReflectionAPotMax
Größte Redundanz eines Reflexes im Datensatz (symmetrieäquivalente Reflexe mitgezählt).

## FriedelPairCount
Anzahl der (in P1) gemessenen Friedel-Paare (*h*, *k*, *l*) und (-*h*, -*k*, -*l*).

## Redundancy
In der Zahlenreihe (*n*<sub>1</sub>, *n*<sub>2</sub>, *n*<sub>3</sub>, ...) ist *n*<sub>1</sub> die Zahl der einmal gemessenen Reflexe, *n*<sub>2</sub> die der zweimal gemessenen, *n*<sub>3</sub> die der dreimal gemessenen usw.

## IsCentrosymmetric
1, wenn die Struktur zentrosymmetrisch ist, 0, wenn nicht.

## Completeness\_laue\_full
Laue-Vollständigkeit des Datensatzes bis zur von der IUCr empfohlenen Auflösungsgrenze sin(&theta;)/&lambda; &ge; 0.6 (z.B. 2&theta; &ge; 50.5&deg; für Mo-K&alpha;-Strahlung).

## Completeness\_point\_full
Punktgruppen-Vollständigkeit des Datensatzes bis zur von der IUCr empfohlenen Auflösungsgrenze sin(&theta;)/&lambda; &ge; 0.6 (z.B. 2&theta; &ge; 50.5&deg; für Mo-K&alpha;-Strahlung).

## Completeness\_laue\_max
Laue-Vollständigkeit des Datensatzes bis zum größten gemessenen 2&theta;.

## Completeness\_point\_max
Punktgruppen-Vollständigkeit des Datensatzes bis zum größten gemessenen 2&theta;.
