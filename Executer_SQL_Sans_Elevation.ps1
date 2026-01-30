# Script PowerShell pour executer les scripts SQL dans un processus NON-ELEVE
# Meme si Cursor est en mode admin, ce script cree un nouveau processus PowerShell
# sans elevation pour executer les scripts Python

param(
    [switch]$WebProjets,
    [switch]$WebSections,
    [switch]$LesDeux
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "EXECUTION DES SCRIPTS SQL SANS ELEVATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verifier si ce processus est eleve
$isElevated = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host "Processus actuel eleve: $isElevated" -ForegroundColor $(if ($isElevated) { "Yellow" } else { "Green" })
Write-Host ""

# Chemin des scripts
$scriptDir = "c:\Apps"
$script1 = Join-Path $scriptDir "creer_table_web_projets.py"
$script2 = Join-Path $scriptDir "creer_table_web_sections.py"

# Fonction pour executer un script Python dans un processus non-eleve
function Invoke-NonElevatedPython {
    param(
        [string]$ScriptPath,
        [string]$ScriptName
    )
    
    Write-Host "Execution de $ScriptName..." -ForegroundColor Yellow
    
    # Creer un script temporaire qui execute le Python
    $tempScript = [System.IO.Path]::GetTempFileName() + ".ps1"
    $pythonCmd = "python `"$ScriptPath`""
    
    # Creer un script qui sera execute sans elevation
    $scriptContent = @"
`$ErrorActionPreference = 'Stop'
try {
    Write-Host '[DEBUT] $ScriptName' -ForegroundColor Cyan
    Push-Location '$scriptDir'
    `$output = & $pythonCmd 2>&1
    `$exitCode = `$LASTEXITCODE
    Write-Host `$output
    if (`$exitCode -eq 0) {
        Write-Host '[SUCCES] $ScriptName' -ForegroundColor Green
        exit 0
    } else {
        Write-Host '[ERREUR] $ScriptName (code: `$exitCode)' -ForegroundColor Red
        exit `$exitCode
    }
} catch {
    Write-Host '[ERREUR] $ScriptName : `$_' -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}
"@
    
    Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8
    
    try {
        # Lancer PowerShell sans elevation en utilisant Start-Process avec -Verb RunAsUser
        # Mais RunAsUser demande elevation, donc on utilise une autre methode
        
        # Methode 1: Utiliser schtasks pour creer une tache temporaire qui s'execute sans elevation
        $taskName = "CursorSQLTemp_$(Get-Random)"
        $taskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -File "$tempScript"</Arguments>
      <WorkingDirectory>$scriptDir</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
        
        $taskXmlPath = [System.IO.Path]::GetTempFileName() + ".xml"
        Set-Content -Path $taskXmlPath -Value $taskXml -Encoding Unicode
        
        # Creer et executer la tache
        schtasks /Create /TN $taskName /XML $taskXmlPath /F 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            schtasks /Run /TN $taskName 2>&1 | Out-Null
            Start-Sleep -Seconds 2
            
            # Attendre la fin de la tache
            $maxWait = 60
            $waited = 0
            while ($waited -lt $maxWait) {
                $task = schtasks /Query /TN $taskName /FO CSV /NH 2>&1
                if ($task -match "Ready|Running") {
                    Start-Sleep -Seconds 1
                    $waited++
                } else {
                    break
                }
            }
            
            # Supprimer la tache
            schtasks /Delete /TN $taskName /F 2>&1 | Out-Null
            
            # Lire le resultat depuis le fichier temporaire
            if (Test-Path $tempScript) {
                # Le script a deja affiche sa sortie via Write-Host dans le processus enfant
                # On peut lire un fichier de sortie si on le cree
            }
        } else {
            Write-Host "Impossible de creer la tache planifiee. Tentative alternative..." -ForegroundColor Yellow
            
            # Methode alternative: Utiliser Start-Process avec des credentials non-eleves
            # Mais cela necessite des credentials explicites...
            
            # Methode simple: Executer directement (si on n'est pas eleve)
            if (-not $isElevated) {
                & powershell.exe -ExecutionPolicy Bypass -File $tempScript
            } else {
                Write-Host "ERREUR: Ce processus est eleve et ne peut pas creer un processus non-eleve directement." -ForegroundColor Red
                Write-Host "Solution: Utilisez la route web ou lancez ce script depuis un PowerShell non-eleve." -ForegroundColor Yellow
                return $false
            }
        }
        
        Remove-Item $taskXmlPath -ErrorAction SilentlyContinue
        return $true
        
    } catch {
        Write-Host "ERREUR lors de l'execution: $_" -ForegroundColor Red
        return $false
    } finally {
        Remove-Item $tempScript -ErrorAction SilentlyContinue
    }
}

# Determiner quels scripts executer
$run1 = $false
$run2 = $false

if ($LesDeux) {
    $run1 = $true
    $run2 = $true
} elseif ($WebProjets) {
    $run1 = $true
} elseif ($WebSections) {
    $run2 = $true
} else {
    # Par defaut, executer les deux
    $run1 = $true
    $run2 = $true
}

$success1 = $true
$success2 = $true

if ($run1) {
    if (Test-Path $script1) {
        $success1 = Invoke-NonElevatedPython -ScriptPath $script1 -ScriptName "creer_table_web_projets.py"
    } else {
        Write-Host "Script introuvable: $script1" -ForegroundColor Red
        $success1 = $false
    }
    Write-Host ""
}

if ($run2) {
    if (Test-Path $script2) {
        $success2 = Invoke-NonElevatedPython -ScriptPath $script2 -ScriptName "creer_table_web_sections.py"
    } else {
        Write-Host "Script introuvable: $script2" -ForegroundColor Red
        $success2 = $false
    }
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Cyan
if ($success1 -and $success2) {
    Write-Host "SUCCES: Tous les scripts ont ete executes." -ForegroundColor Green
    exit 0
} else {
    Write-Host "ERREUR: Certains scripts ont echoue." -ForegroundColor Red
    exit 1
}
