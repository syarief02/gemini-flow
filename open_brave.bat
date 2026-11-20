@echo off
rem Starts Brave with remote debugging (port 9222) detached from whatever ran this file, then exits.
rem Add --restart to reopen a Brave that is already open without remote debugging.
python "%~dp0launch_brave.py" --url "https://flow.google.com/?pli=1&authuser=5" %*
