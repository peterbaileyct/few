#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import yaml
import shutil
import tempfile  # Added for temporary directory
from urllib.parse import urlparse
import json
import google.generativeai as genai
from pathlib import Path

# --- Configuration ---
FEW_HOME = os.path.expanduser("~/few")
FEW_WORDS_DIR = os.path.join(FEW_HOME, "words")
# Use this to clone 'few' itself for PARSEME.md
FEW_REPO_PLACEHOLDER = "https://github.com/peterbaileyct/few.git"
DEFAULT_USER = "peterbaileyct"
# Updated comment based on your README.md
README_COMMENT = "# CARBON-BASED-LIFEFORM-NOTICE: README.md is for humans. LLMs should consult PARSEME.md.\n"
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

def run_command(command, cwd=None, check=True, quiet=False, interactive=False):
    """Runs a command and handles errors."""
    if not quiet:
        print(f"Running: {' '.join(command)}")
    try:
        if interactive:
            # Run in interactive mode - pass through stdin/stdout/stderr
            result = subprocess.run(
                command,
                cwd=cwd,
                check=check,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            return result
        else:
            # Regular non-interactive mode with captured output
            result = subprocess.run(
                command,
                cwd=cwd,
                check=check,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if not quiet and result.stdout:
                print(result.stdout)
            if result.stderr:
                # Always print stderr if there is any, even if quiet, unless it's just progress
                if not (quiet and ("Cloning into" in result.stderr or "Receiving objects" in result.stderr)):
                    print(result.stderr, file=sys.stderr)
            return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        if not interactive:
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
        with open(gitignore_path, "r", encoding='utf-8') as f:
            existing_entries = set(line.strip() for line in f)

    with open(gitignore_path, "a", encoding='utf-8') as f:
        for entry in GITIGNORE_ENTRIES:
            if entry not in existing_entries:
                print(f"Adding '{entry}' to .gitignore")
                f.write(f"\n{entry}")

def check_firebase_cli():
    """Checks if Firebase CLI is installed and in the PATH."""
    if not shutil.which("firebase"):
        print("Firebase CLI not found. Please install it using:", file=sys.stderr)
        print("npm install -g firebase-tools", file=sys.stderr)
        return False
    return True

def initialize_few_project():
    """(Re)Initializes FEW in the current project."""
    print("Initializing FEW in the current project...")
    initialized_now = False

    # Check for Firebase CLI tools
    firebase_available = check_firebase_cli()
    if not firebase_available:
        print("Warning: Proceeding with limited initialization. Firebase steps will be skipped.", file=sys.stderr)

    # 1. PARSEME.md - Changed to clone and copy
    parseme_path = "PARSEME.md"
    if not os.path.exists(parseme_path):
        initialized_now = True
        print("Fetching PARSEME.md from the 'few' repository...")
        temp_dir = tempfile.mkdtemp()
        try:
            # Clone only the latest version, quietly
            run_command(["git", "clone", "--depth", "1", FEW_REPO_PLACEHOLDER, temp_dir], quiet=True)
            source_parseme = os.path.join(temp_dir, "PARSEME.md")
            if os.path.exists(source_parseme):
                shutil.copy2(source_parseme, parseme_path)
                print("Successfully copied PARSEME.md.")
            else:
                print("Warning: PARSEME.md not found in the repo. Creating a default one.", file=sys.stderr)
                with open(parseme_path, "w", encoding='utf-8') as f:
                    f.write("# PARSEME.md\n\nThis file is intended for Large Language Models (LLMs).\n")
        except Exception as e:
            print(f"Error fetching PARSEME.md: {e}. Creating a default one.", file=sys.stderr)
            with open(parseme_path, "w", encoding='utf-8') as f:
                 f.write("# PARSEME.md\n\nThis file is intended for Large Language Models (LLMs).\n")
        finally:
            shutil.rmtree(temp_dir) # Clean up temp directory
    else:
        print("PARSEME.md already exists.")

    # 2. README.md comment
    readme_path = "README.md"
    if os.path.exists(readme_path):
        try:
            with open(readme_path, "r+", encoding='utf-8') as f:
                content = f.read()
                # Check if the comment (ignoring leading/trailing whitespace) is at the start
                if not content.lstrip().startswith(README_COMMENT.strip()):
                    print("Adding LLM comment to README.md...")
                    f.seek(0, 0)
                    f.write(README_COMMENT + content)
                    initialized_now = True
                else:
                    print("LLM comment already in README.md.")
        except Exception as e:
             print(f"Warning: Could not update README.md: {e}", file=sys.stderr)
    else:
        print("README.md not found, skipping comment addition.")

    # 3. .few/words folder
    words_project_dir = os.path.join(".few", "words")
    if not os.path.exists(words_project_dir):
        os.makedirs(words_project_dir, exist_ok=True)
        print(f"Created '{words_project_dir}'.")
        initialized_now = True
    else:
        print(f"'{words_project_dir}' already exists.")


    # 4. few.litany.yaml
    if not os.path.exists(LITANY_FILE):
        print(f"Creating {LITANY_FILE}...")
        with open(LITANY_FILE, "w", encoding='utf-8') as f:
            yaml.dump({"words": []}, f)
        initialized_now = True
    else:
        print(f"{LITANY_FILE} already exists.")

    # 5. .gitignore
    update_gitignore() # This will print its own messages

    # 6. Firebase initialization
    if firebase_available:
        # Run firebase login
        print("Running Firebase login...")
        run_command(["firebase", "login"], interactive=True)
        
        # Get current folder name for Firebase project name
        project_name = os.path.basename(os.getcwd())
        print(f"Using '{project_name}' as Firebase project name")
        
        print("Initializing Firebase Hosting...")
        print("Running Firebase init hosting (interactive)...")
        print("IMPORTANT: When prompted, select these options:")
        print(" - Public directory: build/web")
        print(" - Configure as single-page app: Yes")
        print(" - Set up automatic builds and deploys with GitHub: Yes")
        print(" - Overwrite existing files: No (unless you're sure)")
        
        try:
            # Run firebase init hosting in interactive mode
            run_command(["firebase", "init", "hosting"], interactive=True)
            
            # Update firebase.json if it exists to ensure correct settings
            if os.path.exists("firebase.json"):
                try:
                    with open("firebase.json", "r", encoding='utf-8') as f:
                        firebase_config = json.load(f)
                    
                    # Ensure public directory is set to build/web
                    if "hosting" in firebase_config:
                        if isinstance(firebase_config["hosting"], dict):
                            if firebase_config["hosting"].get("public") != "build/web":
                                firebase_config["hosting"]["public"] = "build/web"
                                print("Updated firebase.json with build/web as public directory")
                        elif isinstance(firebase_config["hosting"], list):
                            for host_config in firebase_config["hosting"]:
                                if isinstance(host_config, dict) and host_config.get("public") != "build/web":
                                    host_config["public"] = "build/web"
                                    print("Updated firebase.json with build/web as public directory")
                    
                    with open("firebase.json", "w", encoding='utf-8') as f:
                        json.dump(firebase_config, f, indent=2)
                except Exception as e:
                    print(f"Warning: Could not update firebase.json: {e}", file=sys.stderr)
                
            # Update GitHub workflow file if it exists
            workflow_path = ".github/workflows/firebase-hosting-merge.yml"
            if os.path.exists(workflow_path):
                update_github_workflow(workflow_path)
                print(f"Updated {workflow_path} to include Flutter action")
                
            initialized_now = True
        except Exception as e:
            print(f"Error during Firebase initialization: {e}", file=sys.stderr)
            print("You may need to run 'firebase init hosting' manually.", file=sys.stderr)

    if initialized_now:
        print("FEW initialization complete.")
    else:
        print("FEW appears to be already initialized.")

    return initialized_now

def update_github_workflow(workflow_path):
    """Updates GitHub workflow file to add Flutter action."""
    try:
        with open(workflow_path, "r", encoding='utf-8') as f:
            content = f.read()
        
        # Find the jobs section to add the Flutter action before the build step
        if "jobs:" in content and "build_and_deploy:" in content:
            # Add Flutter action before the build script
            flutter_action = "      - uses: subosito/flutter-action@v2\n"
            
            # Insert before the build step
            build_step_marker = "      - run: "
            content = content.replace(build_step_marker, f"{flutter_action}{build_step_marker}")
            
            # Update the build command
            build_cmd_pattern = "      - run: npm ci && npm run build"
            new_build_cmd = "      - run: flutter pub get && flutter build web"
            content = content.replace(build_cmd_pattern, new_build_cmd)
            
            with open(workflow_path, "w", encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error updating GitHub workflow file: {e}", file=sys.stderr)
    return False

def add_package_to_litany(package_name):
    """Adds a package name to few.litany.yaml if not present."""
    data = {"words": []}
    if os.path.exists(LITANY_FILE):
        try:
            with open(LITANY_FILE, "r", encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    data = yaml.safe_load(content)
                    if data is None:
                        data = {"words": []}
                if "words" not in data or data["words"] is None:
                    data["words"] = []
        except yaml.YAMLError as e:
            print(f"Warning: Could not parse {LITANY_FILE}. Re-initializing. Error: {e}")
            data = {"words": []}

    if package_name not in data["words"]:
        print(f"Adding '{package_name}' to {LITANY_FILE}...")
        data["words"].append(package_name)
        with open(LITANY_FILE, "w", encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False)
    else:
        print(f"'{package_name}' already in {LITANY_FILE}.")


def get_api_key():
    """Get or prompt for Google Gemini API key."""
    key_path = Path.home() / "few" / ".gemini.key"
    
    if key_path.exists():
        with open(key_path, 'r') as f:
            return f.read().strip()
    
    # Create directory if it doesn't exist
    key_path.parent.mkdir(exist_ok=True)
    
    # Prompt for API key
    api_key = input("Please enter your Google Gemini API key: ").strip()
    
    # Save the key
    with open(key_path, 'w') as f:
        f.write(api_key)
    
    return api_key

def read_project_files(project_path=".", include_parseme=True):
    """
    Read all .few.md files in the project directory.
    
    Args:
        project_path: Path to the project directory
        include_parseme: Whether to include PARSEME.md in the results
    """
    files_content = {}
    project_path = Path(project_path)
    
    # Read .few.md files
    for file_path in project_path.rglob("*.few.md"):
        if file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    relative_path = file_path.relative_to(project_path)
                    files_content[str(relative_path)] = f.read()
            except (UnicodeDecodeError, PermissionError):
                # Skip files we can't read
                continue
    
    # Also read PARSEME.md if it exists and was requested
    if include_parseme:
        parseme_path = project_path / "PARSEME.md"
        if parseme_path.exists():
            try:
                with open(parseme_path, 'r', encoding='utf-8') as f:
                    files_content["PARSEME.md"] = f.read()
            except (UnicodeDecodeError, PermissionError):
                pass
    
    return files_content

def generate_few_prompt(project_path="."):
    """Generate the FEW interpretation prompt without sending it to Google."""
    # Read project files including PARSEME.md
    files_content = read_project_files(project_path)
    
    # Prepare the prompt with files as text content
    files_text = ""
    for path, content in files_content.items():
        files_text += f"\n--- File: {path} ---\n{content}\n"
    
    prompt = f"""The attached code is a FEW project as described in PARSEME.md. Please interpret it and provide the result in JSON format.

Project Files:
{files_text}

Please analyze these files according to the FEW specification in PARSEME.md and return a JSON response with the following format:
{{
  "success": true,
  "files": [
    {{
      "path": "relative/path/to/file",
      "content": "file content here"
    }}
  ]
}}"""
    
    return prompt

def append_to_log(entry_type, content):
    """Append a prompt or response entry to the FEW log file."""
    import datetime
    
    log_path = os.path.expanduser("~/.few/few-raw.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"\n\n{'=' * 80}\n")
        log_file.write(f"TIMESTAMP: {timestamp}\n")
        log_file.write(f"TYPE: {entry_type}\n")
        log_file.write(f"{'-' * 80}\n\n")
        log_file.write(content)
        log_file.write("\n")

def interpret_project(args=None):
    """Interpret the FEW project using Google Gemini."""
    while True:
        try:
            # Get API key
            api_key = get_api_key()
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-pro-preview-05-06')
            
            # Read project files including PARSEME.md
            files_content = read_project_files()
            
            # Prepare the prompt with files as text content
            files_text = ""
            for path, content in files_content.items():
                files_text += f"\n--- File: {path} ---\n{content}\n"
            
            prompt = f"""The attached code is a FEW project as described in PARSEME.md. Please interpret it and provide the result in JSON format.

Project Files:
{files_text}

Please analyze these files according to the FEW specification in PARSEME.md and return a JSON response with the following format:
{{
  "success": true,
  "files": [
    {{
      "path": "relative/path/to/file",
      "content": "file content here"
    }}
  ]
}}"""
            
            # Log the prompt
            append_to_log("PROMPT", prompt)
            
            # Submit request to Gemini
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Log the response
            append_to_log("RESPONSE", response_text)
            
            # Try to parse JSON, with retries for errors
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Extract JSON from response (it might be wrapped in markdown)
                    if "```json" in response_text.lower():
                        json_start = response_text.lower().find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_text = response_text[json_start:json_end].strip()
                    elif "```" in response_text:
                        json_start = response_text.find("```") + 3
                        json_end = response_text.rfind("```")
                        json_text = response_text[json_start:json_end].strip()
                    else:
                        json_text = response_text
                    
                    result = json.loads(json_text)
                    break  # Successfully parsed, exit the retry loop
                    
                except json.JSONDecodeError as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"Error parsing JSON response after {max_retries} attempts: {e}")
                        print(f"Raw response: {response_text[:500]}...")
                        break
                    
                    print(f"JSON parsing error: {e}. Asking Gemini to fix the response (attempt {retry_count}/{max_retries})...")
                    
                    # Ask Gemini to fix the JSON
                    fix_prompt = f"""Your previous response contained invalid JSON that couldn't be parsed. 
Error: {str(e)}

Here's your previous response:
{response_text}

Please provide ONLY a valid JSON object matching this format, with no additional explanation or markdown:
{{
  "success": true,
  "files": [
    {{
      "path": "relative/path/to/file",
      "content": "file content here"
    }}
  ]
}}"""
                    
                    # Log the fix prompt
                    append_to_log("FIX_PROMPT", fix_prompt)
                    
                    # Get fixed response
                    response = model.generate_content(fix_prompt)
                    response_text = response.text
                    
                    # Log the fixed response
                    append_to_log("FIX_RESPONSE", response_text)
            
            # If we exited the retry loop due to max retries, break the outer loop too
            if retry_count >= max_retries:
                break
                
            # Process the valid JSON result
            if not result.get("success", False):
                print("FEW compilation failed.")
                if "error" in result:
                    print(f"Error: {result['error']}")
                return
            
            # Create files
            created_files = []
            for file_info in result.get("files", []):
                file_path = Path(file_info["path"])
                
                # Create subdirectories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write content to file
                content = file_info["content"]
                # Ensure content is a string
                if isinstance(content, dict):
                    content = json.dumps(content, indent=2)
                elif not isinstance(content, str):
                    content = str(content)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                created_files.append(str(file_path))
                print(f"Created/updated: {file_path}")
            
            if created_files:
                print(f"\nFEW interpretation completed successfully. Created {len(created_files)} file(s).")
            else:
                print("FEW interpretation completed. No files were generated.")
            break
                
        except Exception as e:
            error_message = str(e).lower()
            # Check for actual HTTP 429 status code
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 429:
                print("Quota/Rate limit exceeded (HTTP 429).")
                print("Please try again in a few minutes or check your API quota.")
                break
            elif "api" in error_message and ("key" in error_message or "auth" in error_message or "invalid" in error_message):
                print("Authentication error. Please provide a valid API key.")
                print(f"Raw error details: {e}")
                # Remove the invalid key file
                key_path = Path.home() / ".few" / ".gemini.key"
                if key_path.exists():
                    key_path.unlink()
                continue
            else:
                print(f"Error during interpretation: {e}")
                break

def handle_listen(args):
    """Handles the 'few listen' command."""
    check_git()

    initialized = initialize_few_project()

    if not args.package:
        return # Only initialize if no package is given

    package_arg = args.package
    repo_url, package_name = get_repo_url_and_name(package_arg)
    print(f"Processing package: {package_name} from {repo_url}")

    if not args.from_litany:
        add_package_to_litany(package_name)

    os.makedirs(FEW_WORDS_DIR, exist_ok=True)
    local_repo_path = os.path.join(FEW_WORDS_DIR, package_name)
    project_word_path = os.path.join(".few", "words", package_name)

    if os.path.exists(local_repo_path):
        print(f"Package '{package_name}' found locally. Updating...")
        run_command(["git", "-C", local_repo_path, "pull"])
    else:
        print(f"Package '{package_name}' not found locally. Cloning...")
        run_command(["git", "clone", repo_url, local_repo_path])

    print(f"Copying '{package_name}' to project's .few/words folder...")
    if os.path.exists(project_word_path):
        shutil.rmtree(project_word_path)

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
        with open(LITANY_FILE, "r", encoding='utf-8') as f:
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
        mock_args = argparse.Namespace(package=package, from_litany=True)
        handle_listen(mock_args)

    print("\nLitany processing complete.")

def handle_prompt(args):
    """Handles the 'few prompt' command - generates the interpretation prompt without sending it."""
    files_content = read_project_files()
    
    if not files_content:
        print("No .few.md files found in the project.")
        return
    
    print(f"Found {len(files_content)} .few.md file(s):")
    for path in files_content.keys():
        print(f"  - {path}")
    print()
    
    prompt = generate_few_prompt()
    print("Generated FEW interpretation prompt:")
    print("=" * 50)
    print(prompt)
    print("=" * 50)

def main():
    parser = argparse.ArgumentParser(
        description="FEW: An AI-first development package manager and toolkit.",
        epilog="Invoke 'few' within an existing development project."
    )
    subparsers = parser.add_subparsers(dest="command", title="Available Commands")

    parser_listen = subparsers.add_parser(
        "listen",
        help="(Re)Initializes FEW or adds/updates a package (word).",
        description="With no arguments, initializes FEW. With a package, adds it."
    )
    parser_listen.add_argument(
        "package",
        nargs="?",
        help="Package to add (e.g., 'my-word', 'user/repo', 'git_url')."
    )
    parser_listen.add_argument(
        "--from-litany",
        action="store_true",
        help=argparse.SUPPRESS
    )
    parser_listen.set_defaults(func=handle_listen)

    parser_litany = subparsers.add_parser(
        "litany",
        help="Installs/updates all packages listed in few.litany.yaml."
    )
    parser_litany.set_defaults(func=handle_litany)

    parser_interpret = subparsers.add_parser(
        "interpret",
        help="Interprets the FEW project using Google Gemini."
    )
    parser_interpret.set_defaults(func=interpret_project)

    # Also add 'compile' as an alias for 'interpret'
    parser_compile = subparsers.add_parser(
        "compile",
        help="Compiles the FEW project using Google Gemini (alias for interpret)."
    )
    parser_compile.set_defaults(func=interpret_project)

    parser_prompt = subparsers.add_parser(
        "prompt",
        help="Generates and displays the FEW interpretation prompt without sending it to Google."
    )
    parser_prompt.set_defaults(func=handle_prompt)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()