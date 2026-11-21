# Shelx Restraints
Dies sind die Restraints von SHELX. Sie gelten alle auch bei einer Verfeinerung mit olex2.refine. Die Schaltfläche **go** wendet den Restraint auf die ausgewählten Atome an.


# DFIX
Verwendung: **DFIX d s[0.02] Atompaar(e)**<br>
Zieht den Abstand zwischen Atompaaren per Restraint auf den Wert **d** in &Aring;, mit einer Standardunsicherheit von &plusmn; **s** (Standard 0.02 &Aring;).
<br>
<br>

**Beispiel:** &nbsp; *DFIX 1.54 0.01 C1 C2 C2 C3 C3 C4*<br>
Hält die C-C-Bindungslängen benachbarter Kohlenstoffatome einer Butylgruppe bei 1.54 &plusmn; 0.01 &Aring;, also zwischen 1.53 und 1.55 &Aring;.
![0.3 n-Butan](images/butane.jpg)


# DANG
Verwendung: **DANG d s[0.04] Atompaare**<br>
Zieht den "1,3-Abstand" oder "Winkelabstand" (den Abstand zweier Atome, die an ein drittes, zentrales Atom gebunden sind) per Restraint auf den Wert **d**, mit einer Standardunsicherheit von &plusmn; **s** (Standard 0.04 &Aring;).
<br>
<br>

**Beispiel:** &nbsp; *DANG  1.33 0.02 H1 H2*<br>
Hält den H-H-Abstand in einem Wassermolekül bei 1.33 &plusmn; 0.02 &Aring;.


# SADI
Verwendung: **SADI s[0.02] Atompaare**
<br>
<br>

Hält die Bindungslängen der angegebenen Atompaare per Restraint gleich, mit einer Standardunsicherheit von &plusmn; **s** (Standard 0.02 &Aring;).
<br>
<br>

**Beispiel:** &nbsp; *SADI 0.005&nbsp;&nbsp;C1 F1&nbsp;&nbsp;&nbsp;C1 F2&nbsp;&nbsp;&nbsp;C1 F3*<br>
Hält die C-F-Abstände einer CF<sub>3</sub>-Gruppe gleich (innerhalb &plusmn;0.005 &Aring;).


# CHIV
Verwendung: **CHIV V[0] s[0.1] Atomnamen**
<br>
<br>

Zieht das "chirale Volumen" der genannten Atome per Restraint auf das Volumen **V** &Aring;<sup>3</sup>, innerhalb &plusmn; **s** &Aring;. Das "chirale Volumen" ist das Volumen des Parallelepipeds, dessen Kanten die drei kürzesten Bindungen vom genannten Atom zu genau drei anderen Nicht-Wasserstoffatomen sind.


# FLAT
Verwendung: **FLAT s[0.1] vier oder mehr Atome**
<br>
<br>

Hält die genannten Atome per Restraint in einer Ebene.
<br>
<br>

**Beispiel:** &nbsp; *FLAT C1 C2 C3 C4 C5 C6 C7*<br>
Hält die sieben Kohlenstoffatome eines Toluolmoleküls in einer Ebene.


# DELU
Verwendung: **DELU s1[0.01] s2[0.01] Atomnamen**
<br>
<br>

Wendet einen "Rigid-Bond"-Restraint auf die Bindungen zwischen den genannten Atomen an. Für benachbarte Atome werden die Komponenten der anisotropen Auslenkungsparameter in Bindungsrichtung innerhalb &plusmn; **s1** &Aring; gleich gehalten. Ein ähnlicher Restraint mit **s2** gilt für 1,3-Abstände.


# SIMU
Verwendung: **SIMU s[0.04] st[0.08] dmax[2.0] Atomnamen**
<br>
<br>

Genannte Atome, die näher als **dmax** beieinander liegen, erhalten per Restraint gleiche Uij-Komponenten (anisotrope Auslenkungsparameter, ADPs), innerhalb &plusmn; **s** &Aring;.
<br>
<br>

**Beispiel:** &nbsp; *SIMU C1 C2 C3 O1*<br>
Hält die ADPs der Atome eines Acetonmoleküls ähnlich.


# ISOR
Verwendung: **ISOR s[0.1] st[0.2] Atomnamen**
<br>
<br>

Zieht die Uij-Komponenten der genannten Atome per Restraint auf isotrope Werte, innerhalb &plusmn; **s** (&plusmn; **st** für endständige oder isolierte Atome). Die betroffenen Atome erhalten annähernd kugelförmige ADPs. Nützlich, um stark verformte oder nicht positiv definite (NPD) ADPs zu verhindern, aber nicht wahllos einzusetzen.
<br>
<br>

**Beispiel:** &nbsp; *ISOR C5 C6*<br>
Hält die ADPs der Atome C5 und C6 annähernd kugelförmig.


# RIGU
Verwendung: **RIGU s1[0.004] s2[0.004] Atomnamen**
<br>
<br>

Wendet verstärkte "Rigid-Bond"-Restraints (siehe **DELU** oben) auf Bindungen zwischen benachbarten Atomen und auf 1,3-Abstände an, mit den Standardunsicherheiten **s1** bzw. **s2**.
<br>
<br>

**Beispiel:** &nbsp; *RIGU C1 Cl1 Cl2*<br>
Wendet verstärkte Rigid-Bond-Restraints auf ein Dichlormethanmolekül an.
