"""Launcher for the Streamlit app (avoids interactive prompts)."""
import os
os.environ["ST_SERVER_HEADLESS"] = "true"
os.environ["ST_BROWSER_GATHERUSAGESTATS"] = "false"
os.environ["ST_TELEMETRY_OPT_OUT"] = "1"
os.environ["ST_SERVER_ENABLEWEBASSEMBLY"] = "false"

import streamlit.web.cli as stcli
import sys

sys.argv = [
    "streamlit", "run", "app.py",
    "--server.port", "8504",
    "--server.address", "127.0.0.1",
]
stcli.main()
