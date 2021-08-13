@echo off
cd "%~dp0"
C:\Python34\Scripts\pyinstaller -y --clean "%~dp0acquisition.spec"
"C:\Program Files (x86)\Inno Setup 5\iscc" /Qp "%~dp0acquisition_installer.iss"