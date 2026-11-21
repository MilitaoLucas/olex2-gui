# bad reflections target
Tools für schlecht passende Reflexe.


# OMIT REFLECTIONS
Die Schaltfläche **OMIT** setzt in der Instruktionsdatei eine *OMIT*-Anweisung für alle Reflexe, bei denen |Fehler/esd| größer ist als der Wert im Feld (Standard 10).
<br>
<br>

Die Schaltfläche **OMITs löschen** entfernt ALLE *OMIT*-Anweisungen; alle zuvor ausgelassenen Reflexe stehen der Verfeinerung wieder zur Verfügung, außer denen, die durch eine allgemeine *OMIT*-Anweisung ausgelassen werden, z.B. *OMIT -3 52*.


# Bad Reflections Sorting
Ist dieses Feld angehakt, werden die schlechten Reflexe nach dem nächsten Verfeinerungszyklus nach fallendem |Fehler/esd| sortiert. Ist es nicht angehakt, werden sie im nächsten Zyklus vom größten positiven bis zum größten negativen Fehler/esd sortiert.


# Bad Reflections
Dieser Bereich enthält die Reflexe, für die das Verfeinerungsprogramm die größten Werte von |Fehler/esd| ermittelt hat.

## Alle äquivalenten Reflexe auslassen
Einen einzelnen Reflex (und alle seine äquivalenten Reflexe) schließt man mit dem Link **OMIT** daneben in der Liste aus. Damit wird die passende *OMIT*-Anweisung in die Instruktionsdatei eingetragen.


# Exclude hkl
Hier lassen sich Bedingungen festlegen, nach denen bestimmte Gruppen von Reflexen ausgeschlossen werden.

## Standardmodus (ODER)
Beim Klick auf den Link **Ausschließen:** werden alle Reflexe, die die Bedingungen für *h*, *k* ODER *l* erfüllen, im nächsten Verfeinerungszyklus ausgelassen.

## UND-Modus
Ist das Feld **AND** angehakt, muss ein Reflex die Bedingungen für *h*, *k* UND *l* erfüllen, um beim Klick auf **Ausschließen:** aus der Verfeinerung genommen zu werden.

## Zurücksetzen
Der Link **Zurücksetzen** löscht alle gesetzten Ausschlussbedingungen für *h*, *k* und *l*.


# Edit reflections
Man kann auch einen bestimmten Reflex auslassen (z.B. weil er vom Beamstop verdeckt war). Dazu öffnet der Link **Reflexe bearbeiten** eine Datei mit allen schlechten Reflexen. Ein "-" (Minuszeichen) vor einem Reflex verschiebt ihn ans Ende der hkl-Datei (hinter die Zeile "0 0 0"), sodass das Verfeinerungsprogramm ihn nicht mehr verwendet. Wird das "-" vor einem ausgelassenen Reflex in dieser Datei durch ein "+" ersetzt, ist er im nächsten Verfeinerungszyklus wieder dabei.
