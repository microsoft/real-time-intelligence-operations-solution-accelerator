<#
.SYNOPSIS
    Get Microsoft Fabric Activator (Reflex) Definition using REST API

.DESCRIPTION
    This script retrieves and decodes Microsoft Fabric Activator (Reflex) definitions using the Fabric REST API.
    It handles Azure CLI authentication, makes the API request, and decodes the Base64 payload to provide
    readable activator configuration including entities, triggers, and other components.
    By default, it also tokenizes the resulting JSON files using the Run-FabricJsonTokenizer.ps1 script.

.PARAMETER WorkspaceId
    The workspace ID (GUID) containing the activator

.PARAMETER ReflexId
    The activator (reflex) ID (GUID) to retrieve

.PARAMETER FolderPath
    Path to save the decoded definition files (defaults to "src/activator" relative to repository root)

.PARAMETER Format
    Optional format parameter for the activator definition (as supported by the API)

.PARAMETER SkipTokenization
    If specified, skips the automatic tokenization of JSON files after creation

.EXAMPLE
    .\Get-FabricActivatorDefinition.ps1 -WorkspaceId "aaaabbbb-0000-cccc-1111-dddd2222eeee" -ReflexId "bbbbcccc-1111-dddd-2222-eeee3333ffff"

.EXAMPLE
    .\Get-FabricActivatorDefinition.ps1 -WorkspaceId "aaaabbbb-0000-cccc-1111-dddd2222eeee" -ReflexId "bbbbcccc-1111-dddd-2222-eeee3333ffff" -FolderPath "C:\temp\activator"

.NOTES
    Requires Azure CLI to be installed and logged in with appropriate permissions to access Fabric resources.
    
    Required Scopes:
    - Reflex.ReadWrite.All or Item.ReadWrite.All
    
    Required Permissions:
    - Read and write permissions for the reflex

.LINK
    https://learn.microsoft.com/en-us/rest/api/fabric/reflex/items/get-reflex-definition
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')]
    [string]$WorkspaceId,
    
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')]
    [string]$ReflexId,
    
    [Parameter(Mandatory = $false)]
    [string]$FolderPath = $null,
    
    [Parameter(Mandatory = $false)]
    [string]$Format,

    [Parameter(Mandatory = $false)]
    [int]$TimeoutSeconds = 240,

    [Parameter(Mandatory = $false)]
    [switch]$SkipTokenization
)

# Global variables
$script:ApiUrl = "https://api.fabric.microsoft.com/v1"
$script:ResourceUrl = "https://api.fabric.microsoft.com"
$script:AccessToken = $null
$script:TokenExpiry = $null

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARNING", "ERROR")]
        [string]$Level = "INFO"
    )
    
    $icon = switch ($Level) {
        "ERROR" { "❌" }
        "WARNING" { "⚠️" }
        default { "ℹ️" }
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "$icon [$timestamp] $Message" -ForegroundColor $(
        switch ($Level) {
            "ERROR" { "Red" }
            "WARNING" { "Yellow" }
            default { "White" }
        }
    )
}

function Get-AuthToken {
    <#
    .SYNOPSIS
        Get or refresh Azure CLI authentication token for Fabric API
    #>
    
    try {
        # Check if we need to refresh the token (refresh 5 minutes before expiry)
        $currentTime = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        
        if (-not $script:AccessToken -or ($script:TokenExpiry -and $currentTime -gt ($script:TokenExpiry - 300))) {
            Write-Log "Getting authentication token from Azure CLI"
            
            # Get token using Azure CLI
            $tokenResponse = az account get-access-token --resource $script:ResourceUrl --query "{accessToken:accessToken,expiresOn:expiresOn}" --output json 2>$null
            
            if ($LASTEXITCODE -ne 0) {
                throw "Azure CLI authentication failed. Please run 'az login' first."
            }
            
            $tokenData = $tokenResponse | ConvertFrom-Json
            $script:AccessToken = $tokenData.accessToken
            
            # Parse expiry time (Azure CLI returns ISO 8601 format)
            $expiryDateTime = [DateTime]::Parse($tokenData.expiresOn)
            $script:TokenExpiry = [DateTimeOffset]::new($expiryDateTime).ToUnixTimeSeconds()
            
            Write-Log "Authentication successful"
        }
        
        return $script:AccessToken
    }
    catch {
        throw "Authentication failed: $($_.Exception.Message)"
    }
}

function Invoke-FabricApiRequest {
    <#
    .SYNOPSIS
        Make HTTP request to Fabric API with error handling and authentication
    #>
    param(
        [string]$Uri,
        [string]$Method = "GET",
        [object]$Body = $null,
        [hashtable]$Headers = @{},
        [int]$TimeoutSec = $TimeoutSeconds,
        [int]$MaxRetries = 3
    )
    
    $fullUrl = "$script:ApiUrl/$($Uri.TrimStart('/'))"
    $retryCount = 0
    
    do {
        try {
            Write-Log "Making $Method request to $fullUrl $(if ($retryCount -gt 0) { "(attempt $($retryCount + 1))" })"
            
            # Prepare headers with authentication
            $requestHeaders = @{
                'Content-Type'  = 'application/json; charset=utf-8'
                'Authorization' = "Bearer $(Get-AuthToken)"
            }
            
            # Add custom headers
            foreach ($key in $Headers.Keys) {
                $requestHeaders[$key] = $Headers[$key]
            }
            
            # Prepare request parameters
            $requestParams = @{
                Uri             = $fullUrl
                Method          = $Method
                Headers         = $requestHeaders
                TimeoutSec      = $TimeoutSec
                UseBasicParsing = $true
            }
            
            if ($Body) {
                if ($Body -is [string]) {
                    $requestParams.Body = $Body
                }
                else {
                    $requestParams.Body = $Body | ConvertTo-Json -Depth 10 -Compress
                }
            }
            
            $response = Invoke-WebRequest @requestParams
            
            # Log request ID if available
            $requestId = $response.Headers['requestId']
            if ($requestId) {
                Write-Log "Request ID: $requestId"
            }
            
            # Handle different status codes
            switch ($response.StatusCode) {
                200 {
                    Write-Log "Request completed successfully"
                    return $response
                }
                202 {
                    Write-Log "Long-running operation detected, returning 202 response"
                    return $response
                }
                429 {
                    # Rate limiting - retry with exponential backoff
                    $retryAfter = if ($response.Headers['Retry-After']) { 
                        [int]$response.Headers['Retry-After'] 
                    }
                    else { 
                        [Math]::Min(60, [Math]::Pow(2, $retryCount))
                    }
                    
                    $retryAfter = [Math]::Min($retryAfter, 300)  # Cap at 5 minutes
                    
                    Write-Log "Rate limit exceeded. Retrying in $retryAfter seconds... (attempt $($retryCount + 1)/$MaxRetries)" "WARNING"
                    Start-Sleep -Seconds $retryAfter
                    $retryCount++
                    continue
                }
                default {
                    $errorMsg = "API request failed with status $($response.StatusCode)"
                    
                    try {
                        $errorResponse = $response.Content | ConvertFrom-Json
                        Write-Log "Error response: $($errorResponse | ConvertTo-Json -Depth 5)" "ERROR"
                        
                        if ($errorResponse.error) {
                            $errorMsg += ": $($errorResponse.error.message)"
                        }
                    }
                    catch {
                        $errorMsg += ": $($response.Content.Substring(0, [Math]::Min(500, $response.Content.Length)))"
                    }
                    
                    throw $errorMsg
                }
            }
        }
        catch {
            if ($_.Exception -is [System.Net.WebException] -and $_.Exception.Response.StatusCode -eq 429 -and $retryCount -lt $MaxRetries) {
                # Handle rate limiting in older PowerShell versions
                $retryAfter = 60
                Write-Log "Rate limit exceeded. Retrying in $retryAfter seconds... (attempt $($retryCount + 1)/$MaxRetries)" "WARNING"
                Start-Sleep -Seconds $retryAfter
                $retryCount++
                continue
            }
            
            throw "Request failed: $($_.Exception.Message)"
        }
    } while ($retryCount -lt $MaxRetries)
    
    throw "Maximum retries ($MaxRetries) exceeded"
}

function ConvertFrom-Base64 {
    <#
    .SYNOPSIS
        Decode Base64 string to UTF-8 text
    #>
    param(
        [string]$Base64String
    )
    
    try {
        $bytes = [System.Convert]::FromBase64String($Base64String)
        return [System.Text.Encoding]::UTF8.GetString($bytes)
    }
    catch {
        throw "Failed to decode Base64 string: $($_.Exception.Message)"
    }
}

function Invoke-JsonTokenization {
    <#
    .SYNOPSIS
        Tokenize JSON files using the Run-FabricJsonTokenizer.ps1 script
    #>
    param(
        [string]$FolderPath,
        [string]$SchemaType
    )
    
    try {
        Write-Log "Starting JSON tokenization for schema type: $SchemaType in folder: $FolderPath"
        
        # Get the path to the tokenizer script
        $tokenizerScript = Join-Path $PSScriptRoot "Run-FabricJsonTokenizer.ps1"
        
        if (-not (Test-Path $tokenizerScript)) {
            Write-Log "Tokenizer script not found at: $tokenizerScript" "WARNING"
            return
        }
        
        if (-not (Test-Path $FolderPath)) {
            Write-Log "Folder not found at: $FolderPath" "WARNING"
            return
        }
        
        # Let the tokenizer script find and process all appropriate files based on schema type
        # This ensures both .json and .platform files are processed correctly
        Write-Log "Running tokenizer for schema type: $SchemaType"
        & $tokenizerScript -SchemaType $SchemaType
        
        Write-Log "JSON tokenization completed successfully"
    }
    catch {
        Write-Log "Failed to tokenize JSON files: $($_.Exception.Message)" "WARNING"
    }
}

function Get-ActivatorDefinition {
    <#
    .SYNOPSIS
        Get and decode Activator (Reflex) definition from Fabric API
    #>
    
    try {
        Write-Log "Getting activator definition for workspace $WorkspaceId, reflex $ReflexId"
        
        # Build URI with optional format parameter
        $uri = "workspaces/$WorkspaceId/reflexes/$ReflexId/getDefinition"
        if ($Format) {
            $uri += "?format=$Format"
        }
        
        # Make API request
        $response = Invoke-FabricApiRequest -Uri $uri -Method "POST"
        
        if ($response.StatusCode -eq 202) {
            # Handle long-running operation
            $location = $response.Headers['Location']
            $operationId = $response.Headers['x-ms-operation-id']
            $retryAfter = if ($response.Headers['Retry-After']) { [int]$response.Headers['Retry-After'] } else { 30 }
            
            Write-Log "Long-running operation started. Operation ID: $operationId" "WARNING"
            Write-Log "Polling for completion every $retryAfter seconds..."
            
            do {
                Start-Sleep -Seconds $retryAfter
                Write-Log "Checking operation status..."
                
                try {
                    $statusResponse = Invoke-WebRequest -Uri $location -Headers @{
                        'Authorization' = "Bearer $(Get-AuthToken)"
                    } -UseBasicParsing
                    
                    if ($statusResponse.StatusCode -eq 200) {
                        $response = $statusResponse
                        Write-Log "Operation completed successfully"
                        break
                    }
                    elseif ($statusResponse.StatusCode -eq 202) {
                        Write-Log "Operation still in progress..."
                        continue
                    }
                    else {
                        throw "Unexpected status code: $($statusResponse.StatusCode)"
                    }
                }
                catch {
                    Write-Log "Error checking operation status: $($_.Exception.Message)" "ERROR"
                    throw
                }
            } while ($true)
        }
        elseif ($response.StatusCode -ne 200) {
            throw "Failed to get activator definition. Status: $($response.StatusCode)"
        }
        
        # Parse response
        $responseData = $response.Content | ConvertFrom-Json
        
        if (-not $responseData.definition -or -not $responseData.definition.parts) {
            throw "Invalid response format: missing definition or parts"
        }
        
        Write-Log "Retrieved activator definition with $($responseData.definition.parts.Count) part(s)"
        
        # Decode all parts
        $decodedParts = @{}
        $summaryInfo = @{}
        
        foreach ($part in $responseData.definition.parts) {
            Write-Log "Processing part: $($part.path)"
            
            if ($part.payloadType -eq "InlineBase64") {
                try {
                    $decodedContent = ConvertFrom-Base64 -Base64String $part.payload
                    $decodedParts[$part.path] = $decodedContent
                    
                    # Try to parse as JSON for summary information
                    try {
                        $jsonContent = $decodedContent | ConvertFrom-Json
                        
                        # Analyze content based on file name
                        switch ($part.path) {
                            "ReflexEntities.json" {
                                if ($jsonContent.entities) {
                                    $summaryInfo["Entities"] = $jsonContent.entities.Count
                                }
                                if ($jsonContent.triggers) {
                                    $summaryInfo["Triggers"] = $jsonContent.triggers.Count
                                }
                                if ($jsonContent.rules) {
                                    $summaryInfo["Rules"] = $jsonContent.rules.Count
                                }
                            }
                            default {
                                # Generic analysis for other JSON files
                                if ($jsonContent -is [System.Object] -and $jsonContent.PSObject.Properties.Count -gt 0) {
                                    $summaryInfo[$part.path] = "JSON object with $($jsonContent.PSObject.Properties.Count) properties"
                                }
                            }
                        }
                    }
                    catch {
                        # Not JSON or parsing failed - that's okay
                        $summaryInfo[$part.path] = "Text content ($($decodedContent.Length) characters)"
                    }
                }
                catch {
                    Write-Log "Failed to decode part $($part.path): $($_.Exception.Message)" "WARNING"
                    $decodedParts[$part.path] = "[DECODE ERROR: $($_.Exception.Message)]"
                    $summaryInfo[$part.path] = "Decode error"
                }
            }
            else {
                Write-Log "Unsupported payload type for part $($part.path): $($part.payloadType)" "WARNING"
                $decodedParts[$part.path] = "[UNSUPPORTED PAYLOAD TYPE: $($part.payloadType)]"
                $summaryInfo[$part.path] = "Unsupported payload type"
            }
        }
        
        Write-Log "Successfully decoded activator definition"
        
        # Display summary
        Write-Log "Activator definition summary:"
        foreach ($key in $summaryInfo.Keys) {
            Write-Log "  $key : $($summaryInfo[$key])"
        }
        
        # Save to files if folder path specified
        if ($FolderPath) {
            Write-Log "Saving decoded activator definition files to: $FolderPath"
            
            # Create directory if it doesn't exist
            if (-not (Test-Path $FolderPath)) {
                New-Item -ItemType Directory -Path $FolderPath -Force | Out-Null
            }
            
            # Save each part to a separate file
            foreach ($partPath in $decodedParts.Keys) {
                $fileName = $partPath -replace '[\\/:*?"<>|]', '_'  # Replace invalid characters
                $filePath = Join-Path $FolderPath $fileName
                
                try {
                    # Try to pretty-print JSON files
                    if ($partPath -like "*.json" -and -not $decodedParts[$partPath].StartsWith("[")) {
                        $jsonContent = $decodedParts[$partPath] | ConvertFrom-Json
                        $jsonContent | ConvertTo-Json -Depth 10 | Set-Content -Path $filePath -Encoding UTF8 -Force
                    }
                    else {
                        $decodedParts[$partPath] | Set-Content -Path $filePath -Encoding UTF8 -Force
                    }
                    
                    Write-Log "  Saved: $fileName"
                }
                catch {
                    Write-Log "  Failed to save $fileName : $($_.Exception.Message)" "WARNING"
                }
            }
            
            Write-Log "Activator definition files saved successfully"
            
            # Tokenize the JSON files unless skipped
            if (-not $SkipTokenization) {
                Invoke-JsonTokenization -FolderPath $FolderPath -SchemaType "Activator"
            }
        }
        
        # Return the decoded parts
        return $decodedParts
    }
    catch {
        Write-Log "Failed to get activator definition: $($_.Exception.Message)" "ERROR"
        throw
    }
}

# Main execution
try {
    # Calculate default folder path if not provided
    if (-not $FolderPath) {
        $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
        # Script is located at infra\scripts\utils\Get-FabricActivatorDefinition.ps1
        $RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptDir))
        $FolderPath = Join-Path $RepoRoot "src" | Join-Path -ChildPath "activator"
        Write-Log "Using default folder path: $FolderPath"
    }
    
    Write-Log "Starting Fabric Activator (Reflex) Definition retrieval"
    Write-Log "Workspace ID: $WorkspaceId"
    Write-Log "Reflex ID: $ReflexId"
    Write-Log "Folder Path: $FolderPath"
    
    if ($Format) {
        Write-Log "Format: $Format"
    }
    
    # Get and display activator definition
    $activatorDefinition = Get-ActivatorDefinition
    
    Write-Log "Activator definition retrieved successfully" 
    
    # Display the decoded content
    Write-Host "`n=== DECODED ACTIVATOR DEFINITION PARTS ===" -ForegroundColor Green
    
    foreach ($partPath in $activatorDefinition.Keys) {
        Write-Host "`n--- PART: $partPath ---" -ForegroundColor Cyan
        
        # Try to format as JSON if possible
        try {
            if ($partPath -like "*.json" -and -not $activatorDefinition[$partPath].StartsWith("[")) {
                $jsonContent = $activatorDefinition[$partPath] | ConvertFrom-Json
                $jsonContent | ConvertTo-Json -Depth 10
            }
            else {
                $activatorDefinition[$partPath]
            }
        }
        catch {
            # Display as-is if JSON parsing fails
            $activatorDefinition[$partPath]
        }
    }
    
    Write-Host "`n=== END OF DEFINITION ===" -ForegroundColor Green
    
}
catch {
    Write-Log "Script execution failed: $($_.Exception.Message)" "ERROR"
    exit 1
}

Write-Log "Script completed successfully"