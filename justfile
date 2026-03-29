set shell := ["powershell.exe", "-c"]

research:
    uv run jupyter lab --config .jupyter/jupyter_lab_config.py

trace:
    uv run mlflow ui
