"""Default Streamlit Community Cloud entry. The app itself is revive_cvst_app.py."""

from pathlib import Path

target = Path(__file__).with_name("revive_cvst_app.py")
exec(target.read_text(), {"__file__": str(target), "__name__": "__main__"})
