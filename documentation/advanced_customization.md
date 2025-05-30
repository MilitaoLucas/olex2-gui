# Advanced Customization in Olex2

This document provides an overview of advanced customization options available in Olex2, including scripting with Python and macros, changing default external programs, modifying GUI appearance, and integrating external crystallographic software.

## Scripting and Macros

Olex2 offers powerful scripting capabilities through Python and a macro system, allowing users to automate tasks, add new functionalities, and extend the software's core features.

### Python Scripting

*   **Core Functionality**: Olex2 has a deeply integrated Python interpreter, enabling scripts to interact with its crystallographic data, GUI elements, and core functions.
*   **Running Scripts**: Python scripts can be executed within Olex2. A common method mentioned in the `Commands.html` documentation (in the context of HKL file operations for HKLF5) is using the command:
    ```
    @py -l
    ```
    This command typically opens a file dialog to select a Python script, which is then loaded and executed. Scripts can also be run directly by providing their path.
*   **Example Scripts (`etc/scripts/`)**: The `etc/scripts/` directory contains a variety of example Python scripts that demonstrate how to extend Olex2. These include:
    *   `LazyOlex.py`: Likely provides utility functions or shortcuts for common tasks.
    *   `Olex2vmd.py`: Suggests integration or interface with VMD (Visual Molecular Dynamics).
    *   `example.py`: A generic example script for users to learn from.
    *   `hklf5.py`: A script for advanced HKL file processing, specifically creating HKLF 5 format files.
    *   `Olex2CCDC.py`: Likely for interactions with the Cambridge Crystallographic Data Centre (CCDC).
    *   `OlexPlaton.py`: May provide enhanced integration with the PLATON software.
    *   Many others like `OlexBET.py`, `XPlain.py`, `datasplit.py` suggest various specialized tools and utilities.
*   **Capabilities**: Python scripts can define new functions and register them as Olex2 commands, interact with and modify crystallographic data, create custom GUI elements, and automate complex workflows. The `util/pyUtil/PluginLib/` directory further details how Python is used for a structured plugin system.

### Macros

*   **Purpose**: The "About Macros and Scripting in Olex2" section in `Commands.html` indicates that Olex2 supports two types of external scripting: Macros and Python scripts. While Python is more powerful, macros likely offer a simpler way to automate sequences of Olex2 commands.
*   **`macro.xld`**: This file (likely in `etc/`) is probably used to define and store user or system macros.

## Customizing Olex2

Olex2 provides several ways to customize the user environment, from default external programs to the look and feel of the GUI.

### Default Programs

The "Change default programs" section in `Commands.html` explains how to modify the default applications Olex2 uses for tasks like opening text files, HTML files, or browsing folders.

*   **Method**: This is done by setting Olex2 variables associated with these programs.
*   **Persistent Changes**: To make these changes permanent, users can create or edit a file named `custom.xld` in their Olex2 installation or user directory.
*   **Example (`custom.xld` for KDE)**:
    ```xml
    <user_onstartup help="Executes on program start">
      <body <args>>
        <cmd>
          <cmd1 "setvar(defeditor,'kate')">
          <cmd2 "setvar(defexplorer,'konqueror')">
          <cmd3 "setvar(defbrowser,'konqueror')">
        </cmd>
      </body>
    </user_onstartup>
    ```
    This XML snippet defines a function that runs on startup, setting Kate as the default editor and Konqueror as the default file explorer and web browser. Users can adapt this for their preferred applications.

### GUI Appearance

The visual style of the Olex2 GUI is highly customizable.

*   **`gui.params`**: As detailed in `gui_overview.md`, this central file controls a vast number of parameters related to the GUI's appearance, including colors for different elements, font types, font sizes, and the dimensions of UI components.
*   **Skins (`etc/skins/`)**: Olex2 supports theming or "skins." The `etc/skins/` directory contains `.phil` files, each likely defining a distinct visual theme. Users can potentially switch between these skins or create their own by modifying these PHIL files.
*   **3D View Styles (`etc/styles/`)**: The appearance of the 3D crystallographic viewer can also be customized. The `etc/styles/` directory contains:
    *   `.glsp` files: Likely "OpenGL Style Preset" files.
    *   `.glds` files: Likely "OpenGL Style Definition" files.
    These allow users to save and load different visual representations for the molecular display (e.g., atom styles, colors, bond styles).

### External Program Integration

Olex2 is designed to work with several external crystallographic programs, enhancing its capabilities. The "External Programs" section in the Appendix of `Commands.html` highlights this:

*   **SHELX**: Seamless integration with the SHELX suite (ShelXS, ShelXL, ShelXM) for structure solution and refinement. Olex2 can often use these programs directly if they are on the system path.
*   **PLATON**: Interface provided for PLATON, a multipurpose crystallographic tool.
*   **SuperFlip**: Interface provided for SuperFlip, a program for structure solution from diffraction data using charge flipping.

These integrations allow users to leverage the strengths of these specialized programs from within the Olex2 environment.

By utilizing scripting, macros, configuration files, and understanding its integration with external tools, users can significantly tailor Olex2 to their specific needs and workflows.
