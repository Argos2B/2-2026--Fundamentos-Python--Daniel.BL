Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectPath = fso.GetAbsolutePathName(".")
ws.Run "cmd /c """ & projectPath & "\run.bat"""", 0, False
