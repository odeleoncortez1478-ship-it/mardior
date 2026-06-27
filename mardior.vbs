' MARDIOR Launcher
' Doble click para iniciar — se abre el navegador solo, sin ventana de terminal

Dim shell, fso
Set shell = CreateObject("Wscript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

shell.CurrentDirectory = fso.GetParentFolderName(Wscript.ScriptFullName)

shell.Run "cmd /c python -m mardior", 0, False

Wscript.Sleep 5000

shell.Run "http://localhost:8000"
