' Lance le diagnostic Cursor dans une fenetre PowerShell visible
' La fenetre reste ouverte pour que vous puissiez lire les resultats.

Set WshShell = CreateObject("WScript.Shell")
' Lancer PowerShell avec le script de diagnostic
' /k = garder la fenetre ouverte apres execution
WshShell.Run "powershell.exe -ExecutionPolicy Bypass -File ""c:\Apps\Diagnostic_Cursor_Admin.ps1""", 1, False
