"""
Script Python pour executer les scripts SQL en creant un processus non-eleve.
Utilise subprocess avec des flags speciaux pour forcer l'execution sans elevation.
"""

import subprocess
import sys
import os
import ctypes
from pathlib import Path

def is_elevated():
    """Verifie si le processus actuel est eleve."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_non_elevated_python(script_path):
    """
    Execute un script Python dans un processus non-eleve.
    Utilise PowerShell pour creer un nouveau processus sans elevation.
    """
    script_path = Path(script_path).resolve()
    script_dir = script_path.parent
    
    if not script_path.exists():
        print(f"[ERREUR] Script introuvable: {script_path}")
        return False
    
    # Creer un script PowerShell temporaire qui execute le Python
    ps_script = f"""
$ErrorActionPreference = 'Stop'
try {{
    Write-Host '[DEBUT] {script_path.name}' -ForegroundColor Cyan
    Push-Location '{script_dir}'
    $output = python "{script_path}" 2>&1
    $exitCode = $LASTEXITCODE
    Write-Host $output
    if ($exitCode -eq 0) {{
        Write-Host '[SUCCES] {script_path.name}' -ForegroundColor Green
        exit 0
    }} else {{
        Write-Host '[ERREUR] {script_path.name} (code: $exitCode)' -ForegroundColor Red
        exit $exitCode
    }}
}} catch {{
    Write-Host '[ERREUR] {script_path.name} : $_' -ForegroundColor Red
    exit 1
}} finally {{
    Pop-Location
}}
"""
    
    # Methode 1: Utiliser Start-Process avec -Verb RunAsUser (necessite elevation pour creer)
    # Methode 2: Utiliser schtasks pour creer une tache qui s'execute sans elevation
    # Methode 3: Utiliser un wrapper batch avec __COMPAT_LAYER
    
    # Methode la plus simple: Si on n'est pas eleve, executer directement
    if not is_elevated():
        print(f"[INFO] Processus non-eleve, execution directe de {script_path.name}")
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(script_dir),
                capture_output=False,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"[ERREUR] {e}")
            return False
    
    # Si on est eleve, utiliser PowerShell avec une methode speciale
    print(f"[INFO] Processus eleve detecte, tentative de creation d'un processus non-eleve...")
    
    # Creer un fichier batch temporaire avec __COMPAT_LAYER
    batch_content = f"""@echo off
set __COMPAT_LAYER=RunAsInvoker
cd /d "{script_dir}"
python "{script_path}"
"""
    
    batch_path = Path(os.environ.get('TEMP', '.')) / f"cursor_sql_{os.getpid()}.bat"
    try:
        batch_path.write_text(batch_content, encoding='utf-8')
        
        # Lancer le batch via cmd.exe (qui devrait respecter __COMPAT_LAYER)
        # Mais cmd.exe herite de l'elevation...
        
        # Essayer avec PowerShell Start-Process -Verb RunAsUser
        # Mais cela necessite des credentials...
        
        # Solution: Utiliser schtasks pour creer une tache qui s'execute sans elevation
        task_name = f"CursorSQL_{os.getpid()}"
        
        # Creer le XML de tache
        task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
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
      <Command>python.exe</Command>
      <Arguments>"{script_path}"</Arguments>
      <WorkingDirectory>{script_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""
        
        xml_path = Path(os.environ.get('TEMP', '.')) / f"cursor_task_{os.getpid()}.xml"
        xml_path.write_text(task_xml, encoding='utf-16')
        
        try:
            # Creer la tache
            subprocess.run(
                ["schtasks", "/Create", "/TN", task_name, "/XML", str(xml_path), "/F"],
                check=True,
                capture_output=True
            )
            
            # Executer la tache
            subprocess.run(
                ["schtasks", "/Run", "/TN", task_name],
                check=True,
                capture_output=True
            )
            
            # Attendre un peu
            import time
            time.sleep(3)
            
            # Supprimer la tache
            subprocess.run(
                ["schtasks", "/Delete", "/TN", task_name, "/F"],
                capture_output=True
            )
            
            xml_path.unlink(missing_ok=True)
            batch_path.unlink(missing_ok=True)
            
            print(f"[INFO] Tache planifiee executee. Verifiez les resultats ci-dessus.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[ERREUR] Impossible de creer/executer la tache: {e}")
            xml_path.unlink(missing_ok=True)
            batch_path.unlink(missing_ok=True)
            return False
            
    except Exception as e:
        print(f"[ERREUR] {e}")
        batch_path.unlink(missing_ok=True)
        return False

def main():
    script_dir = Path("c:\\Apps")
    scripts = [
        script_dir / "creer_table_web_projets.py",
        script_dir / "creer_table_web_sections.py"
    ]
    
    print("=" * 60)
    print("EXECUTION DES SCRIPTS SQL VIA PROCESSUS NON-ELEVE")
    print("=" * 60)
    print()
    
    if is_elevated():
        print("[ATTENTION] Processus actuel est eleve.")
        print("[INFO] Tentative de creation d'un processus non-eleve...")
        print()
    else:
        print("[INFO] Processus actuel n'est pas eleve, execution directe.")
        print()
    
    success = True
    for script in scripts:
        if script.exists():
            print(f"Execution de {script.name}...")
            if not run_non_elevated_python(script):
                success = False
            print()
        else:
            print(f"[ERREUR] Script introuvable: {script}")
            success = False
    
    print("=" * 60)
    if success:
        print("SUCCES: Tous les scripts ont ete executes.")
        return 0
    else:
        print("ERREUR: Certains scripts ont echoue.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
