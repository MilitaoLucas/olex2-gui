[comment]: < Help for the moiety formula tool (Toolbox Work > Finishing). Compiled into the help index by gui/help/help_index.py. >

# Moiety Formula
The **moiety formula** (_chemical_formula_moiety) lists the chemically distinct units of the structure — molecules and ions — each with its charge, as the IUCr asks for it in the CIF, e.g. *C12 H10 N2 O4, 2(Cl -)*.

This tool works it out from the model: it splits the structure into fragments, infers a charge for each one and checks that the charges balance.

## Working
The table lists every fragment:

- **n** — how many times the fragment occurs
- **Formula** — the fragment's formula (a partial occupancy is shown in brackets)
- **Total** — n × charge
- **Charge** — the charge of one fragment, editable (see below)
- **Confidence** — where the charge came from

Below the table, the **balance equation** adds up the charges; for a sensible formula the total is 0.

## Confidence
- **lookup** — a known ion or molecule (built-in table)
- **user lookup** — a charge you entered for this formula earlier (see *Your own charges*)
- **user** — a charge you entered for this structure
- **balance** — the only unknown charge, worked out so that everything adds up to 0
- **element** / **ambiguous!** — a lone element (often a metal) with its most common oxidation state; *ambiguous* means other states are common too — check it
- **assumed neutral** — no metal or ion in the structure, so the fragment is taken as neutral
- **SUSPECT** — balance gives a charge that is chemically unlikely for this fragment; usually a metal's oxidation state is wrong
- **???** — no charge could be worked out: enter it yourself

## Editing charges
Every charge is an input box. Type a charge — **2+**, **+2**, **2-**, **-1** or **0** — and press **Enter** or leave the box: the fragment's confidence becomes *user* and the balance, the suggested formulae and **Apply to CIF** are updated. If one unknown charge is left, it is worked out from the balance.

Type **?** (or clear the box) to go back to the inferred charge. **Clear user-supplied charges** (below the table) undoes all charges entered for this structure.

## Your own charges
Charges you enter for multi-atom fragments are remembered in the file *user_charges.csv* (in DataDir()/gui/moiety) and used again for the same formula in later structures, shown as **user lookup**. Single elements are never remembered — a metal's oxidation state belongs to one structure, not to the element. Typing **?** for a *user lookup* charge removes it from the file.

## Suggested moiety formulae
The drop-down offers:

- **Best guess** — the charges in the table, with mixed valence if that is what balances
- **All n× M as +q** — every ambiguous metal in one oxidation state
- **No charges** — the formula as it stands, without charges

**Apply to CIF** writes the selected formula to _chemical_formula_moiety. Contents of masked solvent regions (from the solvent mask or SQUEEZE) are included in the formula when they could be identified.
