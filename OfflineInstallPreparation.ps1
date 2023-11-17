<#
    .Synopsis
        Prepares the repository for an offline deployment.

    .Description
        These playbooks can be run from a network without access to the internet,
        but it needs to prepare packages to be run offline.
        This script downloads and internalizes packages for such usage.

    .Notes
        This must be run on a Windows system with access to the internet because 
        it uses Chocolatey for Business' Package Internalizer.

    .Notes
        Instead of using this script, you can internalize all required packages manually, 
        zip them, and drop them in the files directory as shown below.

    .Example
        .\OfflineInstallPreparation.ps1 -LicensePath C:\ProgramData\chocolatey\license\chocolatey.license.xml
#>
[CmdletBinding()]
param(
    [ValidateScript({
        if (-not (Test-Path (Convert-Path $_))) {
            throw "License file does not exist at '$($_)'. Please provide a valid -LicensePath"
        }
        $true
    })]
    [string]$LicensePath = "C:\ProgramData\chocolatey\license\chocolatey.license.xml",

    [ValidateScript({
        if (-not (Test-Path (Convert-Path $_))) {
            throw "Certificate file does not exist at '$($_)'. Please provide a valid -CertificatePath"
        }
        $true
    })]
    [Parameter(Mandatory)]
    [string]$CertificatePath,

    [Parameter(Mandatory)]
    [securestring]$CertificatePassword,

    [string]$WorkingDirectory = $(Join-Path $env:Temp "choco-offline")
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$LicensePath = Convert-Path $LicensePath
$CertificatePath = Convert-Path $CertificatePath

# Validate License
try {
    [xml]$License = Get-Content $LicensePath
    $Expiry = Get-Date $License.license.expiration
    if (-not $Expiry -or $Expiry -lt (Get-Date)) {throw}
} catch {
    throw "License '$($LicensePath)' is not valid.$(if ($Expiry) {" It expired at '$($Expiry)'."})"
}

# Validate Certificate and Password
try {
    $null = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
        $CertificatePath,
        $CertificatePassword,
        "EphemeralKeySet"
    )
} catch {
    throw "Certificate '$($CertificatePath)' failed to import with the provided CertificatePassword. Please ensure the Certificate Path and Password are correct."
}

if (-not (Get-Command choco.exe)) {
    Get-Content $PSScriptRoot\templates\ChocolateyInstall.ps1.j2 | Invoke-Expression
}

# Initialize environment, ensure Chocolatey For Business, etc.
$Licensed = ($($(choco)[0] -match "^Chocolatey (?<Version>\S+)\s*(?<LicenseType>Business)?$") -and $Matches.LicenseType)
$InstalledLicensePath = "$env:ChocolateyInstall\license\chocolatey.license.xml"
if (-not $Licensed) {
    if (-not (Test-Path $InstalledLicensePath)) {
        if (-not (Test-Path $env:ChocolateyInstall\license)) {
            $null = New-Item $env:ChocolateyInstall\license -ItemType Directory
        }
        Copy-Item $LicensePath $InstalledLicensePath -Force
    }
    choco install chocolatey.extension --source https://licensedpackages.chocolatey.org/api/v2/ --confirm
}

# Download each set of packages to the output directories
$PackageWorkingDirectory = Join-Path $WorkingDirectory "Packages"
if (-not (Test-Path $PackageWorkingDirectory)) {
    $null = New-Item -Path $PackageWorkingDirectory -ItemType Directory -Force
}
foreach ($Package in (Get-Content $PSScriptRoot\files\chocolatey.json | ConvertFrom-Json).packages) {
    $ChocoArgs = @(
        "download", "$($Package.Name)"
        "--output-directory", $PackageWorkingDirectory
    )
    $ChocoArgs += switch ($Package.Keys) {
        "Version" { "--version", $Package.Version }
        "Args"    { $Package.Args }
    }
    if ($Package.Internalize -or $Package.PSObject.Properties.Name -notcontains "Internalize") {
        $ChocoArgs += "--internalize"  # Default to internalizing
    }
    
    try {
        if (-not (Test-Path "$($PackageWorkingDirectory)\$($Package.Name)*.nupkg") -and -not (Test-Path "$PSScriptRoot\files\$($Package.Name)*.nupkg")) {
            Write-Verbose "Downloading '$($Package.Name)'"
            $Output = choco @ChocoArgs
            if ($LASTEXITCODE -ne 0) {
                $Output
            }
        }
    } catch {
        throw $_
    }
}
Move-Item -Path $PackageWorkingDirectory\*.nupkg -Destination $PSScriptRoot\files\

# Jenkins Plugins
$PluginsWorkingDirectory = Join-Path $WorkingDirectory "JenkinsPlugins"
if (-not (Test-Path $PluginsWorkingDirectory)) {
    $null = New-Item -Path $PluginsWorkingDirectory -ItemType Directory -Force
}
$ProgressPreference = "Ignore"
foreach ($Plugin in (Get-Content $PSScriptRoot\files\jenkins.json | ConvertFrom-Json).plugins) {
    $RestArgs = @{
        Uri     = "https://updates.jenkins-ci.org/latest/$($Plugin.Name).hpi"
        OutFile = Join-Path $PluginsWorkingDirectory "$($Plugin.Name).hpi"
    }
    if ($Plugin.Version -and $Plugin.Version -ne 'latest') {
        $RestArgs.Uri = "https://updates.jenkins-ci.org/download/plugins/$($Plugin.Name)/$($Plugin.Version)/$($Plugin.Name).hpi"
    }
    if (-not (Test-Path $RestArgs.OutFile)) {
        Invoke-WebRequest @RestArgs -UseBasicParsing
    }
}
Compress-Archive -Path $PluginsWorkingDirectory\* -Destination $PSScriptRoot\files\JenkinsPlugins.zip -Force

# License and Certificate
Copy-Item -Path (Convert-Path $LicensePath) -Destination $PSScriptRoot\files\chocolatey.license.xml
Copy-Item -Path (Convert-Path $CertificatePath) -Destination $PSScriptRoot\files\certificate.pfx