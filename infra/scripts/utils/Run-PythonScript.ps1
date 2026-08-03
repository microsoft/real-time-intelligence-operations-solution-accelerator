<#
.SYNOPSIS
    Unified script to execute Python scripts for Microsoft Fabric operations.

.DESCRIPTION
    A unified PowerShell script that handles Python environment initialization and execution
    of any Python script within the repository. Supports all common Python environment
    options and parameter passing to the target Python script.

.PARAMETER ScriptPath
    Relative path to the Python script to execute (relative to repository root).
    Examples: 
    - "infra/scripts/fabric/deploy_fabric_rti.py"
    - "infra/scripts/fabric/delete_fabric_rti.py" 

.PARAMETER ScriptArguments
    Optional array of arguments to pass to the Python script.

.PARAMETER SkipPythonVirtualEnvironment
    Use system Python directly instead of creating virtual environment.

.PARAMETER SkipPythonDependencies
    Skip installing Python dependencies (assume pre-installed).

.PARAMETER SkipPipUpgrade
    Skip upgrading pip to latest version.

.PARAMETER RequirementsPath
    Path to requirements.txt file. Defaults to repository root requirements.txt.

.EXAMPLE
    .\Run-PythonScript.ps1 -ScriptPath "infra/scripts/fabric/deploy_fabric_rti.py"
    
.EXAMPLE
    .\Run-PythonScript.ps1 -ScriptPath "infra/scripts/fabric/delete_fabric_rti.py" -SkipPythonVirtualEnvironment -SkipPythonDependencies

.NOTES
    Prerequisites: PowerShell 7+, Python 3.9+
    
    This unified script provides a consistent interface for executing Python scripts
    across all Fabric operations with integrated environment management.
#>

param(
    [Parameter(Mandatory = $true, HelpMessage = "Relative path to the Python script to execute (e.g., 'infra/scripts/fabric/deploy_fabric_rti.py')")]
    [string]$ScriptPath,
    
    [Parameter(Mandatory = $false, HelpMessage = "Optional array of arguments to pass to the Python script")]
    [string[]]$ScriptArguments = @(),
    
    [Parameter(Mandatory = $false, HelpMessage = "Skip creating and using Python virtual environment (use system Python directly)")]
    [switch]$SkipPythonVirtualEnvironment,
    
    [Parameter(Mandatory = $false, HelpMessage = "Skip installing Python dependencies from requirements.txt (assume dependencies are already installed)")]
    [switch]$SkipPythonDependencies,
    
    [Parameter(Mandatory = $false, HelpMessage = "Skip upgrading pip to the latest version")]
    [switch]$SkipPipUpgrade,
    
    [Parameter(Mandatory = $false, HelpMessage = "Path to requirements.txt file")]
    [string]$RequirementsPath
)

$ErrorActionPreference = "Stop"

# Helper functions for colored output
function Write-Info { param([string]$Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host $Message -ForegroundColor Red }

# Helper function to find Python executable
# On Windows ARM64 an x64 interpreter is preferred: several dependencies in
# requirements.txt (notably `cryptography`, pulled in transitively by
# azure-identity -> msal -> pyjwt[crypto]) stopped publishing win_arm64 wheels
# after 46.0.3. Under an ARM64 interpreter pip falls back to building from
# source, which requires a Rust toolchain and an OpenSSL installation and fails
# with "Could not find directory of OpenSSL installation". x64 interpreters get
# the win_amd64 wheels and run fine under Windows' x64 emulation.
function Get-PythonCommand {
    $isWindowsOs = $IsWindows -or $env:OS -eq "Windows_NT"

    if ($isWindowsOs -and $env:PROCESSOR_ARCHITECTURE -eq "ARM64") {
        $x64Python = Find-X64PythonOnArm64
        if ($x64Python) {
            Write-Info "Windows ARM64 detected - using x64 Python at '$x64Python' for prebuilt wheel support."
            return $x64Python
        }
        Write-Warning "Windows ARM64 detected but no x64 Python was found."
        Write-Warning "Dependencies such as 'cryptography' have no win_arm64 wheels and will be built from source, which usually fails."
        Write-Warning "Install an x64 build of Python 3.11+ from https://www.python.org/downloads/windows/ (choose the 64-bit installer, not ARM64)."
    }

    $pythonCommands = @("python3", "python")
    foreach ($cmd in $pythonCommands) {
        try {
            $null = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0) { return $cmd }
        }
        catch { }
    }
    throw "Python is not installed or not available in PATH. Please install Python 3.9+ and try again."
}

# Locates an x64 Python interpreter on a Windows ARM64 host.
# Uses the py launcher first, then falls back to well-known install locations.
function Find-X64PythonOnArm64 {
    $candidates = @()

    # `py --list-paths` reports ARM64 builds with an explicit "-arm64" tag, so any
    # entry without that tag is an x64 (or x86) install.
    try {
        $null = & py --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $candidates += (& py --list-paths 2>&1) |
                Where-Object { $_ -match '^\s*-V:(\d+\.\d+)\s' -and $_ -notmatch '-arm64' -and $_ -notmatch '-32' } |
                ForEach-Object { if ($_ -match '(?<path>[A-Za-z]:\\[^\r\n]*python\.exe)') { $Matches['path'].Trim() } }
        }
    }
    catch { }

    $candidates += Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python", "$env:ProgramFiles" -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^Python3\d+$' } |
        ForEach-Object { Join-Path $_.FullName 'python.exe' }

    foreach ($candidate in ($candidates | Where-Object { $_ } | Select-Object -Unique)) {
        if (Test-Path $candidate) {
            if ((Get-PythonArchitecture -PythonExe $candidate) -eq 'AMD64') { return $candidate }
        }
    }
    return $null
}

# Returns the processor architecture reported by a Python interpreter
# (e.g. 'AMD64' or 'ARM64'), or $null when the interpreter cannot be run.
function Get-PythonArchitecture {
    param([string]$PythonExe)

    try {
        $arch = & $PythonExe -c "import platform; print(platform.machine())" 2>&1
        if ($LASTEXITCODE -eq 0) { return "$arch".Trim() }
    }
    catch { }
    return $null
}

# Function to initialize Python environment
function Initialize-PythonEnvironment {
    param(
        [string]$RepoRoot,
        [bool]$SkipVirtualEnv,
        [bool]$SkipDependencies,
        [bool]$SkipPipUpgrade,
        [string]$RequirementsPath
    )
    
    $pythonCmd = Get-PythonCommand
    Write-Success "Python found: $pythonCmd"
    
    if ($SkipVirtualEnv) {
        Write-Info "Skipping Python virtual environment - using system Python"
        $pythonExec = $pythonCmd
    }
    else {
        Write-Warning "Setting up Python virtual environment..."
        $venvPath = Join-Path $RepoRoot ".venv"
        $isWindowsOs = $IsWindows -or $env:OS -eq "Windows_NT"

        $venvPython = if ($isWindowsOs) {
            Join-Path $venvPath "Scripts\python.exe"
        }
        else {
            Join-Path $venvPath "bin\python3"
        }

        # A virtual environment inherits the architecture of the interpreter that
        # created it and cannot be re-pointed. If a previous run created the venv
        # with a different architecture (common on Windows ARM64, where an earlier
        # attempt used the ARM64 interpreter), recreate it so the correct wheels
        # can be installed.
        if ((Test-Path $venvPath) -and (Test-Path $venvPython)) {
            $venvArch = Get-PythonArchitecture -PythonExe $venvPython
            $targetArch = Get-PythonArchitecture -PythonExe $pythonCmd
            if ($venvArch -and $targetArch -and $venvArch -ne $targetArch) {
                Write-Warning "Existing virtual environment is $venvArch but $targetArch is required. Recreating '$venvPath'..."
                Remove-Item -Recurse -Force $venvPath
            }
        }
        elseif (Test-Path $venvPath) {
            Write-Warning "Existing virtual environment at '$venvPath' is incomplete. Recreating..."
            Remove-Item -Recurse -Force $venvPath
        }

        if (-not (Test-Path $venvPath)) {
            & $pythonCmd -m venv "$venvPath"
            if ($LASTEXITCODE -ne 0) { throw "Failed to create Python virtual environment." }
        }
        
        # Activate virtual environment
        $activateScript = if ($isWindowsOs) {
            Join-Path $venvPath "Scripts\Activate.ps1"
        }
        else {
            Join-Path $venvPath "bin\activate.ps1"
        }
        
        if (Test-Path $activateScript) { & $activateScript } 
        else { throw "Virtual environment activation script not found at '$activateScript'." }
        
        $pythonExec = $venvPython
    }
    
    # Upgrade pip if not skipped
    if (-not $SkipPipUpgrade) {
        Write-Warning "Upgrading pip..."
        & $pythonExec -m pip install --upgrade pip --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Warning: Failed to upgrade pip, continuing with existing version..."
        }
    }
    else {
        Write-Info "Skipping pip upgrade"
    }
    
    # Install dependencies if not skipped
    if (-not $SkipDependencies) {
        Write-Warning "Installing requirements..."
        if (-not (Test-Path $RequirementsPath)) {
            throw "requirements.txt not found at: $RequirementsPath"
        }
        & $pythonExec -m pip install -r "$RequirementsPath" --quiet
        if ($LASTEXITCODE -ne 0) {
            if (($IsWindows -or $env:OS -eq "Windows_NT") -and $env:PROCESSOR_ARCHITECTURE -eq "ARM64" -and
                (Get-PythonArchitecture -PythonExe $pythonExec) -eq "ARM64") {
                Write-Warning ""
                Write-Warning "This looks like the known Windows ARM64 wheel issue."
                Write-Warning "Packages such as 'cryptography' publish no win_arm64 wheels, so pip tries to build them"
                Write-Warning "from source and fails (typically 'Could not find directory of OpenSSL installation')."
                Write-Warning "Fix: install an x64 build of Python 3.11+ (the 64-bit installer, NOT the ARM64 one) from"
                Write-Warning "https://www.python.org/downloads/windows/ then delete the '.venv' folder and retry."
            }
            throw "Failed to install Python dependencies."
        }
    }
    else {
        Write-Info "Skipping Python dependencies installation"
    }
    
    return $pythonExec
}

Write-Info "Starting Python script execution..."

try {
    # Calculate paths
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptDir))
    
    # Set default requirements path if not provided
    if ([string]::IsNullOrWhiteSpace($RequirementsPath)) {
        $RequirementsPath = Join-Path $RepoRoot "requirements.txt"
    }
    
    # Resolve the target Python script path
    $TargetScriptPath = Join-Path $RepoRoot $ScriptPath
    if (-not (Test-Path $TargetScriptPath)) {
        throw "Python script not found: $TargetScriptPath"
    }
    
    # Get the directory of the target script for working directory
    $TargetScriptDir = Split-Path -Parent $TargetScriptPath
    $TargetScriptName = Split-Path -Leaf $TargetScriptPath
    
    Write-Success "Target script: $TargetScriptPath"
    Write-Success "Working directory: $TargetScriptDir"
    
    # Initialize Python environment
    $pythonExec = Initialize-PythonEnvironment -RepoRoot $RepoRoot -SkipVirtualEnv:$SkipPythonVirtualEnvironment -SkipDependencies:$SkipPythonDependencies -SkipPipUpgrade:$SkipPipUpgrade -RequirementsPath $RequirementsPath
    
    # Change to the target script directory and execute
    Push-Location $TargetScriptDir
    Write-Info "Executing Python script..."
    
    # Execute Python script with arguments
    if ($ScriptArguments.Count -gt 0) {
        Write-Warning "Arguments: $($ScriptArguments -join ' ')"
        & $pythonExec -u $TargetScriptName @ScriptArguments
    }
    else {
        & $pythonExec -u $TargetScriptName
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✅ Python script execution completed successfully!"
    }
    else {
        throw "Python script execution failed with exit code: $LASTEXITCODE"
    }
}
catch {
    Write-Error "❌ Script execution failed: $($_.Exception.Message)"
    Write-Host ""
    Write-Warning "Troubleshooting tips:"
    @(
        "1. Ensure you are logged in to Azure CLI: az login",
        "2. Verify you have appropriate permissions for the operation",
        "3. Check that all required environment variables are set",
        "4. Ensure the Python script path is correct and accessible",
        "5. Verify Python 3.9+ is installed and available in PATH",
        "6. Check that requirements.txt exists and is accessible"
    ) | ForEach-Object { Write-Host $_ -ForegroundColor White }
    exit 1
}
finally {
    # Cleanup
    if ($env:VIRTUAL_ENV -and (Get-Command deactivate -ErrorAction SilentlyContinue)) {
        deactivate
    }
    if (Get-Location -Stack -ErrorAction SilentlyContinue) {
        Pop-Location
    }
}