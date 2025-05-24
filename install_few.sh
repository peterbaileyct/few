#!/bin/bash
# https://g.co/gemini/share/7a2cc63a3589
# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
REPO_URL="https://github.com/peterbaileyct/few/"
INSTALL_DIR="$HOME/.few"
SCRIPT_NAME="few"
SOURCE_FILE="few.py"

# --- Functions ---
check_command() {
  if ! command -v "$1" &> /dev/null; then
    echo "Error: '$1' is not installed. Please install it before running this script."
    exit 1
  fi
}

add_to_path() {
  local path_to_add="$1"
  local shell_config_file=""

  # Detect shell configuration file
  if [ -n "$BASH_VERSION" ]; then
    shell_config_file="$HOME/.bashrc"
  elif [ -n "$ZSH_VERSION" ]; then
    shell_config_file="$HOME/.zshrc"
  else
    # Fallback or try to detect others, .profile is a common one
    shell_config_file="$HOME/.profile"
    echo "Warning: Could not detect BASH or ZSH, attempting to use $shell_config_file."
  fi

  if [ ! -f "$shell_config_file" ]; then
      touch "$shell_config_file"
      echo "Created $shell_config_file."
  fi

  # Check if the path is already in the config file
  if ! grep -q "export PATH=\"$path_to_add:\$PATH\"" "$shell_config_file"; then
    echo "Adding $path_to_add to PATH in $shell_config_file..."
    echo "" >> "$shell_config_file" # Add a newline for separation
    echo "# Add 'few' tool to PATH" >> "$shell_config_file"
    echo "export PATH=\"$path_to_add:\$PATH\"" >> "$shell_config_file"
    echo "Successfully added to PATH. Please run 'source $shell_config_file' or restart your shell."
  else
    echo "$path_to_add is already in your PATH in $shell_config_file."
  fi
}

# --- Main Script ---
echo "Starting installation of 'few'..."

# 1. Check for Git
check_command "git"

# 2. Create temporary directory and set up cleanup
TEMP_DIR=$(mktemp -d)
trap 'echo "Cleaning up temporary files..."; rm -rf "$TEMP_DIR"' EXIT
echo "Created temporary directory: $TEMP_DIR"

# 3. Clone the repository
echo "Cloning $REPO_URL..."
git clone --quiet "$REPO_URL" "$TEMP_DIR"

# 4. Create installation directory
echo "Creating installation directory: $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# 5. Move and rename the script
echo "Moving $SOURCE_FILE to $INSTALL_DIR/$SCRIPT_NAME..."
mv "$TEMP_DIR/$SOURCE_FILE" "$INSTALL_DIR/$SCRIPT_NAME"

# 6. Make the script executable
echo "Making $INSTALL_DIR/$SCRIPT_NAME executable..."
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

# 7. Add to PATH
add_to_path "$INSTALL_DIR"

echo "Installation complete! 🎉"
echo "Please run 'source <your_shell_config_file>' (e.g., 'source ~/.bashrc') or open a new terminal to use the 'few' command."

# Trap cleanup will run on exit