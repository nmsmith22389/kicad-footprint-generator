taskkill -im freecad.exe /f
@echo OFF
echo cadquery-freecad-module required
@echo ON
cd %~p0
start "" "c:\FreeCAD\bin\freecad" make_tantalum_export_fc.py CP_Tantalum_Case-A_EIA-3216-18
:: A_3216_18

::pause