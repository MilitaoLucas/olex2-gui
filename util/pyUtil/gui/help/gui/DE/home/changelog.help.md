---
title: "ChangeLog"
linkTitle: "ChangeLog"
weight: 4
description: "ChangeLog"
categories:
 - home
tags:
 - home
---


# ChangeLog

Dies ist ein größeres Update von Olex2. Die wichtigsten Änderungen sind unten beschrieben.

## Überarbeitetes Hilfesystem

Das Hilfesystem sieht anders aus als früher. Es ist auch viel vollständiger – wenn auch noch lange nicht so vollständig, wie wir es gern hätten.

Das gesamte Hilfesystem wird aus Markdown-Dateien erzeugt, die unter

URL[https://github.com/Olex2/help/tree/master/gui/EN, GITHUB]

zu finden sind und dort gut lesbar dargestellt werden. Damit kann jeder zu unserer Hilfe beitragen – bitten Sie uns um Schreibrechte, wir freuen uns über jeden Beitrag. Langfristig soll die Hilfe auch in anderen Sprachen erscheinen – wenn Sie bei einer Übersetzung helfen können, sagen Sie uns bitte Bescheid.

## NoSpherA2 ersetzt HARt

Das Team der Hirshfeld-Atom-Verfeinerung um **Simon Grabowsky**, **Dylan Jayatilaka** und Kollegen hat intensiv an diesem neuen Verfeinerungs-Tool gearbeitet. Für Verfeinerungen mit nicht-sphärischen Formfaktoren wurde es durch das leistungsfähigere NoSpherA2 (im Bereich Work) ersetzt. NoSpherA2 enthält weiterhin HARt für alle, die eine Hirshfeld-Atom-Verfeinerung durchführen möchten.

## EXTI

Manchmal muss die Extinktion verfeinert werden, manchmal nicht. Olex2 entscheidet das jetzt automatisch (EXTI wird verfeinert, wenn der Wert doppelt so groß ist wie seine Standardunsicherheit). Wird das Häkchen entfernt, wird EXTI **nicht** verfeinert; wird es *wieder gesetzt*, **wird** es verfeinert. Sie haben die Kontrolle!

## Keine \_publ\_*-Einträge mehr in der CIF

Nach vielen Gesprächen mit Verlagen, der IUCr und dem CCDC haben wir beschlossen, alle Einträge, die mit \_publ\_* beginnen, aus unseren CIF-Dateien zu entfernen. Sie wurden durch \_audit\_* ersetzt, denn jede Struktur ist eine eigenständige Arbeit, deren Autoren klar erkennbar und gewürdigt sein sollen, ganz gleich, wo die Struktur am Ende landet. Mehr dazu unter URL[https://www.iucr.org/\_\_data/iucr/cifdic\_html/1/cif\_core.dic/Caudit\_author.html, \_audit_author].
