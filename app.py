"""Alternate entry point. Streamlit Community Cloud should use revive_cvst_app.py."""

from pathlib import Path

exec(Path(__file__).with_name("revive_cvst_app.py").read_text(), {"__file__": str(Path(__file__).with_name("revive_cvst_app.py")), "__name__": "__main__"})
