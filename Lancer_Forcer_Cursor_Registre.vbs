' Ouvre une fenêtre de commande visible pour exécuter Forcer_Cursor_Sans_Admin_Registre.bat
' La fenêtre reste ouverte après le script pour que vous puissiez lire les messages.
' À la fin, tapez "exit" ou fermez la fenêtre.

Set WshShell = CreateObject("WScript.Shell")
' /k = garder la fenêtre ouverte après le .bat
' 1 = fenêtre visible, 1 = mode normal
WshShell.Run "cmd /k ""cd /d c:\Apps && Forcer_Cursor_Sans_Admin_Registre.bat""", 1, False
