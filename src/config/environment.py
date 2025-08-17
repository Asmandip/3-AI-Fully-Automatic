# src/config/environment.py
import os
import sys
import platform

def setup_environment():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path_separator = ";" if platform.system() == "Windows" else ":"
    current_path = os.environ.get("PYTHONPATH", "")
    if project_root not in current_path.split(path_separator):
        os.environ["PYTHONPATH"] = f"{current_path}{path_separator}{project_root}"
    sys.path.insert(0, project_root)

setup_environment()