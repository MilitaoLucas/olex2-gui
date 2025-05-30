# Overview of Python Utilities in `util/pyUtil/`

This document provides a high-level overview of the `util/pyUtil/` directory, outlining the likely purpose of its subdirectories and key Python files. This directory appears to house core Python utilities, helper functions, specialized libraries, and modules that support the Olex2 application's functionality, GUI interactions, and development processes.

## Subdirectory Breakdown

The `util/pyUtil/` directory is organized into several key subdirectories, each with a probable specialized role:

### `CctbxLib`

*   **Likely Role**: This subdirectory seems dedicated to the integration of the Computational Crystallography Toolbox (CCTBX) with Olex2. CCTBX is a comprehensive library for crystallographic computations.
*   **Key Files Noted**:
    *   `cctbx_controller.py`: May act as a central manager or interface for CCTBX-related operations.
    *   `refinement.py`: Suggests functionality related to crystallographic refinement using CCTBX libraries.

### `NoSpherA2`

*   **Likely Role**: This directory likely contains modules related to "Non-Spherical Atom Refinement" (NoSpherA2), a technique used in crystallography to model electron density that isn't perfectly spherical around atoms. It could also be a specific tool or a set of tools for this purpose.
*   **Key Files Noted**:
    *   `NoSpherA2.py`: Possibly the main script or library for NoSpherA2 operations.
    *   `ELMO.py`: May refer to Electron Localizability MOrphology, a method often associated with non-spherical atom refinement, or a specific tool/library.

### `PluginLib`

*   **Likely Role**: This directory suggests a system for managing plugins and extending the core functionality of Olex2. It likely provides tools and a framework for developing and integrating external modules.
*   **Key Files Noted**:
    *   `PluginTools.py`: Probably contains helper functions and classes for plugin development and management.
    *   `plugin_skeleton.txt`: Likely a template or boilerplate file to help developers create new plugins.

### `PyToolLib`

*   **Likely Role**: This seems to be a library of general-purpose Python tools and utilities used across various parts of the Olex2 application.
*   **Key Files/Subdirectories Noted**:
    *   `FileReaders/`: A subdirectory indicating modules specifically for reading various file formats relevant to crystallography.
    *   `GuiTools.py`: Suggests helper functions or classes for GUI-related tasks, possibly bridging Python logic with the HTML/JavaScript frontend.
    *   `Report.py`: Likely involved in generating reports (e.g., refinement reports, CIF generation).
    *   `RunPrg.py`: Probably a utility for running external programs or scripts from within Olex2.

### `gui`

*   **Likely Role**: This subdirectory appears to contain Python modules that are specifically part of the Olex2 GUI backend or provide logic supporting the user interface.
*   **Key Files Noted**:
    *   `guiFunctions.py`: Likely a collection of functions used by the GUI for various operations and interactions.
    *   `htmlMaker.py`: Suggests utilities for dynamically generating HTML content for the GUI.

### `regression`

*   **Likely Role**: This directory is standard for housing software testing scripts and tools, specifically for regression testing to ensure new changes don't break existing functionality.
*   **Key Files Noted**:
    *   `run_tests.py`: A central script for executing the test suite.
    *   `testFileReaders.py`: Specific tests for the file reading utilities found in `PyToolLib/FileReaders/`.

## Key Individual Files in `util/pyUtil/`

Apart from the subdirectories, some Python files directly under `util/pyUtil/` may also provide important standalone functionalities:

*   **`olexFunctions.py`**: This file likely contains a collection of core functions specific to Olex2's operations, possibly covering a wide range of crystallographic calculations, data manipulations, or utility tasks frequently used by the application.
*   **`initpy.py`**: Files named `init.py` (or similar like `initpy.py`) in Python often handle initialization tasks for a package or a significant module, setting up necessary configurations, importing sub-modules, or defining widely used variables when this part of the Olex2 system is loaded.

This overview is based on directory and file naming conventions. A deeper analysis of each file's content would be required to fully detail its specific role and functionality.
