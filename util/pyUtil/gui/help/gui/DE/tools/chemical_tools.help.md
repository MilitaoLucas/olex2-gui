# Elemental Analysis
Elementaranalyse, Molmasse und simuliertes Massenspektrum.

## Elementaranalyse: CHN
Berechnet die erwarteten Werte einer CHN-Analyse aus dem Strukturmodell. Außerdem werden die Molmasse in g/mol und eine vollständige Elementaranalyse angegeben. Der entsprechende Befehl ist '<c>calcCHN</c>'.

## Molekulares Isotopenmuster: Massenspektrum
Berechnet ein simuliertes molekulares Isotopenmuster der Struktur aus den natürlichen Häufigkeiten aller Isotope. Entspricht dem Befehl '<c>calcms</c>'.


# Molecular Volume
Gesamtvolumen des Moleküls und Polyedervolumen einzelner Atome.

## Molekülvolumen
Berechnet die molekulare Oberfläche in &Aring;<sup>2</sup> und das Molekülvolumen in &Aring;<sup>3</sup>. Der Befehl ist '<c> vvol</c>'.

## Polyedervolumen berechnen
Berechnet das Volumen eines Polyeders um das ausgewählte Atom (Befehl '<c>calcvol</c>').


# R S Chirality Designations
Tools zur Analyse chiraler Kohlenstoffatome einer Struktur.

## R/S-Bezeichnungen chiraler Kohlenstoffe auflisten
Gibt eine Liste aller chiralen Kohlenstoffatome der asymmetrischen Einheit mit ihrer R/S-Konfiguration aus. Der entsprechende Befehl ist '<c>rsa</c>'.

## Chirale Kohlenstoffe als R/S beschriften
Beschriftet jedes chirale Kohlenstoffatom auf dem Bildschirm mit seiner R- oder S-Konfiguration.


# Bounding Box and Geometry Index
Zeigt eine rechteckige Begrenzungsbox oder berechnet einen Geometrie-Index.

## Molekulare Begrenzungsbox
Diese Schaltfläche (oder '<c>wbox</c>') zeigt eine rechteckige Box um die Struktur auf dem Bildschirm. Die Struktur erscheint raumfüllend, und Abmessungen und Volumen der Box werden angezeigt. Zum Entfernen der Box mit der rechten Maustaste darauf klicken und **Hide** wählen. Zurück zur Kugel-Stab-Darstellung mit '<c>pers</c>'.

## Geometrie-Index
Berechnet für 4- und 5-fach koordinierte Geometrien den **Geometrie-Index** des Zentralatoms URL[https://en.wikipedia.org/wiki/Geometry_index,WIKIPEDIA]. Verfahren und Literatur stehen im verlinkten Wikipedia-Artikel.

### 4-fach koordiniert
Aus den Bindungswinkeln um ein ausgewähltes vierfach koordiniertes Atom wird der Parameter &tau;<sub>4</sub> berechnet. Er zeigt, ob die Umgebung des Atoms quadratisch-planar (&tau;<sub>4</sub> = 0) oder tetraedrisch (&tau;<sub>4</sub> = 1) ist.
<br>
<br>

Zusätzlich wird der Parameter &tau;<sub>4</sub>' berechnet, der immer kleiner oder gleich &tau;<sub>4</sub> ist. Auch &tau;<sub>4</sub>' ist 0 für quadratisch-planare und 1 für tetraedrische Geometrie. Mit &tau;<sub>4</sub>' lassen sich aber auch andere Formen unterscheiden, etwa die Wippen-Geometrie (seesaw), für die &tau;<sub>4</sub> &asymp; 0.43 und &tau;<sub>4</sub>' &asymp; 0.24 ist.

### 5-fach koordiniert
Aus den Bindungswinkeln um ein ausgewähltes fünffach koordiniertes Atom wird der Parameter &tau;<sub>5</sub> berechnet. Er zeigt, ob die Umgebung des Atoms quadratisch-pyramidal (&tau;<sub>5</sub> = 0) oder trigonal-bipyramidal (&tau;<sub>5</sub> = 1) ist.
