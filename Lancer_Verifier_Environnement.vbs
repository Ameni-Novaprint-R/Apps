' Lance la verification de l'environnement eleve dans PowerShell

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -ExecutionPolicy Bypass -File ""c:\Apps\Verifier_Environnement_Eleve.ps1""", 1, False
