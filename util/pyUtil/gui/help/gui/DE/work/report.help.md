# collection-target
Proben-ID und Angaben zum Einreicher


# crystal-target
Name der Verbindung; Größe, Form, Farbe des Kristalls usw.


# crystal image-target
Bilder des Kristalls


# diffraction-target
Angaben zu Diffraktometer, Temperatur, Verfeinerungsdetails usw.


# absorption correction-target
Angaben zur Absorptionskorrektur


# publication-target
Angaben zu Publikation und Autoren


# citations-target
Zitate für die bei Lösung und Verfeinerung verwendete Software und Module


# reference-target
CSD-Refcode und Angaben zur Zeitschrift


# source files-target
Dateien, aus denen die CIF-Angaben zusammengestellt werden


# Report Settings 1
Tools, um (a) einen Bericht über die Struktur im HTML-Format und (b) eine CIF-Datei der Struktur zu erstellen.
<br>
<br>

Den Namen des Berichts wählen (Standard ist der Name der aktuell in Olex2 geöffneten Datei) und im Auswahlmenü das Bild für den Bericht wählen. Das Menü zeigt alle Bilddateien im Arbeitsordner der Struktur. Sind die übrigen Berichtseinstellungen unten gewählt, erzeugt **HTML-Bericht** einen Bericht als .HTML-Datei im Arbeitsordner der Struktur.


# Report Settings 2
Einen Stil sowie das Format von Kopf- und Fußzeile des Berichts wählen.


# Report Settings 3
Einen Stil für Zahlen und Suffixe in den Atomnamen des Berichts wählen.


# h3-collection-help
# Collection
Hier werden Angaben zur Datensammlung eingetragen: **Proben-ID**, Namen von **Einreicher** und **Bearbeiter** sowie verschiedene Daten.
<br>
<br>

**Angaben in diesen Feldern haben beim Schreiben der CIF-Datei Vorrang vor Angaben aus anderen Dateien.** Werden die CIF-Angaben mit der Schaltfläche **CIF-Info bearbeiten** unten geändert, haben diese Vorrang vor den Einträgen hier, und die neuen Werte erscheinen in diesen Feldern.


# h3-crystal-help
# Crystal
Hier werden Angaben zum Kristall des Beugungsexperiments eingetragen: der **Systematische Name** der Verbindung, falls bekannt (sonst '?'); **Farbe** (meist automatisch aus der .CIF_OD-Datei übernommen); **Größe** (Abmessungen in mm) und **Form** (Kristallbeschreibung aus dem Auswahlmenü); die Synthese der Verbindung (**Angaben zur Präparation**); **Angaben zur Kristallisation** (wie der Kristall gezüchtet wurde) und **Kristallmontage**.
<br>
<br>

**Angaben in diesen Feldern haben beim Schreiben der CIF-Datei Vorrang vor Angaben aus anderen Dateien.** Werden die CIF-Angaben mit der Schaltfläche **CIF-Info bearbeiten** unten geändert, haben diese Vorrang vor den Einträgen hier, und die neuen Werte erscheinen in diesen Feldern.


# Crystal Image
Hier lassen sich alle Fotos des Kristalls ansehen, die im Ordner 'movie' im Arbeitsordner der Struktur liegen. Eine Fotoserie (z.B. des montierten Kristalls, der sich auf dem Goniometer dreht) lässt sich mit der Wiedergabe-Schaltfläche in diesem Bereich als Animation abspielen.


# h3-diffraction-help
# Diffraction
Hier werden Angaben zum Beugungsexperiment eingetragen: Art des **Diffraktometers**; weitere Angaben zu Diffraktometer und Beugung (der Link **Definitionsdatei** öffnet ein Fenster zur Wahl eines Diffraktometers); die Temperaturen bei **Messung** und **Zellbestimmung**. Weitere **Besonderheiten** des Experiments und der Verfeinerung (z.B. Behandlung von Fehlordnung, Lösungsmittelmasken) lassen sich in die entsprechenden Felder eintragen.
<br>
<br>

**Angaben in diesen Feldern haben beim Schreiben der CIF-Datei Vorrang vor Angaben aus anderen Dateien.** Werden die CIF-Angaben mit der Schaltfläche **CIF-Info bearbeiten** unten geändert, haben diese Vorrang vor den Einträgen hier, und die neuen Werte erscheinen in diesen Feldern.


# h3-absorption correction-help
# Absorption Correction
Angaben zur Art der verwendeten Absorptionskorrektur (**Art**; **Details** des Verfahrens; **Tmax** und **Tmin**) werden automatisch aus den beim Experiment erzeugten Dateien übernommen und in diese Felder eingetragen. Fehlende Angaben lassen sich hier von Hand ergänzen.


# h3-publication-help
# Publication
Hier werden Angaben zur Publikation für die CIF-Datei eingetragen: **CCDC-Nummer** der Struktur (falls bekannt); **Kontaktautor** und weitere Autoren der Arbeit (aus der Benutzerdatenbank); Name der **Zeitschrift** und **Zeitschriftenstil** (allgemein oder Acta Cryst.). Über den Link **Contact Letter** lässt sich ein Text für das CIF-Feld *\_publ\_contact\_letter* eingeben.
<br>
<br>

**Angaben in diesen Feldern haben beim Schreiben der CIF-Datei Vorrang vor Angaben aus anderen Dateien.** Werden die CIF-Angaben mit der Schaltfläche **CIF-Info bearbeiten** unten geändert, haben diese Vorrang vor den Einträgen hier, und die neuen Werte erscheinen in diesen Feldern.


# Citations
Olex2 erstellt automatisch Literaturzitate für alle bei der Strukturbestimmung verwendete Software einschließlich Plugins (sofern über Olex2 aufgerufen oder in den Quelldateien gefunden).


# Reference
Hier lassen sich weitere Angaben zur Zeitschrift eintragen, in der die Struktur veröffentlicht ist: **CSD-Refcode** der Struktur (falls bekannt); Liste der **Autoren**; Name der **Zeitschrift**; **Band**; **Seiten** und **Jahr** der Veröffentlichung. Im letzten Feld kann ein **Kommentar** zur Publikation stehen.
<br>
<br>

**Angaben in diesen Feldern haben beim Schreiben der CIF-Datei Vorrang vor Angaben aus anderen Dateien.** Werden die CIF-Angaben mit der Schaltfläche **CIF-Info bearbeiten** unten geändert, haben diese Vorrang vor den Einträgen hier, und die neuen Werte erscheinen in diesen Feldern.


# h3-source files-help
# Source Files
Dieser Bereich zeigt die Quelldateien, aus denen Olex2 die CIF-Datei der Struktur zusammenstellt, und warnt bei widersprüchlichen Angaben in den Quellen.


# Metadata Sources
Olex2 durchsucht den Arbeitsordner nach Metadaten wie Angaben zum Diffraktometer und Messparametern, um sie in die CIF-Datei aufzunehmen, die nach der Verfeinerung entsteht. Solche Angaben werden normalerweise beim Beugungsexperiment in einer .CIF_OD-Datei festgehalten. Findet Olex2 keine Dateien mit Metadaten, gibt es eine kurze Meldung aus.


# Metadata Conflicts
Olex2 übernimmt die passenden Angaben automatisch aus den Metadatendateien in die CIF-Datei; das ist aber nicht immer einfach, weil die Quellen sich widersprechen können. Dann gibt Olex2 eine Fehlermeldung aus, und der Benutzer muss die Widersprüche von Hand auflösen, also die richtige Quelle für die CIF-Daten wählen.
<br>
<br>

Um die Fehlermeldung **<font color="red">There are unresolved conflicts</font>** zu beseitigen, den Bereich **Report** zu- und wieder aufklappen und die Widersprüche im sich öffnenden Fenster auflösen. Das Tool **Quelldateien** öffnet und schließt man per Klick. Olex2 bestätigt dann, dass alle Widersprüche aufgelöst sind. Der Link **Show ALL** listet alle Quellen der CIF-Daten, der Link **Reset Previously Resolved Conflicts** entfernt alle von Hand gewählten Angaben (sodass frühere Widersprüche wieder auftreten).


# CIF-Part-1-help
# CIF Part 1
Dieser Abschnitt betrifft das Erstellen und Ändern der CIF-Datei, die alles über die Struktur in einem von der IUCr festgelegten Format enthält. Eine vollständige und korrekte CIF-Datei ist für die Veröffentlichung einer Struktur in jeder begutachteten Zeitschrift unerlässlich. Normalerweise erstellt Olex2 die CIF automatisch; diese Tools sind für den Fall da, dass sie geändert werden muss.

## CIF-Info bearbeiten
Diese Schaltfläche öffnet eine Datei mit allen Angaben, die Olex2 beim Erstellen in die CIF-Datei aufnimmt. Die Einträge aus den Tools oben (**Messung**, **Kristall**, **Beugung** usw.) erscheinen hier. Der Inhalt dieser Datei lässt sich ändern, Einträge lassen sich auch hinzufügen oder entfernen. Änderungen hier haben Vorrang vor allen zuvor eingegebenen Werten, und die mit **CIF-Info bearbeiten** eingetragenen Werte erscheinen beim erneuten Öffnen der Tools oben.

## CIF zusammenführen
**CIF zusammenführen** nimmt die Metadaten aus den Quelldateien, den Tools oben und den mit **CIF-Info bearbeiten** eingegebenen Angaben und führt sie mit der CIF aus dem letzten Verfeinerungszyklus zusammen. Diese fertige CIF wird dann im Standard-Texteditor geöffnet.

## HKL und RES in der CIF ein-/ausschließen
Im Auswahlmenü wählen, wie Reflexdaten und Verfeinerungsanweisungen in die fertige CIF kommen. **Leave as is** übernimmt .hkl und .res so, wie das Verfeinerungsprogramm sie liefert; ShelXL fügt HKL und RES standardmäßig als einfachen Text ein. **Include** fügt die HKL/RES-Angaben als Loop (IUCr-Format) in die CIF ein. **Exclude** lässt HKL und RES weg – davon wird dringend abgeraten.


# CIF-Part-2-help
# CIF Part 2
Die IUCr bietet mit ~checkCIF~ einen kostenlosen Prüfdienst für CIF-Dateien an.

## IUCr-checkCIF-Bericht
Die Schaltfläche **IUCr checkCIF** schickt die zusammengeführte CIF zur Prüfung an diesen Dienst. Der ~checkCIF~-Bericht kommt als PDF oder HTML zurück (Auswahlmenü). Er hilft, mögliche Probleme der Struktur zu erkennen. Für eine vollständige Prüfung von CIF und Strukturfaktoren müssen die Strukturfaktoren zusätzlich als .fcf-Datei hochgeladen werden. Dazu und zu weiteren ~checkCIF~-Optionen siehe die Webseite URL[https://checkcif.iucr.org/,checkCIF].

## Eine Struktur beim CCDC hinterlegen
Es gibt zwei Arten der Einreichung beim Cambridge Crystallographic Data Centre (URL[https://www.ccdc.cam.ac.uk/,CCDC]).

### CCDC-Nummer anfordern
Die Hinterlegung einer Struktur in der ~Cambridge Structural Database~ (URL[https://www.ccdc.cam.ac.uk/solutions/csd-core/components/csd/,CSD]) verlangen inzwischen die meisten Zeitschriften. Diese Schaltfläche schickt die CIF-Datei und optional die Strukturfaktordatei an das CCDC. Nach der Bearbeitung erhält die Struktur eine eindeutige CCDC-Nummer, die dem hinterlegenden Autor meist innerhalb weniger Tage per E-Mail zugeht. Diese Nummer muss der Zeitschrift genannt werden, in der die Struktur erscheinen soll.

Hinweis: Damit die Bearbeitung zügig geht, müssen *alle* nötigen Angaben vorliegen, d.h. die Formulare des CCDC sollten so vollständig wie möglich ausgefüllt sein.
<br>
<br>

Wird eine Struktur nicht innerhalb von drei Jahren veröffentlicht und liegen keine anderen Anweisungen vor, versucht das CCDC, den hinterlegenden und den korrespondierenden Autor per E-Mail zu erreichen. Kommt keine Antwort, bewahrt das CCDC die Daten bis zu einer späteren Veröffentlichung unbegrenzt auf.

### Als CSD Communication veröffentlichen
Manchmal soll eine Struktur nicht in einer Fachzeitschrift erscheinen, wird aber in der CSD hinterlegt, um sie anderen Wissenschaftlern zugänglich zu machen. Dann lässt sie sich als "CSD Communication" veröffentlichen: das CCDC wird ermächtigt, sie direkt in die CSD aufzunehmen, was geschieht, sobald das CCDC sie bearbeitet hat.
<br>
<br>

Mehr zu CSD Communications in diesem URL[https://www.ccdc.cam.ac.uk/Community/blog/2018-06-CSDComm1/,Blog] und in dieser URL[https://www.ccdc.cam.ac.uk/Community/depositastructure/CSDCommunications/,Anleitung].


# CIF-Part-3-help
# CIF Part 3
Eine besondere Stärke von Olex2 ist, dass es die CIF-Angaben während des gesamten Lösungs- und Verfeinerungsprozesses synchron hält. Das ist recht knifflig, aber wenn alles wie vorgesehen funktioniert, muss man nie wieder eine CIF von Hand bearbeiten.

## CIF zusammenführen 1
Dieses Feld gibt es nur für die sehr seltenen Fälle, in denen beim Zusammenführen der CIF-Daten aus dem Verfeinerungsprogramm und der Angaben von Olex2 Probleme auftreten. Ist es angehakt, wie normalerweise, werden alle in dieser Zeile genannten Dateien mit den CIF-Angaben zusammengeführt. Geht dabei beim Erstellen der fertigen CIF etwas gründlich schief, das Häkchen entfernen. Das wird aber wirklich nicht empfohlen; muss es je entfernt werden, bitte das Problem per E-Mail an **support@olex2.org** beschreiben, damit es behoben werden kann.

## metacif
Der Link **metacif** öffnet die Datei, in der Olex2 alle verfügbaren Angaben zur Struktur sammelt. Diese Datei lässt sich auch mit der Schaltfläche **CIF-Info bearbeiten** oben öffnen; Änderungen darin haben, wie schon erwähnt, Vorrang vor allen anderen Quellen.

## Lokale/Standard-CIF hinzufügen
Damit lassen sich Angaben aus einer externen CIF-Datei in die CIF der aktuellen Struktur übernehmen. **local** für eine CIF im aktuellen Arbeitsordner, **default** für eine der eingebauten CIF-Dateien von Olex2, z.B. um Angaben zu einem bestimmten Diffraktometer hinzuzufügen.


# CIF Part 4
Ist dieses Feld angehakt, werden Angaben aus **metacif** in jedem Fall in die fertige CIF übernommen. Normalerweise stammen Einträge wie Verfeinerungsdetails (und andere im Abschnitt "skip_merge" der Olex2-Systemdatei *customisation.xlt* genannte Einträge) aus dem Verfeinerungsprogramm, nicht aus **metacif**; daher bleibt das Feld meist leer.


# ABS STR
Hier stehen bei chiralen Strukturen der Flack-Parameter *x* und der Hooft-Parameter *y*. Bei richtig bestimmter absoluter Struktur liegen beide nahe 0. Liegen sie nahe 1, muss die Struktur eventuell mit '<c>inv -f</c>' invertiert werden. Im Auswahlmenü das Verfahren wählen, mit dem die absolute Struktur bestimmt wurde (meist **Anomalous dispersion**).
