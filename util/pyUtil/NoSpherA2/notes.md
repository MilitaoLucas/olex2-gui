NoSpherA2_refine_interface.htm
- This should be changed here for disabled when I implement the option in olex2
<td width="2%" align="left">
  $+
    html.Snippet("gui/snippets/input-checkbox-td",
    "name=NoSpherA2_ORCA_Relativistics@refine",
    "label=Relativistics",
    "bgcolor=GetVar(HtmlTableFirstcolColour)",
    "disabled=spy.GetParam('snum.NoSpherA2.DisableRelativistic')"
    "checked=spy.GetParam('snum.NoSpherA2.Relativistic')",
    "oncheck=spy.SetParam('snum.NoSpherA2.Relativistic','True')",
    "onuncheck=spy.SetParam('snum.NoSpherA2.Relativistic','False')"
    )
  $-
