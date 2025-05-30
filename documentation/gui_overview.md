# Olex2 GUI Overview: Structure and Configuration

This document provides a high-level understanding of how the Olex2 Graphical User Interface (GUI) is structured and configured, based on the `etc/index.htm` and `gui.params` files.

## 1. GUI Structure from `etc/index.htm`

The `etc/index.htm` file defines the main HTML skeleton and layout for the Olex2 interface.

### Main Layout

The GUI's primary structure is built using HTML tables. Key components observed include:

*   **Header/Logo Area**: A section at the top (`<table name="LOGO">`) dedicated to displaying the Olex2 logo and potentially other branding elements.
*   **Information Bar**: A section (`<table name="SNUM_INFO">`) likely used for displaying context-specific information, possibly related to the currently loaded structure or project.
*   **Main Tab Bar**: A prominent horizontal navigation bar (`<table name="TABS">`) that houses the primary sections of the GUI.
*   **Content Panes**: Below the tab bar, specific content areas are loaded dynamically based on the selected tab (e.g., `index-home`, `index-work`).

### Main Tabs

The GUI features a tab-based navigation system. The main tabs defined in `etc/index.htm` are:

*   **Home**: Likely the default landing page or a general overview section.
*   **Work**: This tab probably contains tools and options related to structure solution, refinement, and model manipulation.
*   **View**: Expected to house controls for customizing the 3D display of the crystallographic model, styles, and perspectives.
*   **Tools**: This section likely provides access to various crystallographic tools, calculations, and utilities.
*   **Info**: Probably displays information about the current structure, project history, help resources, or Olex2 itself.

### Templating Mechanism (`<!-- #include ... -->`)

Olex2's GUI heavily utilizes a server-side include-like templating mechanism. This is evident from comments such as:
`<!-- #include logo gui\blocks\logo.htm;1; -->`
`<!-- #includeif file.Exists(FileFull()) tab-home gui\blocks\tab-on.htm;gui\blocks\tab-off.htm;image=home;2; -->`

This mechanism allows for a modular GUI design:

*   **Reusable Blocks**: Common UI elements (like logos, tab buttons, content panes for each tab) are defined in separate HTML files located in the `etc/gui/blocks/` directory (e.g., `logo.htm`, `tab-on.htm`, `index-home.htm`).
*   **Dynamic Inclusion**: The main `index.htm` file includes these smaller HTML blocks to construct the final interface. Some inclusions are conditional (e.g., `<!-- #includeif file.Exists(FileFull()) ... -->`), allowing the GUI to adapt based on context or file existence.
*   **Parameters**: The include directives can also pass parameters (e.g., `image=home;2;`), which likely customize the included block, for instance, by specifying which icon to use for a tab.

This approach makes the GUI easier to manage and update by breaking it down into smaller, self-contained components.

## 2. GUI Configuration from `gui.params`

The `gui.params` file is a plain text file that defines a wide array of parameters controlling the appearance and some behavioral aspects of the Olex2 GUI. It uses a hierarchical key-value structure.

### Overview of Configuration

`gui.params` acts as a central theme or skin configuration file. It allows users or developers to customize:

*   **Colors**: Backgrounds, fonts, borders, highlights for various UI elements.
*   **Fonts**: Font faces and sizes for different text elements in the GUI.
*   **Sizes and Dimensions**: Widths, heights, padding, and other layout-related numbers for buttons, input fields, panels, etc.
*   **Specific Element Styling**: Detailed appearance properties for dynamically generated "text images" (timage) which are used for buttons, tabs, and headers, allowing for custom-rendered UI elements beyond standard HTML controls.

### Key Parameter Groups and Examples

Several key groups of parameters are evident:

*   **`gui.skin.*`**: Controls global skin properties.
    *   `base_width`: Defines a base width for the GUI.
    *   `clearcolor`: Background color for the main 3D display area.
    *   `icon_size`, `icon_border_colour`: Styles for icons.
    *   `button.highlight.lightness`, `button.border.lightness`: Appearance of buttons on interaction.
*   **`gui.html.*`**: Defines styles for standard HTML elements rendered within Olex2's embedded browser components.
    *   `bg_colour`, `font_colour`, `font_name`, `font_size`: Basic HTML page styling.
    *   `link_colour`: Color for hyperlinks.
    *   `table_bg_colour`, `table_row_bg_colour`: Styling for HTML tables.
    *   `input_bg_colour`, `input_height`: Appearance of input fields.
*   **`gui.timage.*`**: Configures "Text Images" – dynamically generated graphical UI elements. This is a powerful feature for creating custom-looking buttons and tabs.
    *   `timage.tab.*`: Parameters for main navigation tabs (colors, font, size, corner radius, arrows).
    *   `timage.button.*`, `timage.cbtn.*`, `timage.tinybutton.*`: Parameters for different types of buttons.
    *   `timage.h1.*`, `timage.h3.*`: Styling for header elements that are rendered as images.
*   **`gui.help.*`**: Parameters for the integrated help system.
    *   `src`: Path to help files.
    *   `bg_colour`, `font_colour`, `highlight_colour`: Appearance of the help browser.
*   **`gui.css.*`**: Defines styles for specific HTML header tags (h1, h2) and a "big" class, similar to CSS.
    *   `font_size`, `font_name`, `color`, `line_height`.
*   **Other groups**: `gui.notification` (for pop-up messages), `gui.xgrid` (for the 3D grid display), `gui.diagnostics` (colors for report grades), etc.

### Variables in HTML (`$GetVar(...)`)

The `etc/index.htm` file uses placeholders like `$GetVar(HtmlLinkColour)`. These are variables that Olex2's HTML rendering engine replaces at runtime with values defined in `gui.params`.

For example, in `etc/index.htm`:
`<body link="$GetVar(HtmlLinkColour)" bgcolor="$GetVar(HtmlBgColour)">`

This line uses the values of `gui.html.link_colour` and `gui.html.bg_colour` from `gui.params` to set the hyperlink color and background color of the HTML body, respectively.

## 3. Relationship between `etc/index.htm` and `gui.params`

The two files work in tandem to generate the final Olex2 GUI:

1.  **Structure (`etc/index.htm`)**: Provides the fundamental HTML layout, defining where different UI components (logo, tabs, content panes) are placed. It uses `#include` directives to build the interface modularly from smaller HTML blocks.
2.  **Styling and Configuration (`gui.params`)**: Contains a comprehensive set of parameters that dictate the visual appearance (colors, fonts, sizes, specific styles for custom-rendered elements) and some behavioral settings.
3.  **Dynamic Rendering**: When Olex2 starts or renders a GUI view, it parses `etc/index.htm`. The `$GetVar(variableName)` placeholders in the HTML are dynamically replaced with the corresponding values read from `gui.params`. This allows the static structure of `index.htm` to be themed and configured by the values in `gui.params` without altering the HTML code itself. The "text image" (`timage`) engine uses parameters from `gui.params` to generate custom graphical elements like buttons and tabs that are then displayed within the HTML structure.

In essence, `etc/index.htm` is the blueprint for the GUI's layout, while `gui.params` is the detailed specification sheet for its look and feel.
