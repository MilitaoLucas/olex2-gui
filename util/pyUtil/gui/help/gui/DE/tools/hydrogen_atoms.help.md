# HFIX Quickmodes
Dieser Bereich enthält gängige Constraints für das Setzen von Wasserstoffatomen. Steht die Maus über einem der kleinen Symbole, erscheint der SHELX-Constraint, der auf die ausgewählten Atome angewendet wird. Ein Klick auf ein Symbol startet einen Modus für genau diesen Constraint. Die Atome anklicken, auf die er angewendet werden soll, dann mit '<c>ESC</c>' den Modus beenden. Man kann auch einfach nach Auswahl eines Atoms den Code des Constraints eintippen.


# Toolbar Hydrogen_2
Hier lassen sich H-Atome mit eigenen X-H-Bindungslängen hinzufügen.

## A, D und HFIX
Den gewünschten AFIX-Code in das Feld **A** und die gewünschte X-H-Bindungslänge (in &Aring;) in das Feld **D** eintragen und **HFIX** anklicken. Damit startet ein Modus, in dem dieser Constraint auf jedes angeklickte Atom angewendet wird (an den angeklickten Atomen werden Wasserstoffatome geometrisch gesetzt). '<c>ESC</c>' beendet den Modus.

## H 'Improve'
Diese Funktion stammt direkt aus der Syntax des Kristallographie-Grafikprogramms XP. Die Abstände im Auswahlmenü **HIMP** sind typische X-H-Bindungslängen aus der Neutronenbeugung. Die Wahl eines Abstands startet einen Modus, in dem X-H-Bindungen diese Länge erhalten. Alternativ startet auch ein in das Feld **HIMP** eingegebener Wert mit '<c> TAB</c>' den Modus. In diesem Modus verschiebt ein Klick auf ein Wasserstoffatom dieses entlang seiner X-H-Bindung auf den im Feld **HIMP** angegebenen Abstand.

| `himp 0.983` | Setzt alle X-H-Bindungen der Struktur auf 0.983 &Aring;. |


# Toolbar Hydrogen_3
## Wasserstoff hinzufügen
Dieser Link setzt Wasserstoffatome in der ganzen Struktur geometrisch und belegt sie je nach Umgebung (sp<sup>2</sup>, sp<sup>3</sup> usw.) mit Constraints. Um Wasserstoffpositionen frei zu verfeinern, die Atome auswählen, an die die Wasserstoffatome gebunden sind, '<c> AFIX 0</c>' eingeben und erneut verfeinern.

## H-Atomnamen
Zeigt die Namen aller Atome, auch der Wasserstoffatome.

| `labels -h -l` | Zeigt alle Atomnamen einschließlich der Wasserstoffatome. |

## Keine H-Atomnamen
Zeigt die Namen aller Nicht-Wasserstoffatome.

| `labels -l` | Zeigt alle Namen der Nicht-Wasserstoffatome. |

## AFIX anzeigen
Zeigt den *AFIX*-Code (falls vorhanden) an jedem Wasserstoffatom der Struktur.

| `labels -h -a` | Zeigt den *AFIX*-Constraint-Code jedes Wasserstoffatoms der Struktur. |

## ALLE H FREIGEBEN
Entfernt alle *AFIX*-Constraints von allen Wasserstoffatomen und gibt auch ihre Uiso-Werte frei, sodass sie frei verfeinert werden können.

## Q ausblenden
Blendet alle Elektronendichte-Peaks (Q-Peaks) auf dem Bildschirm aus.


# HTAB Slider
Die Anweisung '<c>htab</c>' analysiert die Wasserstoffbrücken der Struktur. Sie funktioniert nur, wenn allein die asymmetrische Einheit auf dem Bildschirm ist; Wasserstoffbrücken zu symmetrieäquivalenten Atomen werden trotzdem gezeigt. Die Liste der Wasserstoffbrücken, die die Kriterien der Regler unten erfüllen, erscheint im Grafikfenster.

## Abstand
Dieser Regler legt den größten D-A-Abstand (in &Aring;) fest, bis zu dem eine Wechselwirkung D-H&middot;&middot;&middot;A als Wasserstoffbrücke gilt.

## Winkel
Dieser Regler legt den kleinsten D-H-A-Winkel (in Grad) fest, ab dem eine Wechselwirkung D-H&middot;&middot;&middot;A als Wasserstoffbrücke gilt.


# Hydrogen Bond Slider
Diesen Regler nach rechts schieben, um einen Modus zu starten, der mögliche Wasserstoffbrücken bei immer größeren Abständen zeigt. Ein Klick auf eine der gestrichelten "Bindungen" an einem Atom zeigt den Teil der Struktur, mit dem dieses Atom eine Wasserstoffbrücke bildet. '<c>ESC</c>' beendet den Modus.
