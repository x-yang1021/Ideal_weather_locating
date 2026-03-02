"""
Launcher script for packaging with PyInstaller.
Starts the Streamlit server and opens the browser.
"""

import sys
import os


def main():
    # When running as a frozen .exe, we need to set the correct working directory
    # so that Streamlit can find app.py and its imports
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_dir, "app.py")

    # Add base_dir to sys.path so imports work
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit", "run", app_path,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.port", "8501",
    ]
    stcli.main()


if __name__ == "__main__":
    main()
