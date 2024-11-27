@echo off

title Mesh triangulation debug output

chcp 437


call C:\Miniconda3\Scripts\activate.bat scan

python %~dp0gui_triangulate_parallel.py
pause