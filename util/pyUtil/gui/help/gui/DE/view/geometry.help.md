# Geometry
Hier finden sich Tools zur Analyse verschiedener geometrischer Parameter einer Struktur.


# Mean Plane and Best Line
## Beste Ebene berechnen
Drei oder mehr Atome auswählen, durch die eine Ebene gelegt werden soll, dann diese Schaltfläche anklicken oder '<c>mpln sel</c>' eingeben. Eine beste Ebene durch die ausgewählten Atome wird zusammen mit ihrem Schwerpunkt angezeigt. Die Ausgabe enthält die Ebenengleichung, die hkl-Richtung der Ebenennormalen und die mittlere quadratische Abweichung (RMS, in &Aring;) der Atomlagen von der Ebene. Alle symmetrieäquivalenten Ebenen werden automatisch an weitere Fragmente auf dem Bildschirm angefügt. Zum Löschen einer Ebene diese anklicken und '<c>Entf</c>' drücken (oder ausblenden: rechte Maustaste auf die Ebene und im Untermenü **Graphics** **Hide** wählen). Sollen alle angezeigten Ebenen gelöscht werden, mit '<c>sel planes</c>' alle auswählen und dann '<c>Entf</c>' drücken.

## Beste Gerade berechnen
Zwei oder mehr Atome auswählen, durch die eine beste Gerade gelegt werden soll. Ein Klick auf diese Schaltfläche berechnet die beste Gerade durch die Atome und zeigt sie ähnlich wie eine Bindung an.


# Distances and Angles
## Abstände und Winkel
Zeigt im Ausgabefenster den Atomabstand (bei zwei ausgewählten Atomen), den Winkel (bei drei) oder den Torsionswinkel und das Tetraedervolumen (bei vier ausgewählten Atomen).

Hinweis: Damit für diese Werte genaue Standardunsicherheiten angezeigt werden, muss zuerst mit der Schaltfläche **Verfeinern und e.s.d.-Angaben speichern** verfeinert werden.

## Verfeinern und e.s.d.-Angaben speichern
Führt eine Verfeinerung durch und speichert die Angaben, die für genaue Standardunsicherheiten von Größen wie Bindungslängen und -winkeln nötig sind.


# Analyse Interactions
Analyse nichtbindender Wechselwirkungen in einer Struktur.

## &pi;-&pi;-Wechselwirkungen
Sucht &pi;-&pi;-Wechselwirkungen in der Struktur; werden welche gefunden, erscheinen die zugehörigen geometrischen Parameter (z.B. der Abstand zwischen den Schwerpunkten benachbarter aromatischer Ringe) im Ausgabefenster.

## Wasserstoffbrücken
Findet und zeigt die Wasserstoffbrücken der Struktur. Der entsprechende Befehl ist '<c>htab -g</c>'. In beiden Fällen erscheint eine Tabelle im Ausgabefenster.
<br>
<br>

Ein weiterer nützlicher Befehl zur Analyse nichtbindender Wechselwirkungen ist '<c>htab -t</c>'. So zeigt z.B. '<c>htab -t=Br,I</c>' alle Br---I-Halogenbrücken der Struktur.
