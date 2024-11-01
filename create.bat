@echo off

rem Activate the virtual environment
call .\venv_scp\Scripts\activate

rem Check if activation was successful
if errorlevel 1 (
    echo Failed to activate virtual environment. Exiting...
    exit /b
)

rem Build the test_concurrency executable
pyinstaller --onefile --hidden-import=pydicom.encoders.gdcm --hidden-import=pydicom.encoders.pylibjpeg test_concurrency.py

rem Build the app_login executable
pyinstaller --name app_login --onefile app_login.py

echo Build process completed.
pause
