Set WshShell = CreateObject("WScript.Shell")

' Set working directory to the folder containing this VBS script
Dim scriptDir
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
WshShell.CurrentDirectory = scriptDir

' 0 = Hide the window, False = don't wait for exit (detached)
WshShell.Run "cmd /c cd /d """ & scriptDir & """ && START_JACK.bat", 0, False
