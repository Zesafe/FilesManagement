import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Updated to target Desktop by default
SORTING_FOLDER = Path(os.getenv("SORTING_FOLDER", Path.home() / "Desktop" / "SortingFolder"))
TARGET_BASE = Path(os.getenv("TARGET_BASE", Path.home() / "Desktop" / "StudySpace"))