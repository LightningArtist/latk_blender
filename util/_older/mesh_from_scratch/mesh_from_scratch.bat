@echo off

cd %~dp0
"C:\Program Files\blender\blender" --background --python mesh_from_scratch.py -- %1

@pause