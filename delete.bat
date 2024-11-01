@echo off
rem Remove directories
rmdir /s /q "build"
rmdir /s /q "dist"

rem Delete files
del "test_concurrency.spec"
del "app_login.spec"
del "app_login.exe"
del "test_concurrency.exe"
