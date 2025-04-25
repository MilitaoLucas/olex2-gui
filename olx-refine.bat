set bd=%~dp0
set PATH=d:\devel\bin;%PATH%
set PYTHONHOME=%bd%\Python38
set OLEX2_CCTBX_DIR=%bd%\cctbx_dir
set PYL_CMD=%bd%controller.py refine %cd%\%1 %2
rem echo %PYL_CMD%
%bd%pyl %bd%controller.py