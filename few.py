#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import yaml
import shutil
from urllib.parse import urlparse

# --- Configuration ---
FEW_HOME = os.path.expanduser("~/.few")
FEW_WORDS_DIR = os.path.join(FEW_HOME, "words")
FEW_REPO_PLACEHOLDER = "https://github.com/peterbaileyct/few.git" # Placeholder for the main 'few' repo
DEFAULT_USER = "peterbaileyct"
PARSEME_CONTENT = """
# PARSEME.md

This file is intended for Large Language Models (LLMs).
It contains structured information about the project to facilitate AI-first development.

## Project Structure
- TBD

## Core Concepts
- TBD

## Packages (Words)
- TBD
"""
README_COMMENT = "\n"
GITIGNORE_ENTRIES = [
    ".few/",
    "few.litany.yaml"
]
LITANY_FILE = "few.litany.yaml"

# --- Helper Functions ---

def check_git():
    """Checks if git is installed and in the PATH."""
    if not shutil.which("git"):
        print("Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

def run_command(command, cwd=None, check=True):
    """Runs a command and handles errors."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            encoding='utf-8', # Explicitly set encoding
            errors='replace'   # Handle potential encoding errors
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        print(f"Output:\n{e.output}", file=sys.stderr)
        print(f"Stderr:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def get_repo_url_and_name(package_arg):
    """Derives Git URL and package name from the argument."""
    if "://" in package_arg: # Likely a URL
        url = package_arg
        parsed_url = urlparse(url)
        name = os.path.splitext(os.path.basename(parsed_url.path))[0]
        return url, name
    else: # Likely a name
        name = package_arg
        if "/" in name:
            url = f"https://github.com/{name}.git"
            package_name = name.split("/")[-1]
        else:
            url = f"https://github.com/{DEFAULT_USER}/{name}.git"
            package_name = name
        return url, package_name

def update_gitignore():
    """Ensures .few and few.litany.yaml are in .gitignore."""
    gitignore_path = ".gitignore"
    existing_entries = set()

    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            existing_entries = set(line.strip() for line in f)

    with open(gitignore_path, "a") as f:
        for entry in GITIGNORE_ENTRIES:
            if entry not in existing_entries:
                print(f"Adding '{entry}' to .gitignore")
                f.write(f"\n{entry}")

def initialize_few_project():
    """(Re)Initializes FEW in the current project."""
    print("Initializing FEW in the current project...")

    # 1. PARSEME.md
    if not os.path.exists("PARSEME.md"):
        print("Creating PARSEME.md...")
        with open("PARSEME.md", "w") as f:
            f.write(PARSEME_CONTENT)
    else:
        print("PARSEME.md already exists.")

    # 2. README.md comment
    readme_path = "README.md"
    if os.path.exists(readme_path):
        with open(readme_path, "r+") as f:
            content = f.read()
            if not content.startswith(README_COMMENT):
                print("Adding LLM comment to README.md...")
                f.seek(0, 0)
                f.write(README_COMMENT + content)
            else:
                print("LLM comment already in README.md.")
    else:
        print("README.md not found, skipping comment addition.")

    # 3. .few/words folder
    few_project_dir = ".few"
    words_project_dir = os.path.join(few_project_dir, "words")
    os.makedirs(words_project_dir, exist_ok=True)
    print(f"Ensured '{words_project_dir}' exists.")

    # 4. few.litany.yaml
    if not os.path.exists(LITANY_FILE):
        print(f"Creating {LITANY_FILE}...")
        with open(LITANY_FILE, "w") as f:
            yaml.dump({"words": []}, f)
    else:
        print(f"{LITANY_FILE} already exists.")

    # 5. .gitignore
    update_gitignore()
    print("FEW initialization complete.")
    return True # Indicate that initialization happened or was checked


def add_package_to_litany(package_name):
    """Adds a package name to few.litany.yaml if not present."""
    data = {"words": []}
    if os.path.exists(LITANY_FILE):
        try:
            with open(LITANY_FILE, "r") as f:
                content = f.read()
                # Handle empty file case
                if content.strip():
                    data = yaml.safe_load(content)
                    if data is None: # Handle cases where file is just whitespace
                        data = {"words": []}
                if "words" not in data or data["words"] is None:
                    data["words"] = []
        except yaml.YAMLError as e:
            print(f"Warning: Could not parse {LITANY_FILE}. Re-initializing. Error: {e}")
            data = {"words": []}


    if package_name not in data["words"]:
        print(f"Adding '{package_name}' to {LITANY_FILE}...")
        data["words"].append(package_name)
        with open(LITANY_FILE, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
    else:
        print(f"'{package_name}' already in {LITANY_FILE}.")


def handle_listen(args):
    """Handles the 'few listen' command."""
    check_git()

    initialized = initialize_few_project()

    if not args.package:
        if not initialized:
             print("FEW already initialized.")
        return # Only initialize if no package is given

    package_arg = args.package
    repo_url, package_name = get_repo_url_and_name(package_arg)
    print(f"Processing package: {package_name} from {repo_url}")

    # Add to litany first (if not part of 'few litany' run)
    if not args.from_litany:
        add_package_to_litany(package_name)

    # Ensure ~/.few/words exists
    os.makedirs(FEW_WORDS_DIR, exist_ok=True)

    local_repo_path = os.path.join(FEW_WORDS_DIR, package_name)
    project_word_path = os.path.join(".few", "words", package_name)

    # Clone or Pull
    if os.path.exists(local_repo_path):
        print(f"Package '{package_name}' found locally. Updating...")
        run_command(["git", "pull"], cwd=local_repo_path)
    else:
        print(f"Package '{package_name}' not found locally. Cloning...")
        run_command(["git", "clone", repo_url, local_repo_path])

    # Copy to project .few/words
    print(f"Copying '{package_name}' to project's .few/words folder...")
    if os.path.exists(project_word_path):
        print(f"Removing existing '{project_word_path}' before copying...")
        shutil.rmtree(project_word_path)

    # Use copytree, ignoring .git folder
    shutil.copytree(local_repo_path, project_word_path, ignore=shutil.ignore_patterns('.git'))
    print(f"Package '{package_name}' added successfully.")


def handle_litany(args):
    """Handles the 'few litany' command."""
    check_git()
    print(f"Processing {LITANY_FILE}...")

    if not os.path.exists(LITANY_FILE):
        print(f"Error: {LITANY_FILE} not found. Run 'few listen' first.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(LITANY_FILE, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error reading {LITANY_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    if not data or "words" not in data or not data["words"]:
        print("No packages found in 'words:' section of few.litany.yaml.")
        return

    packages = data["words"]
    print(f"Found packages: {', '.join(packages)}")

    for package in packages:
        print(f"\n--- Processing '{package}' from litany ---")
        # Create a mock args object to call handle_listen
        mock_args = argparse.Namespace(package=package, from_litany=True)
        handle_listen(mock_args)

    print("\nLitany processing complete.")

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(
        description="FEW: An AI-first development package manager and toolkit.",
        epilog="Invoke 'few' within an existing development project."
    )
    subparsers = parser.add_subparsers(dest="command", title="Available Commands")

    # 'listen' command
    parser_listen = subparsers.add_parser(
        "listen",
        help="(Re)Initializes FEW or adds/updates a package (word).",
        description="With no arguments, initializes FEW. With a package, adds it."
    )
    parser_listen.add_argument(
        "package",
        nargs="?", # Makes the argument optional
        help="Package to add (e.g., 'my-word', 'user/repo', 'git_url')."
    )
    parser_listen.add_argument(
        "--from-litany", # Internal flag
        action="store_true",
        help=argparse.SUPPRESS
    )
    parser_listen.set_defaults(func=handle_listen)

    # 'litany' command
    parser_litany = subparsers.add_parser(
        "litany",
        help="Installs/updates all packages listed in few.litany.yaml."
    )
    parser_litany.set_defaults(func=handle_litany)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
