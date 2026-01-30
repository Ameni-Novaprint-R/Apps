' Lance Cursor SANS droits administrateur (evite l'erreur sandbox dans le terminal).
' Utilise __COMPAT_LAYER=RunAsInvoker pour forcer l'execution sans elevation.
' Utilisation : double-clic sur ce fichier (apres avoir ferme Cursor).

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
LocalAppData = WshShell.ExpandEnvironmentStrings("%LocalAppData%")

' Essayer plusieurs emplacements et noms (Cursor.exe ou Cursor sans .exe)
candidats = Array( _
  "C:\Program Files\cursor\Cursor.exe", _
  "C:\Program Files\cursor\Cursor", _
  LocalAppData & "\Programs\cursor\Cursor.exe", _
  LocalAppData & "\Programs\cursor\Cursor", _
  LocalAppData & "\Programs\Cursor\Cursor.exe", _
  LocalAppData & "\Programs\Cursor\Cursor", _
  LocalAppData & "\cursor\Cursor.exe", _
  LocalAppData & "\cursor\Cursor", _
  "C:\Program Files\Cursor\Cursor.exe", _
  "C:\Program Files\Cursor\Cursor", _
  "C:\Program Files (x86)\Cursor\Cursor.exe", _
  "C:\Program Files (x86)\Cursor\Cursor" _
)

chemin = ""
For Each c In candidats
  If fso.FileExists(c) Then
    chemin = c
    Exit For
  End If
Next

If chemin = "" Then
  liste = "Chemins tries:" & vbCrLf
  For Each c In candidats
    liste = liste & "  - " & c & vbCrLf
  Next
  MsgBox "Cursor introuvable." & vbCrLf & vbCrLf & liste & vbCrLf & "Ouvrez le .vbs avec un editeur et modifiez la variable 'chemin' en debut de script (ligne des candidats).", 48, "Lancer Cursor Sans Admin"
  WScript.Quit 1
End If

' Creer un .bat temporaire
dossierTemp = fso.GetSpecialFolder(2)
fichierBat = dossierTemp & "\LancerCursorSansAdmin_temp.bat"
q = Chr(34)
contenu = "@echo off" & vbCrLf & "set __COMPAT_LAYER=RunAsInvoker" & vbCrLf & "start " & q & q & " " & q & chemin & q
Set ts = fso.CreateTextFile(fichierBat, True)
ts.Write contenu
ts.Close

' Lancer le .bat (fenetre masquee), puis le supprimer
WshShell.Run q & fichierBat & q, 0, False
WScript.Sleep 2000
On Error Resume Next
fso.DeleteFile fichierBat, True

' Message de confirmation
MsgBox "Cursor a ete lance (sans mode administrateur).", 64, "Lancer Cursor Sans Admin"
