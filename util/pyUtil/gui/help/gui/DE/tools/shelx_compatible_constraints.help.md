# Shelx Constraints
Dies sind die Constraints von SHELX. Sie gelten alle auch bei einer Verfeinerung mit olex2.refine.

## AFIX
Die Anweisung **AFIX** setzt Wasserstoffatome auf idealisierte (reitende) Positionen.

## EXYZ
Die Anweisung **EXYZ** legt fest, dass zwei oder mehr Atome dieselben Koordinaten *x*, *y* und *z* haben.

## EADP
Legt fest, dass zwei oder mehr Atome dieselben anisotropen Auslenkungsparameter haben, z.B. die drei Fluoratome einer CF<sub>3</sub>-Gruppe.


# AFIX
*AFIX*-Anweisungen setzen Wasserstoffatome auf idealisierte (reitende) Positionen in der Struktur.

## Syntax des AFIX-Befehls
Verwendung: **AFIX mn d[number] sof[11] U[10.08]**
<br>
<br>
Aus dem SHELX-Handbuch (übersetzt):<br>
"AFIX wendet Constraints an und/oder erzeugt idealisierte Koordinaten für alle Atome bis zur nächsten AFIX-Anweisung. Die Ziffern mn des AFIX-Codes steuern zwei logisch ganz getrennte Vorgänge. m bezieht sich auf geometrische Operationen, die vor dem ersten Verfeinerungszyklus ausgeführt werden (Wasserstoffatome werden vor jedem Zyklus idealisiert), und n legt Constraints fest, die während der gesamten Kleinste-Quadrate-Verfeinerung gelten. n ist immer eine einzelne Ziffer; m kann zwei, eine oder keine Ziffer haben (Letzteres entspricht m = 0)." <br>
<br>
Mehr dazu im URL[https://shelx.uni-goettingen.de/shelxl_html.php, SHELX-Handbuch].

## Zahlen-Auswahlmenüs
In dieser Zeile beziehen sich die ersten beiden Auswahlmenüs *nach* dem Constraint-Menü auf m und n des *AFIX*-Befehls.

## clear
Atome auswählen, auf die ein *AFIX*-Befehl angewendet wurde. **clear** entfernt den *AFIX*-Befehl.

## de
**de** startet einen Modus, in dem alle *AFIX*-Anweisungen der Struktur angezeigt werden. In diesem Modus lässt sich auch der in diesem Bereich eingestellte *AFIX*-Befehl durch Anklicken auf einzelne Atome anwenden.

## go
**go** wendet den in diesem Bereich eingestellten *AFIX*-Befehl an.


# EXYZ
Verwendung: **EXYZ Atomnamen**
<br>
<br>

Dieser Befehl gibt allen genannten Atomen dieselben Koordinaten *x*, *y* und *z* (für Fälle, in denen zwei oder mehr Elemente dieselbe Lage in einer Struktur teilen, wie oft in Mineralen). Oft zusammen mit *EADP* verwendet. Die Koordinaten (und eventuell Verweise auf freie Variablen) werden vom ersten genannten Atom übernommen. Ein Atom darf nur in einer *EXYZ*-Anweisung vorkommen.


# EADP
Verwendung: **EADP Atomnamen**
<br>
<br>

Aus dem SHELX-Handbuch (übersetzt):<br>
"Für alle genannten Atome werden dieselben isotropen oder anisotropen Auslenkungsparameter verwendet. Die Auslenkungsparameter (und eventuell Verweise auf freie Variablen) werden vom ersten Atom der Liste übernommen, das per EADP mit anderen Atomen verknüpft ist. Die für die Uij der anderen Atome angegebenen Werte, Verweise auf freie Variablen usw. werden ignoriert. Die beteiligten Atome müssen entweder alle isotrop oder alle anisotrop sein. 'Gegenüberliegende' Fluoratome von PF<sub>6 </sub> oder fehlgeordneten -CF<sub>3 </sub>-Gruppen sind gute Kandidaten für EADP, z.B.
<br>
<br>

EADP F11 F14<br>
EADP F12 F15<br>
EADP F13 F16<br>
C1 .......<br>
PART 1<br>
F11 ...... 21 ......<br>
F12 ...... 21 ......<br>
F13 ...... 21 ......<br>
PART 2<br>
F14 ...... -21 ......<br>
F15 ...... -21 ......<br>
F16 ...... -21 ......<br>
PART 0
<br>
<br>

EADP ist ein (exakter) *Constraint*. Die Anweisung SIMU zieht die Uij-Komponenten benachbarter Atome dagegen per *Restraint* mit einer passenden (meist recht großen) Standardunsicherheit auf ungefähr gleiche Werte."
<br>
<br>

Mehr dazu im URL[https://shelx.uni-goettingen.de/shelxl_html.php, SHELX-Handbuch].
