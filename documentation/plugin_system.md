# Olex2 Plugin System Overview

This document describes the plugin system in Olex2, based on the files found in the `util/pyUtil/PluginLib/` directory. It aims to provide an understanding of how plugins extend Olex2's functionality and how new plugins can be developed.

## Overall Purpose of `PluginLib`

The `util/pyUtil/PluginLib/` directory provides the framework and tools necessary for creating, managing, and integrating plugins into the Olex2 environment. Plugins allow for the extension and customization of Olex2's capabilities, enabling users and developers to add new features, tools, or workflows.

## Key Components

Several files and a template play crucial roles in the Olex2 plugin architecture:

### 1. `PluginTools.py`

This file appears to provide the core infrastructure for plugins. It defines:
*   A base class `PluginTools` (which itself inherits from `VFSDependent`, suggesting interaction with Olex2's Virtual File System).
*   **Core Plugin Functionalities**:
    *   Initialization and setup (`__init__`).
    *   Loading and saving of plugin-specific configuration using PHIL files (`deal_with_phil`). PHIL files (`.phil`) are a common way in crystallographic software to handle parameters.
    *   GUI integration (`setup_gui`), which includes creating GUI images and adding the plugin's interface to the main Olex2 GUI tabs and tool indices.
    *   Version and date information handling (`get_plugin_date`, `print_version_date`).
    *   Management of customizable plugin resources (`edit_customisation_folder`, `get_customisation_path`).
*   **Plugin Creation Utility**: A significant function `make_new_plugin(name, overwrite=False)` is defined and registered with Olex2. This function automates the generation of a new plugin's file structure based on `plugin_skeleton.txt`.

### 2. `plugin_skeleton.txt`

This is a multi-part template file used by `make_new_plugin` to generate the basic files for a new plugin. It contains several sections, each defining a different component of a plugin:

*   **`t:plugin_skeleton_py@` (Python Script Template)**:
    *   Defines a Python class for the new plugin (e.g., `class MyPlugin(PluginTools):`).
    *   Includes imports for standard Olex2 libraries (`olexFunctions`, `olex`, `olx`, `gui`).
    *   Shows how to read a `def.txt` file for plugin metadata.
    *   Initializes plugin-specific attributes like name, path, scope, HTML file, and images.
    *   Calls `self.deal_with_phil(operation='read')` for configuration.
    *   Calls `self.setup_gui()` for GUI integration.
    *   Provides an example of how to register a plugin method as an Olex2 command using `OV.registerFunction(self.my_example_method, True, "MyPluginNamespace")`.
*   **`t:plugin_skeleton_phil@` (PHIL File Template)**:
    *   A template for the plugin's configuration file (e.g., `myplugin.phil`).
    *   Includes example parameters for specifying the plugin's location in the Olex2 GUI (e.g., which tab, and before which existing tool it should appear).
*   **`t:plugin_skeleton_html@` (HTML GUI Template)**:
    *   A basic HTML structure for the plugin's user interface.
    *   Uses Olex2's HTML templating system (e.g., `<!-- #include tool-top ... -->`) to incorporate standard GUI elements.
    *   Includes an example of how to link an HTML element to a Python function in the plugin (`<a href="spy.MyPlugin.my_example_method()">RUN</a>`).
*   **`t:plugin_h3_extras@` (HTML Extras Template)**:
    *   A template for an "Extras" section in the plugin's GUI, typically providing buttons for:
        *   Reloading the plugin.
        *   Accessing plugin-specific settings (via `spy.EditParams(plugin_scope)`).
        *   Opening the plugin's folder in the system's file explorer.
*   **`t:plugin_skeleton_def@` (`def.txt` Template)**:
    *   Defines the structure for `def.txt`, a metadata file for the plugin.
    *   Specifies keys for `p_name` (Plugin Name), `p_htm` (HTML file for GUI), `p_img` (images for GUI, often for H1 and H3 headers), and `p_scope` (the PHIL scope for parameters).

### 3. Example Plugins / Tools

*   **`plugin_batch_exex.py`**:
    *   This script provides a `BatchMatch` macro.
    *   It appears to automate the process of reading multiple crystallographic information files (CIFs) from a directory, performing symmetry matching (`olx.Match('-i')`), and then logging the RMS values from these matches to a CSV file and an HTML log.
    *   It demonstrates how a plugin can perform batch operations and interact with core Olex2 crystallographic functions.
*   **`plugin-cProfiler/spy_CProfile.py`**:
    *   This plugin provides a tool to profile Python code within Olex2 using Python's built-in `cProfile` module.
    *   It defines a `Spy` class that can wrap and run another tool/function to measure its performance.
    *   This is an example of a developer-focused plugin that aids in optimizing Olex2 scripts and other plugins.

## How to Develop Plugins (Inferred)

Based on the structure of `PluginTools.py` and `plugin_skeleton.txt`, the typical process for developing a new plugin in Olex2 likely involves these steps:

1.  **Scaffolding with `make_new_plugin`**:
    *   From within Olex2, execute the command `pt make_new_plugin MyPluginName` (assuming `pt` is the namespace for `PluginTools` registered functions).
    *   This will create a new directory named `plugin-MyPluginName` inside `util/pyUtil/PluginLib/`.
    *   This directory will be populated with the following files, generated from `plugin_skeleton.txt`:
        *   `MyPluginName.py` (the main Python code for the plugin)
        *   `mypluginname.phil` (configuration file)
        *   `mypluginname.htm` (HTML template for the GUI)
        *   `def.txt` (metadata definition file)
        *   `h3-MyPluginName-extras.htm` (HTML for an "Extras" section in the GUI)

2.  **Define Metadata (`def.txt`)**:
    *   Edit `def.txt` to set:
        *   `p_name`: The display name of the plugin.
        *   `p_htm`: The name of the HTML file for the plugin's GUI (usually `mypluginname.htm`).
        *   `p_img`: A list of tuples defining images and header types for the GUI (e.g., `[("MyPluginName",'h1'), ("MyPluginName-Extras",'h3')]`).
        *   `p_scope`: The scope name used for PHIL parameters (e.g., `mypluginname`).

3.  **Implement Core Logic (`MyPluginName.py`)**:
    *   Open the generated `MyPluginName.py`.
    *   The class `MyPluginName` will already inherit from `PluginTools.PluginTools`.
    *   Add new methods to this class to implement the plugin's functionality.
    *   Use `OV.registerFunction(self.my_method, is_for_gui=True/False, namespace="MyPluginCommandScope")` within the `__init__` method (or another appropriate place) to expose Python methods as commands callable from the Olex2 console or GUI.
    *   Access and store plugin-specific settings using the PHIL system via `self.params` (after `self.deal_with_phil('read')`).

4.  **Create/Edit GUI (`mypluginname.htm` and `h3-MyPluginName-extras.htm`)**:
    *   Modify `mypluginname.htm` to build the plugin's user interface using HTML.
    *   Olex2's HTML templating features (e.g., `#include` for standard blocks, `$spy` calls for dynamic content like buttons) can be used here.
    *   Links or buttons in the HTML can trigger Python functions registered via `OV.registerFunction` (e.g., `<a href="spy.MyPluginNamespace.my_method()">Run My Method</a>`).
    *   The `h3-MyPluginName-extras.htm` can be customized if needed.

5.  **Define Configuration (`mypluginname.phil`)**:
    *   Edit `mypluginname.phil` to add any custom parameters your plugin needs.
    *   Specify GUI integration details, such as:
        *   `gui.location`: The Olex2 tab where the plugin should appear (e.g., 'tools', 'work').
        *   `gui.before`: The name of an existing tool before which your plugin's GUI should be inserted.

6.  **Register Plugin with Olex2 (`plugins.xld`)**:
    *   The `make_new_plugin` function attempts to automatically add an entry for the new plugin to `etc/plugins.xld`. This XML file is likely used by Olex2 at startup to discover and load available plugins. The entry would be something like `<MyPluginName>`.

7.  **Restart Olex2**:
    *   After creating or modifying a plugin, a restart of Olex2 is typically required for the changes to take effect, particularly for new plugins to be loaded and registered.

This plugin system allows for a modular and extensible Olex2 environment, where new tools and functionalities can be added without modifying the core application code.
