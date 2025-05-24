#Requires -Version 5.1
#https://g.co/gemini/share/7a2cc63a3589
<#
.SYNOPSIS
    Installs the 'few' Python script tool.
.DESCRIPTION
    Clones the 'few' repository, creates an installation directory,
    moves the script, and adds the directory to the user's PATH.
.NOTES
    Requires Git to be installed and available in the PATH.
    Requires PowerShell 5.1 or later.
    You might need to restart PowerShell/Explorer/Windows for PATH changes to take full effect.
    This script assumes 'few.py' will be run using Python. Ensure Python is installed
    and you can run Python scripts from your terminal. You might run it as 'python few'
    or associate .py files (or files without extensions) with Python.
#>

# --- Configuration ---
$RepoUrl = "https://github.com/peterbaileyct/few/"
$InstallDir = Join-Path -Path $HOME -ChildPath ".few"
$ScriptName = "few"
$SourceFile = "few.py"

# --- Functions ---
function Test-CommandExists {
    param (
        [string]$Command
    )
    $Exists = $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
    return $Exists
}

function Add-UserPath {
    param (
        [string]$PathToAdd
    )

    $UserPathScope = [System.EnvironmentVariableTarget]::User
    $CurrentPath = [System.Environment]::GetEnvironmentVariable('Path', $UserPathScope)

    $PathArray = $CurrentPath -split ';' | Where-Object { $_ -ne '' }

    if ($PathArray -contains $PathToAdd) {
        Write-Host "$PathToAdd is already in your user PATH."
    } else {
        Write-Host "Adding $PathToAdd to your user PATH..."
        $NewPath = ($PathArray + $PathToAdd) -join ';'
        [System.Environment]::SetEnvironmentVariable('Path', $NewPath, $UserPathScope)

        # Update the current session's PATH
        $env:Path = $NewPath

        Write-Host "Successfully added to PATH. You may need to restart PowerShell or your computer for changes to apply everywhere."
    }
}

# --- Main Script ---
Write-Host "Starting installation of 'few'..."

# 1. Check for Git
if (-not (Test-CommandExists -Command "git")) {
    Write-Error "Error: 'git' is not installed or not in your PATH. Please install it before running this script."
    exit 1
}

# 2. Create temporary directory
$TempDir = Join-Path -Path $env:TEMP -ChildPath ([System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $TempDir | Out-Null
Write-Host "Created temporary directory: $TempDir"

try {
    # 3. Clone the repository
    Write-Host "Cloning $RepoUrl..."
    git clone --quiet $RepoUrl $TempDir

    # 4. Create installation directory (Force ensures it works even if it exists)
    Write-Host "Creating installation directory: $InstallDir..."
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

    # 5. Move and rename the script
    $SourcePath = Join-Path -Path $TempDir -ChildPath $SourceFile
    $DestinationPath = Join-Path -Path $InstallDir -ChildPath $ScriptName
    Write-Host "Moving $SourcePath to $DestinationPath..."
    Move-Item -Path $SourcePath -Destination $DestinationPath -Force

    # 6. Add to PATH
    Add-UserPath -PathToAdd $InstallDir

    Write-Host "Installation complete! 🎉"
    Write-Host "Please restart your PowerShell session or open a new one."
    Write-Host "Note: To run the tool, you might need to type 'python few' or configure file associations."

}
catch {
    Write-Error "An error occurred during installation: $_"
}
finally {
    # 7. Clean up temporary directory
    Write-Host "Cleaning up temporary files..."
    if (Test-Path $TempDir) {
        Remove-Item -Recurse -Force -Path $TempDir
    }
}