REM Short script to build the ExpressionLncr standalone GUI executable.
REM Requires python, pyinstaller, pyside.
REM pip to install pyinstaller is optional, for
REM ex: pip install REM pyinstaller
REM Note that pyinstaller only makes executables
REM for the platform it 
REM is run on. I.e. you need to run it on Windows to
REM build a Windows executable.
REM
REM note that pyinstaller seems bugged. trying py2exe for windows.
REM C:\Python27\Scripts\pyinstaller.exe --onefile --windowed --name ExpressionLncr --icon=expressionlncr.png gui.py
REM C:\Python27_64\Scripts\pyinstaller.exe --onefile --windowed --name ExpressionLncr --icon=expressionlncr.png gui.py
python.exe wininstaller.py py2exe
