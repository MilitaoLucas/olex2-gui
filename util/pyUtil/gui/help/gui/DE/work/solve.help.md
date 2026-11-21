# solve-target
Die Struktur lösen


# solve-settings-target
Die Lösungseinstellungen öffnen


# Solution Program
Sind Lösungsprogramme auf dem System auf übliche Weise installiert, findet Olex2 sie, und sie erscheinen automatisch im Auswahlmenü **Programm**. Erscheinen sie nicht, sicherstellen, dass ihr Installationsordner im **Systempfad** liegt oder unter **Start > Einstellungen > PATH** eingetragen ist. Ilia Guzeis Handbuch, verlinkt im Tool **Start** im Bereich **Start**, beschreibt die Installation von Lösungsprogrammen genau.

## Wahl der Programme
Olex2 kann viele Strukturlösungsprogramme verwenden, etwa:

  - **ShelXT**
  - ShelXS
  - ShelXD
  - olex2.solve
  - SuperFlip
  - Sir2011
  - Sir2008

## Lösungsmethode
Die Methode für das gewählte Lösungsprogramm wählen. Das ist eigentlich nur für **ShelXS** von Bedeutung – alle anderen Programme haben nur eine Lösungsmethode!


[comment]: < Help text for "Reflections" is now taken from refine.md. >


# Chemical Formula
Die erwartete chemische Zusammensetzung der Struktur. Stehen in der erwarteten Zusammensetzung Schweratome, die in der Struktur gar nicht vorhanden sind, kann das manchen Lösungsprogrammen schaden. Ebenso kann es Probleme machen, ein tatsächlich vorhandenes Schweratom in der erwarteten Zusammensetzung wegzulassen.

## Z
*Z* ist die Zahl der Formeleinheiten in der Elementarzelle. Bei Molekülverbindungen ist *Z* die Zahl der ganzen Moleküle in der Zelle. Bei kontinuierlichen Festkörpern und Strukturen, die "vervollständigt" werden müssen (siehe **View > Symmetrieerzeugung > Vervollständigen**), ist *Z* weniger leicht zu bestimmen, aber im Allgemeinen ebenfalls die Zahl der Formeleinheiten in der Zelle.

## Z'
Der eng verwandte Parameter *Z*' (*Z* Strich) ist die Zahl der Formeleinheiten in der asymmetrischen Einheit.


# Space-Group-help
# Space Group
Die Raumgruppe wird normalerweise bei Datenaufnahme und -reduktion bestimmt.

## RG vorschlagen
| `sg` | Olex2 kann die Raumgruppe auch selbst bestimmen. Ein Klick auf **RG vorschlagen** zeigt die wahrscheinlichsten im Auswahlmenü rechts. Falls nötig, öffnet 'text' eine Textdatei mit der vollständigen Ausgabe der Raumgruppenanalyse. Vor der Verfeinerung eine Raumgruppe im Auswahlmenü wählen. |
<br>
<br>

Man kann eine Raumgruppe auch direkt in das Menüfeld dieser Zeile tippen. Ein Klick außerhalb des Feldes bereitet die Struktur auf die Lösung in dieser Raumgruppe vor.


# Solution Settings Extra
Manche Lösungsprogramme haben zusätzliche Einstellungen, die in der GUI nicht vorkommen; sie lassen sich hier angeben.

# CF
Mehrere Variablen beeinflussen die Lösung mit Charge-Flipping:
<br>
<br>

AMPT - Charge-Flipping kann mit F, E oder Quasi-E erfolgen.
<br>
<br>

MAPT - Größte Zahl von Versuchen, einen Phasenübergang zu finden
<br>
<br>

MACM - Größte Zahl von Versuchen, eine scharfe Korrelationskarte zu erhalten
<br>
<br>

MASI - Größte Zahl von Lösungsiterationen
