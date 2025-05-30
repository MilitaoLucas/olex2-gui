# Olex2 GUI Details and Workflows

This document provides an overview of key UI elements and inferred workflows in Olex2, based on analysis of its HTML and command documentation. Direct GUI interaction was not available for this analysis.

## Home Tab

### Start (from `gui\start.htm`)

Contains UI elements for Olex2 functionality.

### Multiple Dataset (from `gui\multiple-dataset.htm`)

Includes script interactions for: 'gui.home.multiple_dataset.generateHtml' script call.

### Tutorials (from `BaseDir()\util\pyUtil\gui\help\tutorials.htm`)

Path (`util/pyUtil/gui/help/tutorials.htm`) may point outside standard `etc/gui/` structure. Analysis of this block requires direct access to its content.

### Extension Modules (from `gui\extension-modules.htm`)

Includes script interactions for: 'plugins.gui.getInfo' script call.

### H2 Settings (from `gui\settings.htm`)

Contains UI elements for Olex2 functionality.

### Starter (from `gui\starter.htm`)

Contains UI elements for Olex2 functionality.

### Recent Files (from `gui\recent-files.htm`)

Contains UI elements for Olex2 functionality.

### News (from `news\news.htm`)

Content for block `news\news.htm` (normalized to `news/news.htm`) could not be reliably located in the `etc/gui/` manifest.

## Work Tab

### Main Toolbar (from `gui\main-toolbar.htm`)

Contains a table with columns like: $spy.MakeHoverButton('btn-solve','solve')    #include cbtn-solve gui\blocks\cbtn-on.htm;gui\blocks\cbtn-off.htm;image=solve;ondown=;1;, $spy.MakeHoverButton('btn-solve','solve'), #include cbtn-solve gui\blocks\cbtn-on.htm;gui\blocks\cbtn-off.htm;image=solve;ondown=;1;...

Includes script interactions for: 'btn-solve' button/action, 'btn-refine' button/action, 'btn-draw' button/action.

### Toolbox Work (from `gui\toolbox-work.htm`)

Includes script interactions for: 'toolbar-QC' button/action, 'toolbar-QH' button/action, 'toolbar-tidy' button/action.

### History (from `gui\history.htm`)

Contains a table with columns like: $+ html.Snippet(GetVar(default_link), "value=Reload .ins", "onclick=reap FilePath()/FileName().ins", ) $- $+ html.Snippet(GetVar(default_link), "value=Create Branch", "onclick=spy.gui.create_history_branch(true)", ) $- $+ html.Snippet(GetVar(default_link), "value=Create Snapshot", "onclick=spy.gui.create_history_branch(false)", ) $-...

Includes script interactions for: 'make_history_bars' script call.

### Select (from `gui\select.htm`)

Includes script interactions for: 'MakeElementButtonsFromFormula' script call, 'small-Select@uiso' button/action.

### Naming (from `gui\naming.htm`)

Contains a table with columns like: %Start%, $+ html.Snippet("gui/snippets/input-text", "name=naming*start", "width=35", "manage=true") $-, %Suffix%...

Contains input fields like: MATCH_NAME_SUFFIX.

Includes script interactions for: 'small-Name' button/action.

### Sorting (from `gui\sorting.htm`)

Contains a table with columns like: Atoms, $+ html.Snippet("gui/snippets/input-text", "name=sort_atom_order", "width=100%", "value=GetVar('sorting.atom_order', '')", "onchange=SetVar('sorting.atom_order', html.GetValue('~name~'))") $-, $+ html.Snippet("gui/snippets/input-checkbox", "name=atom_sequence_inplace", "value=Reorder ", "right=true", "manage=true", "onclick=html.SetState('atom_sequence_first','false')") $-...

Includes script interactions for: 'small-Sort' button/action.

## View Tab

### Quick Drawing Styles (from `gui\quick-drawing-styles.htm`)

Contains UI elements for Olex2 functionality.

### Symmetry Generation (from `gui\symmetry-generation.htm`)

Contains UI elements for Olex2 functionality.

### Select (from `gui\select.htm`)

Includes script interactions for: 'MakeElementButtonsFromFormula' script call, 'small-Select@uiso' button/action.

### Show (from `gui\show.htm`)

Contains UI elements for Olex2 functionality.

### Geometry (from `gui\geometry.htm`)

Contains UI elements for Olex2 functionality.

### Rotate (from `gui\rotate.htm`)

Includes script interactions for: 'tiny-:x' button/action, 'tiny-x:' button/action, 'tiny-:y' button/action.

### Stereo View (from `gui\stereo-view.htm`)

Includes script interactions for: 'two-Stereo_(Colour' button/action, 'two-Stereo_(Anaglyph' button/action, 'two-Stereo_(Hardware' button/action.

## Tools Tab

### Twinning (from `gui\twinning.htm`)

Key actions/buttons: Spherical, Angle-Axis.

Includes script interactions for: 'tools.get_twin_law_from_hklf5' script call, 'twin.init_twin_gui' script call.

### Images (from `gui\images.htm`)

Contains UI elements for Olex2 functionality.

### Maps (from `gui\maps.htm`)

Includes script interactions for: 'gui.maps.SetXgridView' script call.

### Chemical Tools (from `gui\chemical-tools.htm`)

Contains UI elements for Olex2 functionality.

### Olex2 Constraints Restraints (from `gui\OLEX2-conres.htm`)

Contains UI elements for Olex2 functionality.

### Shelx Compatible Constraints (from `gui\SHELX-compatible-constraints.htm`)

Contains UI elements for Olex2 functionality.

### Shelx Compatible Restraints (from `gui\SHELX-compatible-restraints.htm`)

Contains UI elements for Olex2 functionality.

### Hydrogen Atoms (from `gui\hydrogen-atoms.htm`)

Contains a table with columns like: **sp2:**, $spy.MakeHoverButton('toolbar-sp2_1H','mode hfix 43') $spy.MakeHoverButton('toolbar-sp2_2H','mode hfix 93'), **sp3:**...

Contains input fields like: HFIX, HFIX_D.

Includes script interactions for: 'toolbar-sp2_1H' button/action, 'toolbar-sp2_2H' button/action, 'toolbar-sp3_1H' button/action.

### Disorder (from `gui\disorder.htm`)

Contains UI elements for Olex2 functionality.

### Overlay (from `gui\overlay.htm`)

Includes script interactions for: 'gui.create_overlay_gui' script call.

### Cctbx (from `gui\cctbx.htm`)

Contains UI elements for Olex2 functionality.

### Space Groups (from `gui\space-groups.htm`)

Contains a table with columns like: Centrosymmetric, Non-Centrosymmetric...

Contains input fields like: formula.

### Bruker Saint (from `gui\bruker-saint.htm`)

Content for block `gui\bruker-saint.htm` (normalized to `gui/bruker-saint.htm`) could not be reliably located in the `etc/gui/` manifest.

### Batch (from `gui\batch.htm`)

Contains input fields like: SET_BATCH_DIR.

### Refinement (from `gui\refinement.htm`)

Contains UI elements for Olex2 functionality.

### Solve (from `gui\solve.htm`)

DELETE?  #include tool-top gui\blocks\tool-top.htm;image=#image;onclick=#onclick;1;     #includeif fs.Exists(solution_image.htm) solution_image 'solution_image.htm';1;   #include tool-table-header gui\blocks\tool-table-header.htm;1;   #include soluti...

### Folder View (from `gui\tools\folder-view.htm`)

Key actions/buttons: Select a folder.

Includes script interactions for: 'gui.tools.folder_view.generateHtml' script call.

### Platon (from `gui\tools\platon.htm`)

Contains UI elements for Olex2 functionality.

### Cds Search (from `gui\cds-search.htm`)

Contains a table with columns like: a, b...

Contains input fields like: cell_A, cell_B, cell_C.

## Info Tab

### Recent Files (from `gui\recent-files.htm`)

Contains UI elements for Olex2 functionality.

### Anomalous Dispersion (from `gui\anom-disp.htm`)

Includes script interactions for: 'disp.make_DISP_Table' script call.

### Autochem (from `spy.GetParam(odac.source_dir)\autochem.htm`)

Content for block `spy.GetParam(odac.source_dir)\autochem.htm` (normalized to `spy.GetParam(odac.source_dir)/autochem.htm`) could not be reliably located in the `etc/gui/` manifest.

### Difference Map Peaks (from `gui\electron-density-peaks.htm`)

Contains UI elements for Olex2 functionality.

### Refinement Indicators (from `gui\refinement-indicators.htm`)

Contains UI elements for Olex2 functionality.

### Bad Reflections (from `gui\bad-reflections.htm`)

Contains input fields like: exclude_h, exclude_k, exclude_l.

### Diagnostics (from `gui\diagnostics.htm`)

Contains UI elements for Olex2 functionality.

### Reflection Statistics (from `gui\reflection-statistics.htm`)

Includes script interactions for: 'makeReflectionGraphGui' script call.

### Reflection Statistics Summary (from `gui\reflection-statistics-summary.htm`)

Contains UI elements for Olex2 functionality.
