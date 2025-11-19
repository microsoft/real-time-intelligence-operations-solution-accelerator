param(
    [Parameter(Mandatory = $false, HelpMessage = "Skip creating and using Python virtual environment (use system Python directly)")]
    [switch]$SkipPythonVirtualEnvironment
)

$ErrorActionPreference = "Stop"

# Helper functions for colored output
function Write-Info { param([string]$Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host $Message -ForegroundColor Red }

function Get-PythonCommand {
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
        
        if (-not (Test-Path $venvPath)) {
            & $pythonCmd -m venv "$venvPath"
            if ($LASTEXITCODE -ne 0) { throw "Failed to create Python virtual environment." }
        }
        
        # Activate virtual environment
        $activateScript = if ($IsWindows -or $env:OS -eq "Windows_NT") {
            Join-Path $venvPath "Scripts\Activate.ps1"
        }
        else {
            Join-Path $venvPath "bin\activate.ps1"
        }
        
        if (Test-Path $activateScript) { & $activateScript } 
        else { throw "Virtual environment activation script not found at '$activateScript'." }
        
        $pythonExec = if ($IsWindows -or $env:OS -eq "Windows_NT") {
            Join-Path $venvPath "Scripts\python.exe"
        }
        else {
            Join-Path $venvPath "bin\python3"
        }
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
        if ($LASTEXITCODE -ne 0) { throw "Failed to install Python dependencies." }
    }
    else {
        Write-Info "Skipping Python dependencies installation"
    }
    
    return $pythonExec
}

Write-Info "Starting Microsoft Fabric deployment script..."

try {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    # Script is located at infra\scripts\utils\Run-FabricRTIPythonScript.ps1
    $RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptDir))
    $FabricScriptDir = Join-Path (Split-Path -Parent $ScriptDir) "fabric"
    $RequirementsPath = Join-Path $FabricScriptDir "requirements.txt"
    $pythonExec = Initialize-PythonEnvironment -RepoRoot $RepoRoot -SkipVirtualEnv:$SkipPythonVirtualEnvironment -SkipDependencies $False -SkipPipUpgrade $False -RequirementsPath $RequirementsPath

    Push-Location $FabricScriptDir
    Write-Info "Starting Fabric items deployment..."
    & $pythonExec -u deploy_fabric_rti.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✅ Fabric deployment completed successfully!"
    }
    else {
        throw "Python script execution failed with exit code: $LASTEXITCODE"
    }
}
catch {
    Write-Error "❌ Deployment failed: $($_.Exception.Message)"
    Write-Host ""
    Write-Warning "Troubleshooting tips:"
    @(
        "1. Ensure you are logged in to Azure CLI: az login",
        "2. Verify you have permissions in the Fabric capacity and workspace", 
        "3. Check that the capacity name is correct and accessible"
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