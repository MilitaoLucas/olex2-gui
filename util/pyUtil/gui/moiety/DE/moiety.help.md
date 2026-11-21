[comment]: < German translation of ../moiety.help.md; '#' headings are help IDs and stay English. Panel labels stay as the panel shows them. >

# Moiety Formula
Die **Moiety-Formel** (_chemical_formula_moiety) führt die chemisch unterscheidbaren Einheiten der Struktur auf – Moleküle und Ionen – jede mit ihrer Ladung, so wie die IUCr sie in der CIF verlangt, z.B. *C12 H10 N2 O4, 2(Cl -)*.

Dieses Tool ermittelt sie aus dem Modell: es zerlegt die Struktur in Fragmente, leitet für jedes eine Ladung ab und prüft, ob die Ladungen ausgeglichen sind.

Dazu werden Metalle von ihren Liganden getrennt, mit einer Ausnahme: ein Metall mit nur einatomigen Liganden, dessen Formel ein bekanntes Ion ist, bleibt ganz, z.B. Chromat *(Cr O4 2-)*, Permanganat, Tetrathiomolybdat oder Tetrachlorocobaltat. Eine solche Einheit darf zusätzlich an ein anderes Metall gebunden sein; sie zählt trotzdem als das Ion.

## Die Tabelle
Das Auswahlmenü oben wählt die Formel (siehe *Vorgeschlagene Moiety-Formeln*). Die Tabelle führt dann jedes Fragment auf:

- **n** – wie oft das Fragment vorkommt
- **Formula** – die Formel des Fragments (eine Teilbesetzung steht in Klammern)
- **Total** – n x Ladung
- **Charge** – die Ladung eines Fragments, änderbar (siehe unten)
- **Confidence** – woher die Ladung stammt

Unter den Fragmenten summiert die **Ladungsbilanz** die Ladungen, zuerst je Fragment und dann die Ladungen allein, positive in Rot und negative in Blau; bei einer sinnvollen Formel ist die Summe 0.

## Confidence
- **lookup** – ein bekanntes Ion oder Molekül (eingebaute Tabelle)
- **user lookup** – eine Ladung, die Sie früher für diese Formel eingegeben haben (siehe *Eigene Ladungen*)
- **user** – eine Ladung, die Sie für diese Struktur eingegeben haben
- **balance** – die einzige unbekannte Ladung, so bestimmt, dass alles 0 ergibt
- **element** / **ambiguous!** – ein einzelnes Element (oft ein Metall) mit seiner häufigsten Oxidationsstufe oder ein Ion wie Mn O4 mit seiner häufigsten Ladung; *ambiguous* heißt, dass auch andere Werte häufig sind – prüfen
- **assumed neutral** – kein Metall und kein Ion in der Struktur, das Fragment gilt daher als neutral
- **SUSPECT** – die Bilanz ergibt eine für dieses Fragment chemisch unwahrscheinliche Ladung; meist ist die Oxidationsstufe eines Metalls falsch
- **???** – keine Ladung bestimmbar: selbst eingeben

## Ladungen bearbeiten
Jede Ladung ist ein Eingabefeld. Eine Ladung eintippen – **2+**, **+2**, **2-**, **-1** oder **0** – und **Enter** drücken oder das Feld verlassen: die Confidence des Fragments wird *user*, und Bilanz, vorgeschlagene Formeln und **Apply to CIF** werden aktualisiert. Bleibt eine unbekannte Ladung übrig, wird sie aus der Bilanz bestimmt.

**?** eintippen (oder das Feld leeren), um zur abgeleiteten Ladung zurückzukehren. **Clear user-supplied charges** (unter der Ladungsbilanz) nimmt alle für diese Struktur eingegebenen Ladungen zurück.

## Eigene Ladungen
Ladungen, die Sie für mehratomige Fragmente eingeben, werden in der Datei *user_charges.csv* (in DataDir()/gui/moiety) gespeichert und bei späteren Strukturen für dieselbe Formel wieder verwendet, angezeigt als **user lookup**. Einzelne Elemente werden nie gespeichert – die Oxidationsstufe eines Metalls gehört zu einer Struktur, nicht zum Element. Ein **?** bei einer Ladung *user lookup* entfernt sie aus der Datei.

## Vorgeschlagene Moiety-Formeln
Das Auswahlmenü bietet:

- **Best guess** – die Ladungen aus der Tabelle, mit gemischter Valenz, wenn nur so die Bilanz aufgeht
- **All nx M as +q** – jedes mehrdeutige Metall in einer einzigen Oxidationsstufe
- **Grown structure as displayed** – die Formel dessen, was auf dem Bildschirm ist, wenn die Struktur vervollständigt ist und sich dadurch eine andere Formel ergibt. Sie verwendet die für die Fragmente bestimmten Ladungen, auch selbst eingegebene; ein nur teilweise angezeigtes Fragment zeigt **?**. Die Gesamtladung der angezeigten Struktur steht hinter der Formel. Welcher Eintrag auch gewählt ist, diese Formel und Ladung erscheinen unter der Formel im Bereich. Sie werden auch in der Konsole unter der vorgeschlagenen Formel ausgegeben, erneut nach jeder Verfeinerung. Eine Struktur, die nach dem Zeichnen des Bereichs vervollständigt wurde, erscheint beim nächsten Neuzeichnen, z.B. beim Schließen und Öffnen von Abschluss
- **No charges** – die Formel, wie sie ist, ohne Ladungen

**Apply to CIF** schreibt die gewählte Formel nach _chemical_formula_moiety. Inhalte maskierter Lösungsmittelbereiche (aus der Lösungsmittelmaske oder SQUEEZE) werden in die Formel aufgenommen, wenn sie identifiziert werden konnten.
