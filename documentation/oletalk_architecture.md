```markdown
# Olex2 Client-Server Architecture and Component Roles

This document outlines the client-server architecture involving `controller.py` and the Olex2 system, detailing the roles of various components and how commands are processed.

## 1. Overview of the Client-Server Architecture

The system operates on a client-server model:

*   **Client:** `controller.py` acts as the client application. It provides a high-level interface for users or automated scripts to interact with Olex2.
*   **Server:** The Olex2 application (likely `olex2.exe`) functions as the server. It is the core crystallographic software that performs calculations, manages data, and exposes an interface for remote control.

Communication between the client and server typically occurs over a network connection (e.g., TCP/IP on a specific port), allowing `controller.py` to send commands and receive results from the Olex2 server, even if Olex2 is running as a separate process or on a different machine (though often on the same machine).

## 2. Component Roles

Several key files and components work together in this architecture:

*   **`controller.py` (Client Application):**
    *   **Role:** Primary user-facing script or module for controlling Olex2 operations externally.
    *   **Functionality:**
        *   Establishes a connection to the Olex2 server.
        *   Sends commands (as strings) to the Olex2 server to perform specific actions (e.g., load data, run refinement, solve structure).
        *   Receives responses, data, and status messages from the Olex2 server.
        *   May parse server output to make decisions or present results.
        *   Can orchestrate complex workflows by sending sequences of commands.
        *   Potentially capable of executing batch scripts like `olx-refine.bat` and `olx-solve.bat` or sending their constituent commands directly to the server.

*   **Olex2 Server (typically `olex2.exe`):**
    *   **Role:** The core crystallographic software package that processes commands and manages crystallographic data.
    *   **Functionality:**
        *   Listens for incoming connections from clients like `controller.py`.
        *   Parses and executes commands received from the client.
        *   Performs crystallographic calculations (e.g., structure solution, refinement, analysis).
        *   Manages the state of the crystallographic model.
        *   May provide its own scripting environment (often Python-based, see `olex2-from-server.py`).
        *   Sends results, logs, and error messages back to the connected client.

*   **`olex2.dll` (Dynamic Link Library):**
    *   **Role:** A core library providing essential functionalities for the Olex2 ecosystem.
    *   **Functionality:**
        *   Likely contains fundamental algorithms, functions for data manipulation, and potentially the API endpoints that the Olex2 server uses to expose its capabilities.
        *   It could be used by `olex2.exe` to perform its tasks.
        *   It might also be involved in the communication layer, helping the server to listen for and handle client requests, or providing functions that client-side libraries (if any) could use for lower-level interaction (though `controller.py` seems to use a higher-level command interface).

*   **`olex2-from-server.py` (Server-Side Python Script):**
    *   **Role:** A Python script that is likely executed *by* the Olex2 server itself.
    *   **Functionality:**
        *   Olex2 often includes an embedded Python interpreter or the ability to call external Python scripts. This allows users to extend Olex2's capabilities.
        *   `olex2-from-server.py` could be triggered by specific commands sent from `controller.py` or by internal Olex2 events.
        *   It would run within the Olex2 server's environment (or a child process spawned by it), having access to Olex2's internal data structures and APIs.
        *   Used for tasks that are more conveniently scripted in Python on the server side, potentially interacting with the loaded crystal structure data directly.

*   **`olx-refine.bat` (Batch Script):**
    *   **Role:** A Windows batch script designed to automate a sequence of Olex2 commands specifically for structure refinement.
    *   **Functionality:**
        *   Contains a series of commands that would otherwise be typed into Olex2's console or sent individually by a client.
        *   Provides a way to execute a standard refinement procedure.
        *   `controller.py` might execute this batch file directly (if running on the same Windows machine) or, more likely, read the commands from it and send them sequentially to the Olex2 server.

*   **`olx-solve.bat` (Batch Script):**
    *   **Role:** Similar to `olx-refine.bat`, but tailored for automating structure solution procedures in Olex2.
    *   **Functionality:**
        *   Contains a sequence of Olex2 commands for structure solution.
        *   `controller.py` can interact with this script in the same ways as with `olx-refine.bat`.

## 3. Command Sending and Processing

The typical flow of commands and their processing is as follows:

1.  **Connection:** `controller.py` initiates a network connection to the Olex2 server listening on a pre-configured host and port.
2.  **Command Formulation:** `controller.py` formulates a command string. This could be a simple Olex2 command (e.g., `Refine`) or a more complex instruction that `controller.py` translates into one or more Olex2 server commands.
3.  **Command Transmission:** The command string is sent over the network socket to the Olex2 server.
4.  **Server-Side Reception and Parsing:** The Olex2 server receives the command string. It parses the string to understand the requested action and its parameters.
5.  **Execution:**
    *   The Olex2 server executes the command. This might involve:
        *   Calling internal functions (potentially residing in `olex2.dll`).
        *   Modifying the current crystallographic data.
        *   Performing calculations.
        *   If the command is intended to run a server-side script, it might trigger the execution of a script like `olex2-from-server.py`.
    *   If `controller.py` invokes a batch file like `olx-refine.bat` or `olx-solve.bat`:
        *   **Direct Execution:** `controller.py` might use OS commands to run the batch file. The batch file itself would then interact with Olex2 (either via its command line interface if Olex2 is launched by the batch script, or by sending commands to an already running Olex2 instance if the batch script uses a separate client utility).
        *   **Indirect Execution:** More commonly for robust client-server interaction, `controller.py` would parse the relevant commands from the `.bat` file and send them one by one (or in a suitable sequence) to the Olex2 server over the established connection.
6.  **Response Generation:** After processing the command, the Olex2 server generates a response. This could be a simple acknowledgment, data output, status messages, or error codes.
7.  **Response Transmission:** The response is sent back to `controller.py` over the network connection.
8.  **Client-Side Processing:** `controller.py` receives the response, parses it, and takes appropriate action (e.g., displaying results, logging, proceeding to the next step in a workflow).
9.  **Connection Termination:** The connection might be kept alive for multiple commands or closed after each interaction, depending on the design of `controller.py` and the Olex2 server's capabilities.

This architecture allows for flexible and automatable control of Olex2's powerful crystallographic functionalities from an external Python environment.
```
