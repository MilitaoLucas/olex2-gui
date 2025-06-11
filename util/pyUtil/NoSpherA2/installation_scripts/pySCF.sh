#!/bin/bash
set -e

# Check for -y flag for non-interactive installation
NONINTERACTIVE=false
if [[ "$1" == "-y" ]]; then
    NONINTERACTIVE=true
    echo "Running in non-interactive mode with default options"
fi

echo "pySCF Installation Script"
echo "=========================="
echo

# Function to prompt user for confirmation
confirm() {
    if [ "$NONINTERACTIVE" = true ]; then
        echo "$1 [Automatically confirmed with -y option]"
        return 0
    fi
    
    read -p "$1 [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            echo "Installation aborted by user."
            exit 1
            ;;
    esac
}

# Function to prompt user for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    
    if [ "$NONINTERACTIVE" = true ]; then
        echo "$prompt [$default] (Using default: $default)"
        echo "$default"
        return
    fi
    
    local response
    read -p "$prompt [$default]: " response
    echo "${response:-$default}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main confirmation to proceed with installation
confirm "This script will set up pySCF and its dependencies. Continue?"

# Ask for environment name
ENV_NAME=$(prompt_with_default "Enter name for conda environment" "pyscf")

# Initialize variables
CONDA_CMD=""
CONDA_FOUND=false

# Check for conda/mamba/micromamba
if command_exists conda; then
    CONDA_CMD="conda"
    CONDA_FOUND=true
    echo "Found conda installation."
elif command_exists mamba; then
    CONDA_CMD="mamba"
    CONDA_FOUND=true
    echo "Found mamba installation."
elif command_exists micromamba; then
    CONDA_CMD="micromamba"
    CONDA_FOUND=true
    echo "Found micromamba installation."
fi

# If no conda/mamba is found, install micromamba
if [ "$CONDA_FOUND" = false ]; then
    echo "No conda/mamba/micromamba installation found."
    echo "Micromamba will be installed in $HOME/.micromamba"
    echo "A 'conda' alias will be created for the micromamba command"
    confirm "Proceed with micromamba installation?"
    
    # We'll use the official installation script which handles OS detection automatically
    
    # Using the official installation method
    echo "Installing micromamba using the official installation script..."
    
    # Set environment variables to accept defaults
    export MAMBA_ROOT_PREFIX="${HOME}/.micromamba"
    export MAMBA_BIN_DIR="~/.local/bin"
    export MAMBA_INIT_SHELL="yes"
    export MAMBA_CONDA_FORGE="yes"
    
    # Run the official installation script
    curl -L micro.mamba.pm/install.sh | bash -s -- -p
    
    # Set conda alias
    if [ -f "$HOME/.bashrc" ]; then
        echo 'alias conda="micromamba"' >> $HOME/.bashrc
        echo "Created conda alias in .bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        echo 'alias conda="micromamba"' >> $HOME/.zshrc
        echo "Created conda alias in .zshrc"
    else
        echo "Warning: Could not find .bashrc or .zshrc to add conda alias. Please add manually:"
        echo 'alias conda="micromamba"'
    fi
    
    CONDA_CMD="micromamba"
    CONDA_FOUND=true
    
    # Initialize the shell with micromamba
    if [[ -f "${HOME}/micromamba/etc/profile.d/micromamba.sh" ]]; then
        source "${HOME}/micromamba/etc/profile.d/micromamba.sh"
    elif [[ -f "${MICROMAMBA_ROOT_PREFIX}/etc/profile.d/micromamba.sh" ]]; then
        source "${MICROMAMBA_ROOT_PREFIX}/etc/profile.d/micromamba.sh"
    else
        echo "Warning: Unable to find micromamba.sh to source. You may need to restart your shell."
    fi
fi

# Create a directory for the installation if it doesn't exist
INSTALL_DIR="pyscf_installation"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Create the environment.yml file
cat > environment.yml << 'EOL'
name: pyscf
channels:
  - conda-forge
  - defaults
dependencies:
  - numpy
  - scipy
  - h5py
  - pyscf
EOL

echo "Created environment.yml file."
echo "This file defines all the dependencies that will be installed for pySCF."
echo "This includes Python packages like numpy, scipy, h5py, maptplotlib, and pyscf."

# Create pySCF environment
echo "The script will now create a conda environment named '$ENV_NAME' with all required dependencies."
echo "This may take several minutes depending on your internet connection."
confirm "Proceed with creating the conda environment?"
$CONDA_CMD env create -f environment.yml -n $ENV_NAME

# Activate pySCF environment
echo "Activating $ENV_NAME environment..."
if [ "$CONDA_CMD" = "conda" ] || [ "$CONDA_CMD" = "mamba" ]; then
    eval "$($CONDA_CMD shell.bash hook)"
    $CONDA_CMD activate $ENV_NAME
elif [ "$CONDA_CMD" = "micromamba" ]; then
    eval "$($CONDA_CMD shell hook -s bash)"
    $CONDA_CMD activate $ENV_NAME
fi

echo
echo "pySCF installation complete!"
echo
echo "To activate the environment in the future, run:"
echo "  $CONDA_CMD activate $ENV_NAME"
