# Overview of File Formats in Olex2

This document provides an overview of common file extensions and formats used within the Olex2 crystallographic software package. The information is based on observed file listings and references in documentation like `Commands.html`.

## Common File Extensions

Olex2 utilizes a variety of file extensions. Some of the most commonly encountered include:

*   `.cif` (Crystallographic Information File)
*   `.hkl` (Reflection Data File)
*   `.ins` (ShelX Instruction File)
*   `.res` (ShelX Result File)
*   `.xld` (Olex2 Data/Definition File)
*   `.phil` (PHIL Configuration File)
*   `.def` (Definition File)
*   `.dat` (Data File)
*   `.txt` (Text File, often for definitions or skeletons)
*   `.html`, `.htm` (HTML for GUI components)
*   `.css` (CSS for styling GUI components)
*   `.py` (Python Scripts for core functions, plugins, utilities)
*   `.bat` (Windows Batch Files for automation)
*   `.sh` (Shell Scripts for Linux/macOS automation - presence inferred as common practice)
*   `.png` (Portable Network Graphics for images/icons)
*   `.glsp` (Olex2 Graphics Style Preset - likely)
*   `.glds` (Olex2 Graphics Style Definition - likely)

## Description of Known/Inferable Formats

### Crystallographic Data and Standards

*   **`.cif` (Crystallographic Information File)**:
    *   **Purpose**: The standard format for storing and exchanging crystallographic information, as defined by the International Union of Crystallography (IUCr). Contains structural data, experimental details, and associated metadata.
    *   **Locations**: Found in various places, including example directories like `etc/CIF/` and site-specific configurations in `etc/site/`.
*   **`.hkl` (Reflection Data File)**:
    *   **Purpose**: Stores reflection data from diffraction experiments, typically including h, k, l indices, intensities (or F/Fsq values), and their standard deviations.
    *   **Reference**: The "HKL file Operations" section in `Commands.html` details how Olex2 interacts with these files (e.g., `hklstat`, `omit`, `edithkl`).
*   **`.ins` (ShelX Instruction File)**:
    *   **Purpose**: An input file for the ShelX suite of crystallographic programs (e.g., ShelXL, ShelXS). It contains instructions for structure solution and refinement, including atom coordinates, symmetry operations, and refinement parameters.
    *   **Reference**: `Commands.html` mentions that "all commands of the ShelXL and ShelXS syntax are interpreted by Olex2... a shelx.ins file is generated on the fly if ShelXL/XH is chosen for the refinement."
*   **`.res` (ShelX Result File)**:
    *   **Purpose**: The primary output file from ShelX programs, containing the results of structure solution or refinement, including updated atomic coordinates, displacement parameters, and goodness-of-fit indicators.
    *   **Reference**: `Commands.html` implies interaction with `.res` files as part of the ShelX workflow integrated into Olex2.

### Olex2 Specific Configuration and Data

*   **`.xld` (Olex2 Data/Definition File)**:
    *   **Purpose**: Appears to be an Olex2-specific format, likely XML-based, used for storing various data, definitions, or configurations.
    *   **Examples**: `custom.xld` (user customizations), `macro.xld` (macros), `symmlib.xld` (symmetry library), `plugins.xld` (plugin registration).
*   **`.phil` (PHIL Configuration File)**:
    *   **Purpose**: Configuration files, likely using the Python-based Hierarchical Configuration (PHIL) format. This format is notably used by the Computational Crystallography Toolbox (CCTBX) and allows for structured, human-readable parameter settings.
    *   **Examples**: `gui.params` (main GUI settings), `params.phil` (general parameters), `metacif.phil`, and various files in `etc/skins/` defining UI themes.
*   **`.def` (Definition File)**:
    *   **Purpose**: Text files used for various definitions, often site-specific or for templates.
    *   **Examples**: `etc/site/archive.def` (archiving parameters), `etc/site/cif_info.def` (CIF output customization), `def.txt` within plugin directories (plugin metadata).

### General Data and Scripts

*   **`.dat` (Data File)**:
    *   **Purpose**: General-purpose data files. Their specific content depends on the context.
    *   **Examples**: `ptablex.dat` (likely periodic table information), `etc/CIF/cifindex.dat` (possibly an index for the CIF dictionary).
*   **`.py` (Python Scripts)**:
    *   **Purpose**: Used extensively throughout Olex2 for core functionality, utility scripts, GUI backend logic, and plugins (as seen in `util/pyUtil/`).
*   **`.bat` (Windows Batch Files)**:
    *   **Purpose**: Windows-specific scripts for automating tasks or running sequences of commands.
    *   **Examples**: `olx-solve.bat`, `olx-refine.bat` (likely for initiating solving and refinement processes).
*   **`.sh` (Shell Scripts)**:
    *   **Purpose**: Shell scripts for Linux/macOS environments, for similar automation tasks as `.bat` files. (Presence inferred).

### GUI, Styling, and Image Files

*   **`.html`, `.htm` (HTML Files)**:
    *   **Purpose**: Used to define the structure and layout of Olex2's Graphical User Interface components, as seen in `etc/gui/` and its subdirectories.
*   **`.css` (Cascading Style Sheets)**:
    *   **Purpose**: Used for styling the HTML-based GUI elements.
*   **`.glsp`, `.glds` (Olex2 Graphics Files)**:
    *   **Purpose**: These are likely Olex2-specific formats related to 3D graphics styles and scenes. Files with these extensions are found in `etc/styles/`. `.glsp` could mean "OpenGL Style Preset" and `.glds` "OpenGL Style Definition".
*   **`.png` (Portable Network Graphics)**:
    *   **Purpose**: Image files used for icons, logos, buttons, and other graphical assets in the GUI (e.g., in `etc/gui/images/`).

## Conventions and Directory Structures

The layout of files within the `etc/` directory and its subdirectories suggests certain conventions:

*   **`etc/CIF/`**: Contains core CIF dictionary files and templates (`cif_templates/`).
*   **`etc/ED/`**: Likely related to electron diffraction (e.g., `EDpatterns.def`).
*   **`etc/gui/`**: Contains the HTML, CSS, and image files that make up the user interface, with `blocks/` and `tools/` subdirectories for modular components.
*   **`etc/help/`**: Contains HTML-based help files.
*   **`etc/site/`**: Appears to be for site-specific configurations, overrides, or local definitions (e.g., `archive.def`, `cif_info.def`, `custom.xld`).
*   **`etc/skins/`**: Contains PHIL files that define different visual themes (skins) for the GUI.
*   **`etc/styles/`**: Stores graphics style files (`.glsp`, `.glds`).
*   **`util/pyUtil/PluginLib/plugin-NAME/`**: The standard directory structure for individual plugins, usually containing a `.py` script, a `.phil` config file, an `.htm` GUI file, and a `def.txt` metadata file.

Understanding these file formats and conventions is key to comprehending how Olex2 is structured, configured, and extended.
