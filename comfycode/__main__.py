"""CLI entry point: ``python -m comfycode``

Commands:
    convert — Convert a ComfyUI workflow JSON file to Python code
    export  — Export a Python workflow module to prompt JSON or UI JSON

Usage::

    # Convert JSON to Python
    python -m comfycode convert path/to/workflow.json
    python -m comfycode convert path/to/workflow.json -o output.py

    # Export Python to JSON (requires create_workflow() function)
    python -m comfycode export path/to/workflow.py
    python -m comfycode export path/to/workflow.py -o output.json

    # Export Python to UI JSON (for ComfyUI import with visual layout)
    python -m comfycode export path/to/workflow.py --ui -o workflow_ui.json

    # Backward compatible: bare workflow.json defaults to convert
    python -m comfycode path/to/workflow.json
"""

# Delegate to cli package
from comfycode.cli.main import main

if __name__ == "__main__":
    import sys
    sys.exit(main())
